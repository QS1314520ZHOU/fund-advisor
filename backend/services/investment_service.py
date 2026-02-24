# backend/services/investment_service.py
import pandas as pd
import numpy as np
import logging
from typing import Dict, Any, List, Optional

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

_investment_service = None

def get_investment_service() -> InvestmentService:
    global _investment_service
    if _investment_service is None:
        _investment_service = InvestmentService()
    return _investment_service
