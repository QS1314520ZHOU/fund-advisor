# backend/services/portfolio_service.py
import logging
from typing import Dict, Any, List, Optional
from datetime import datetime

try:
    from services.data_fetcher import get_data_fetcher
    from database import get_db
except ImportError:
    from backend.services.data_fetcher import get_data_fetcher
    from backend.database import get_db

logger = logging.getLogger(__name__)

class PortfolioService:
    """持仓盈亏分析服务"""
    
    def __init__(self):
        self.fetcher = get_data_fetcher()
        
    async def calculate_portfolio_performance(self, holdings: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        计算持仓组合的实时表现
        
        Args:
            holdings: [{code: str, cost: float, shares: float, name: str}]
            
        Returns:
            汇总数据与明细
        """
        try:
            if not holdings:
                return {"success": True, "total": 0, "items": []}
            
            codes = [h['code'] for h in holdings]
            
            # 1. 获取实时估值
            valuations = self.fetcher.get_realtime_valuation_batch(codes)
            
            results = []
            total_cost = 0
            total_value = 0
            total_day_gain = 0
            
            for holding in holdings:
                code = holding['code'] if 'code' in holding else holding.get('fund_code')
                cost_price = holding.get('cost_price', holding.get('cost', 0))
                shares = holding.get('shares', 0)
                name = holding.get('name', holding.get('fund_name', ''))
                
                investment = cost_price * shares
                total_cost += investment
                
                # 匹配估值数据
                valuation = valuations.get(code, {})
                current_nav = valuation.get('estimation_nav', valuation.get('nav', 0))
                day_growth = valuation.get('estimation_growth', 0)
                
                # 如果估值数据缺失，尝试从基础净值获取最近一天（如果是休市日）
                if current_nav == 0:
                    nav_df = self.fetcher.get_fund_nav(code)
                    if nav_df is not None and not nav_df.empty:
                        current_nav = nav_df['nav'].iloc[-1]
                        day_growth = nav_df['daily_return'].iloc[-1]
                
                # 计算当前市值与盈亏
                current_value = current_nav * shares
                total_value += current_value
                
                unrealized_profit = current_value - investment
                unrealized_roi = (unrealized_profit / investment * 100) if investment > 0 else 0
                
                # 计算今日盈亏
                # 估值计算逻辑：(现估值 - 原净值) * 份额
                # 简化逻辑：当前市值 * (估算涨幅 / (1 + 估算涨幅)) if 估算涨幅是相对于原净值的
                # 但更简单的是：今日盈亏 = 市值 / (1 + 涨幅%) * 涨幅%
                day_gain = (current_value / (1 + day_growth/100)) * (day_growth/100)  if day_growth != 0 else 0
                total_day_gain += day_gain
                
                results.append({
                    "code": code,
                    "name": name or valuation.get('name', ''),
                    "shares": round(shares, 2),
                    "cost_price": round(cost_price, 4),
                    "current_nav": round(current_nav, 4),
                    "investment": round(investment, 2),
                    "current_value": round(current_value, 2),
                    "profit": round(unrealized_profit, 2),
                    "roi": round(unrealized_roi, 2),
                    "day_growth": round(day_growth, 2),
                    "day_gain": round(day_gain, 2),
                    "update_time": valuation.get('time', datetime.now().strftime('%H:%M:%S'))
                })
            
            # 总体汇总
            total_profit = total_value - total_cost
            total_roi = (total_profit / total_cost * 100) if total_cost > 0 else 0
            
            return {
                "success": True,
                "summary": {
                    "total_cost": round(total_cost, 2),
                    "total_value": round(total_value, 2),
                    "total_profit": round(total_profit, 2),
                    "total_roi": round(total_roi, 2),
                    "total_day_gain": round(total_day_gain, 2),
                    "day_growth_avg": round(total_day_gain / total_value * 100, 2) if total_value > 0 else 0
                },
                "items": results,
                "update_time": datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            }
            
        except Exception as e:
            logger.error(f"Portfolio performance calculation failed: {e}")
            return {"success": False, "error": str(e)}

    async def get_portfolio_summary(self, user_id: str = 'default') -> Dict[str, Any]:
        """获取持仓汇总（自动从DB拉取持仓）"""
        try:
            db = get_db()
            holdings = db.get_holding_portfolio(user_id)
            if not holdings:
                return {"success": True, "summary": None, "items": []}
            
            # 统一字段名映射
            formatted_holdings = []
            for h in holdings:
                formatted_holdings.append({
                    "code": h['fund_code'],
                    "name": h['fund_name'],
                    "cost_price": h['cost_price'],
                    "shares": h['shares']
                })
            
            return await self.calculate_portfolio_performance(formatted_holdings)
        except Exception as e:
            logger.error(f"Failed to get portfolio summary: {e}")
            return {"success": False, "error": str(e)}

_portfolio_service = None

def get_portfolio_service() -> PortfolioService:
    global _portfolio_service
    if _portfolio_service is None:
        _portfolio_service = PortfolioService()
    return _portfolio_service
