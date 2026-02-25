# backend/services/style_service.py
import pandas as pd
import numpy as np
import logging
from typing import Dict, Any, List, Optional
import akshare as ak

from .data_fetcher import get_data_fetcher

logger = logging.getLogger(__name__)

class StyleService:
    """基金风格分析服务"""
    
    def __init__(self):
        self.fetcher = get_data_fetcher()
        self.indices = {
            'Large-Cap (CSI 300)': '000300',
            'Mid-Cap (CSI 500)': '000905',
            'Small-Cap (CSI 1000)': '000852'
        }
        
    def analyze_style(self, code: str, fund_nav: pd.DataFrame) -> Dict[str, Any]:
        """对基金进行风格诊断"""
        try:
            if fund_nav is None or len(fund_nav) < 120:
                return {"error": "数据不足，无法进行风格分析"}

            # 1. 准备基金收益率
            fund_nav = fund_nav.sort_values('date')
            fund_nav['ret'] = fund_nav['nav'].pct_change()
            fund_nav = fund_nav.dropna()
            
            # 2. 获取基准指数数据 (简化版：使用最近 252 天)
            results = {}
            for name, symbol in self.indices.items():
                try:
                    # 使用统一的 get_benchmark_data 接口
                    idx_df = self.fetcher.get_benchmark_data(symbol=symbol)
                    if idx_df is None or idx_df.empty:
                        continue
                        
                    idx_df['idx_ret'] = idx_df['benchmark_return']
                    
                    # 合并数据
                    merged = pd.merge(fund_nav[['date', 'ret']], idx_df[['date', 'idx_ret']], on='date', how='inner').dropna()
                    
                    if len(merged) < 60:
                        continue
                        
                    # 计算两个阶段的相关性
                    mid = len(merged) // 2
                    corr_recent = merged['ret'].tail(60).corr(merged['idx_ret'].tail(60))
                    corr_prev = merged['ret'].iloc[mid-60:mid].corr(merged['idx_ret'].iloc[mid-60:mid])
                    
                    results[name] = {
                        'recent': round(corr_recent, 4),
                        'previous': round(corr_prev, 4),
                        'diff': round(corr_recent - corr_prev, 4)
                    }
                except Exception as e:
                    logger.warning(f"Failed to fetch index {symbol}: {e}")
            
            if not results:
                return {"error": "无法获取基准数据"}

            # 3. 判定当前主导风格
            main_style = max(results.keys(), key=lambda k: results[k]['recent'])
            max_corr = results[main_style]['recent']
            
            # 4. 判定风格漂移
            prev_main_style = max(results.keys(), key=lambda k: results[k]['previous'])
            is_drift = main_style != prev_main_style
            
            # 5. 判定换手率/主动性 (简化逻辑)
            # 相关性低说明主动管理程度高或换手快 (追踪误差大)
            is_high_turnover = max_corr < 0.7 
            
            return {
                "main_style": main_style,
                "confidence": round(max_corr, 2),
                "style_drift": {
                    "occurred": is_drift,
                    "from": prev_main_style,
                    "to": main_style,
                    "drift_score": round(abs(results[main_style]['diff']), 2) if is_drift else 0
                },
                "active_level": "High" if is_high_turnover else "Moderate",
                "details": results
            }
        except Exception as e:
            logger.error(f"Style analysis failed for {code}: {e}")
            return {"error": str(e)}

_style_service = None

def get_style_service() -> StyleService:
    global _style_service
    if _style_service is None:
        _style_service = StyleService()
    return _style_service
