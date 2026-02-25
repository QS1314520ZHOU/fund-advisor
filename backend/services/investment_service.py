# backend/services/investment_service.py
import pandas as pd
import numpy as np
import logging
from typing import Dict, Any, List, Optional

from .data_fetcher import get_data_fetcher

logger = logging.getLogger(__name__)

class InvestmentService:
    """智能投资建议服务"""
    
    def calculate_smart_dca(self, nav_df: pd.DataFrame, base_amount: float = 1000) -> Dict[str, Any]:
        """
        计算基于均线偏离度的智能定投建议
        策略：指数/基金价格低于均线越多，定投金额越大
        """
        try:
            if nav_df is None or len(nav_df) < 250:
                return {"error": "数据不足 250 天，无法计算年线偏离度"}

            df = nav_df.sort_values('date').copy()
            # 计算 250 日移动平均线
            df['ma250'] = df['nav'].rolling(window=250).mean()
            
            latest = df.iloc[-1]
            current_price = latest['nav']
            ma250 = latest['ma250']
            
            if pd.isna(ma250):
                return {"error": "均线计算结果无效"}

            # 偏离度 = (现价 - 均线) / 均线
            deviation = (current_price - ma250) / ma250
            
            # 档位计算 (简化版逻辑)
            # 偏离度 > 15%: 0.6x (超涨，少投)
            # 5% ~ 15%: 0.8x
            # -5% ~ 5%: 1.0x (定投基准)
            # -15% ~ -5%: 1.5x
            # -25% ~ -15%: 2.0x
            # < -25%: 3.0x (超跌，多投)
            
            multiplier = 1.0
            advice = "保持正常定投"
            
            if deviation > 0.15: 
                multiplier = 0.6
                advice = "市场显著超涨，建议减少定投额度，保留现金。"
            elif deviation > 0.05:
                multiplier = 0.8
                advice = "市场温和上涨，建议略微下调定投额度。"
            elif deviation < -0.25:
                multiplier = 3.0
                advice = "市场处于低估极端区间，建议大幅增加定投额度，加速捡便宜筹码。"
            elif deviation < -0.15:
                multiplier = 2.0
                advice = "市场显著低估，建议加倍定投额度。"
            elif deviation < -0.05:
                multiplier = 1.5
                advice = "市场处于低估区间，建议增加定投额度。"
                
            suggested_amount = base_amount * multiplier
            
            return {
                "current_price": round(current_price, 4),
                "ma250": round(ma250, 4),
                "deviation": f"{deviation*100:.2f}%",
                "base_amount": base_amount,
                "multiplier": multiplier,
                "suggested_amount": round(suggested_amount, 2),
                "advice": advice,
                "level": "low" if deviation < -0.15 else ("high" if deviation > 0.15 else "neutral")
            }
        except Exception as e:
            logger.error(f"Calculate smart DCA failed: {e}")
            return {"error": str(e)}

    def simulate_dca(self, nav_df: pd.DataFrame, 
                     base_amount: float = 1000, 
                     frequency: str = 'weekly',
                     start_date: str = None) -> Dict[str, Any]:
        """
        定投模拟器：对比固定定投 vs 智能定投
        
        Args:
            nav_df: 净值数据
            base_amount: 基准定投金额
            frequency: 频率 ('weekly', 'monthly')
            start_date: 开始日期 (默认全部)
        """
        try:
            if nav_df is None or len(nav_df) < 20:
                return {"error": "数据量不足，无法模拟"}
            
            df = nav_df.sort_values('date').copy()
            if start_date:
                df = df[df['date'] >= pd.to_datetime(start_date)]
            
            if len(df) < 10:
                return {"error": "筛选后数据量不足"}
            
            # 计算 MA250 用于智能定投
            df['ma250'] = df['nav'].rolling(window=250, min_periods=20).mean()
            
            # 定义参与定投的日期
            # 简化逻辑：如果是每周，选周一；如果是每月，选1号（或最近的一个交易日）
            if frequency == 'weekly':
                df['is_invest_day'] = df['date'].dt.dayofweek == 0 # 周一
            else:
                df['is_invest_day'] = df['date'].dt.is_month_start # 月初
            
            # 补丁：如果完全没命中（比如周一都是休市），则改用简单的步长
            if df['is_invest_day'].sum() < 2:
                step = 5 if frequency == 'weekly' else 21
                df['is_invest_day'] = False
                df.iloc[::step, df.columns.get_loc('is_invest_day')] = True
            
            # 变量初始化
            # 1. 固定定投
            fixed_total_invested = 0
            fixed_total_shares = 0
            # 2. 智能定投
            smart_total_invested = 0
            smart_total_shares = 0
            
            history = []
            
            for i, row in df.iterrows():
                nav = row['nav']
                is_day = row['is_invest_day']
                
                if is_day:
                    # A. 固定定投
                    fixed_total_invested += base_amount
                    fixed_total_shares += base_amount / nav
                    
                    # B. 智能定投 (计算乘数)
                    deviation = 0
                    if not pd.isna(row['ma250']):
                        deviation = (nav - row['ma250']) / row['ma250']
                    
                    multiplier = 1.0
                    if deviation > 0.15: multiplier = 0.6
                    elif deviation > 0.05: multiplier = 0.8
                    elif deviation < -0.25: multiplier = 3.0
                    elif deviation < -0.15: multiplier = 2.0
                    elif deviation < -0.05: multiplier = 1.5
                    
                    smart_amount = base_amount * multiplier
                    smart_total_invested += smart_amount
                    smart_total_shares += smart_amount / nav
                
                #记录状态（仅记录有定投的日或最后一天，减少前端压力）
                if is_day or i == len(df) - 1:
                    fixed_value = fixed_total_shares * nav
                    smart_value = smart_total_shares * nav
                    
                    history.append({
                        "date": row['date'].strftime('%Y-%m-%d'),
                        "nav": round(nav, 4),
                        "fixed_invested": round(fixed_total_invested, 2),
                        "fixed_value": round(fixed_value, 2),
                        "smart_invested": round(smart_total_invested, 2),
                        "smart_value": round(smart_value, 2)
                    })
            
            # 最终结果
            final_nav = df.iloc[-1]['nav']
            fixed_final_value = fixed_total_shares * final_nav
            smart_final_value = smart_total_shares * final_nav
            
            # 计算收益率
            fixed_roi = (fixed_final_value / fixed_total_invested - 1) * 100 if fixed_total_invested > 0 else 0
            smart_roi = (smart_final_value / smart_total_invested - 1) * 100 if smart_total_invested > 0 else 0
            
            return {
                "summary": {
                    "start_date": df.iloc[0]['date'].strftime('%Y-%m-%d'),
                    "end_date": df.iloc[-1]['date'].strftime('%Y-%m-%d'),
                    "frequency": frequency,
                    "fixed": {
                        "total_invested": round(fixed_total_invested, 2),
                        "final_value": round(fixed_final_value, 2),
                        "profit": round(fixed_final_value - fixed_total_invested, 2),
                        "roi": round(fixed_roi, 2)
                    },
                    "smart": {
                        "total_invested": round(smart_total_invested, 2),
                        "final_value": round(smart_final_value, 2),
                        "profit": round(smart_final_value - smart_total_invested, 2),
                        "roi": round(smart_roi, 2)
                    },
                    "alpha": round(smart_roi - fixed_roi, 2)
                },
                "history": history
            }
        except Exception as e:
            logger.error(f"DCA simulation failed: {e}")
            return {"error": str(e)}

    async def get_smart_dca_suggestion(self, code: str) -> Dict[str, Any]:
        """封装方法：获取基金定投建议（供 API 直接调用）"""
        try:
            fetcher = get_data_fetcher()
            nav_df = fetcher.get_fund_nav(code)
            return self.calculate_smart_dca(nav_df)
        except Exception as e:
            logger.error(f"Failed to get smart dca suggestion for {code}: {e}")
            return {"error": str(e)}

_investment_service = None

def get_investment_service() -> InvestmentService:
    global _investment_service
    if _investment_service is None:
        _investment_service = InvestmentService()
    return _investment_service
