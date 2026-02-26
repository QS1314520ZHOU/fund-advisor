# backend/services/portfolio_builder.py
import json
import logging
from typing import Dict, Any, List

try:
    from database import get_db
except ImportError:
    from backend.database import get_db

logger = logging.getLogger(__name__)

class PortfolioBuilderService:
    """建仓方案服务：根据金额和风险偏好自动生成投资组合配置"""
    def __init__(self):
        self.db = get_db()
        
    def build_portfolio(self, amount: float, risk_level: str) -> Dict[str, Any]:
        """
        生成推荐组合 
        risk_level: 'conservative' (保守), 'moderate' (稳健), 'aggressive' (积极)
        """
        snapshot = self.db.get_latest_snapshot()
        if not snapshot:
            return {"success": False, "error": "需要最新的快照数据才能生成方案"}
            
        # 1. 定义大类配比
        allocations = {
            'conservative': {
                '固收类': 0.60,
                '货币/短债': 0.20,
                '宽基指数': 0.20
            },
            'moderate': {
                '宽基指数': 0.40,
                '医药医疗/大消费': 0.20, # 行业主题的一个代表，为了更准确这里模糊查询
                '固收类': 0.30,
                '货币/短债': 0.10
            },
            'aggressive': {
                '科技TMT/新能源': 0.40,  # 行业主题
                '宽基指数': 0.30,
                '权益类': 0.20,      # 主动权益
                '固收类': 0.10
            }
        }
        
        target_allocation = allocations.get(risk_level, allocations['moderate'])
        
        # 2. 从库中挑选各分类得分最高的 1 只基金
        portfolio = []
        total_assigned = 0
        
        for category, ratio in target_allocation.items():
            assigned_amount = amount * ratio
            
            # 兼容多种类别名称映射
            themes_cond = category.split('/')
            
            # 使用 SQL 逻辑在当前快照中搜索
            # 为了简化，直接拉取该快照的所有评分，在内存过滤最快的那个
            funds = self.db.get_ranking(snapshot_id=snapshot['id'], limit=500)
            
            selected_fund = None
            for fund in funds:
                themes_str = fund.get('themes', [])
                if isinstance(themes_str, str):
                    try:
                        themes = json.loads(themes_str) if '[' in themes_str else []
                    except:
                        themes = []
                else:
                    themes = themes_str
                    
                # 如果分类包含宽基指数，通常没有具体主题（均衡），或者类型包含指数
                if "指数" in category and ("指数" in fund.get('fund_type', '') or "ETF" in fund.get('name', '')):
                    selected_fund = fund
                    break
                
                # 固收类 / 短债
                if "固收" in category or "短债" in category or "债券" in category:
                    if "债" in fund.get('fund_type', ''):
                        selected_fund = fund
                        break
                        
                # 匹配指定主题
                for t in themes_cond:
                    if any(t in th for th in themes) or t in fund.get('name', ''):
                        selected_fund = fund
                        break
                
                if selected_fund:
                    break
                    
            # Fallback：如果在前500没找到，直接默认取当前排行榜最高且没被选过的
            if not selected_fund:
                 for f in funds:
                     if not any(item['code'] == f['code'] for item in portfolio):
                         selected_fund = f
                         break
            
            if selected_fund:
                portfolio.append({
                    "category": category,
                    "code": selected_fund['code'],
                    "name": selected_fund.get('name', '未知基金'),
                    "ratio": ratio,
                    "amount": round(assigned_amount, 2),
                    "score": selected_fund.get('score', 0)
                })
                total_assigned += assigned_amount
        
        # 处理可能的四舍五入误差导致的未分配完
        if portfolio and total_assigned < amount:
            portfolio[0]['amount'] = round(portfolio[0]['amount'] + (amount - total_assigned), 2)
            
        return {
            "success": True,
            "risk_level": risk_level,
            "total_amount": amount,
            "portfolio": portfolio
        }

_portfolio_builder = None

def get_portfolio_builder() -> PortfolioBuilderService:
    global _portfolio_builder
    if _portfolio_builder is None:
        _portfolio_builder = PortfolioBuilderService()
    return _portfolio_builder
