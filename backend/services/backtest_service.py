# backend/services/backtest_service.py
"""
投资组合回测服务
"""
import pandas as pd
import numpy as np
import logging
from typing import List, Dict, Any, Optional
from datetime import datetime

from .data_fetcher import get_data_fetcher
from .calculator import get_calculator
from ..database import get_db

logger = logging.getLogger(__name__)

class BacktestService:
    """投资组合回测引擎"""
    
    def __init__(self):
        self.fetcher = get_data_fetcher()
        self.calculator = get_calculator()
        self.db = get_db()
        
    async def run_backtest(self, portfolio: List[Dict[str, Any]], 
                          start_date: Optional[str] = None,
                          end_date: Optional[str] = None) -> Dict[str, Any]:
        """
        运行投资组合回测
        
        Args:
            portfolio: [{'code': '000001', 'weight': 50}, ...]
            start_date: 开始日期 (YYYY-MM-DD)
            end_date: 结束日期 (YYYY-MM-DD)
            
        Returns:
            回测结果字典
        """
        try:
            if not portfolio:
                return {"success": False, "error": "组合列表不能为空"}
            
            # 1. 提取代码并标准化权重 (权重之和应为 100)
            codes = [p['code'] for p in portfolio]
            weights = {p['code']: p['weight'] / 100.0 for p in portfolio}
            
            # 2. 并发获取所有基金净值
            fund_data_map = self.fetcher.get_fund_nav_concurrent(codes)
            
            if not fund_data_map:
                return {"success": False, "error": "未能获取到任何基金数据"}
            
            # 3. 数据对齐与组合净值计算
            combined_df = None
            
            for code, df in fund_data_map.items():
                if df is None or df.empty:
                    logger.warning(f"基金 {code} 无数据，跳过")
                    continue
                
                # 预处理：计算日收益率
                df = df.sort_values('date')
                df['ret'] = df['nav'].pct_change()
                df = df[['date', 'ret']].dropna()
                
                weight = weights.get(code, 0)
                df['weighted_ret'] = df['ret'] * weight
                
                if combined_df is None:
                    combined_df = df[['date', 'weighted_ret']].rename(columns={'weighted_ret': 'total_ret'})
                else:
                    combined_df = pd.merge(combined_df, 
                                         df[['date', 'weighted_ret']], 
                                         on='date', how='inner')
                    combined_df['total_ret'] = combined_df['total_ret'] + combined_df['weighted_ret']
                    combined_df = combined_df[['date', 'total_ret']]
            
            if combined_df is None or combined_df.empty:
                return {"success": False, "error": "组合数据对齐后为空，可能由于基金成立时间差异过大"}
            
            # 根据日期筛选
            if start_date:
                combined_df = combined_df[combined_df['date'] >= pd.to_datetime(start_date)]
            if end_date:
                combined_df = combined_df[combined_df['date'] <= pd.to_datetime(end_date)]
                
            if combined_df.empty:
                return {"success": False, "error": "所选日期范围内无重合数据"}
                
            # 4. 从收益率重建组合净值 (从 1.0 开始)
            combined_df = combined_df.sort_values('date')
            combined_df['nav'] = (1 + combined_df['total_ret']).cumprod()
            
            # 5. 计算量化指标
            # 获取基准数据进行对比
            benchmark_data = self.fetcher.get_benchmark_data() 
            
            stats = self.calculator.calculate_metrics(combined_df, benchmark_df=benchmark_data)
            
            if not stats:
                return {"success": False, "error": "指标计算失败"}
                
            # 6. 格式化图表数据
            chart_data = combined_df.tail(252).copy()
            chart_data['date'] = chart_data['date'].dt.strftime('%Y-%m-%d')
            
            return {
                "success": True,
                "metrics": {
                    "total_return": stats.get('annual_return'),
                    "max_drawdown": stats.get('max_drawdown'),
                    "sharpe": stats.get('sharpe'),
                    "volatility": stats.get('volatility'),
                    "alpha": stats.get('alpha'),
                    "beta": stats.get('beta')
                },
                "chart": chart_data[['date', 'nav']].to_dict(orient='records'),
                "details": {
                    "fund_count": len(fund_data_map),
                    "start_date": combined_df['date'].iloc[0].strftime('%Y-%m-%d'),
                    "end_date": combined_df['date'].iloc[-1].strftime('%Y-%m-%d'),
                    "days": len(combined_df)
                }
            }
            
        except Exception as e:
            logger.error(f"Backtest failed: {e}")
            import traceback
            logger.error(traceback.format_exc())
            return {"success": False, "error": str(e)}

_backtest_service = None

def get_backtest_service() -> BacktestService:
    global _backtest_service
    if _backtest_service is None:
        _backtest_service = BacktestService()
    return _backtest_service
