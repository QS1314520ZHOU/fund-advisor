# backend/services/action_service.py
import logging
from typing import Dict, Any, List, Optional

try:
    from database import get_db
    from services.calculator import get_calculator
    from services.investment_service import get_investment_service
    from services.data_fetcher import get_data_fetcher
except ImportError:
    from backend.database import get_db
    from backend.services.calculator import get_calculator
    from backend.services.investment_service import get_investment_service
    from backend.services.data_fetcher import get_data_fetcher

logger = logging.getLogger(__name__)

class ActionService:
    """
    每日操作推荐服务
    基于综合评分、回撤和均线偏离度，为主页提供大白话解释的买入/持有/卖出操作建议。
    """
    def __init__(self):
        self.db = get_db()
        self.calculator = get_calculator()
        self.investment = get_investment_service()
        self.fetcher = get_data_fetcher()

    async def get_daily_actions(self, limit: int = 10) -> Dict[str, Any]:
        """
        获取每日操作清单
        根据最新快照评分结合实时/近期偏离度给出具体操作方案。
        """
        snapshot = self.db.get_latest_snapshot()
        if not snapshot:
            return {"status": "no_data", "message": "暂无快照数据"}

        # 获取快照中评分最高的部分基金以及用户自选/持仓
        top_funds = self.db.get_ranking(snapshot_id=snapshot['id'], limit=50)
        
        actions = []
        for fund in top_funds:
            action = self._determine_action(fund)
            if action:
                actions.append(action)
                
            if len(actions) >= limit:
                break
                
        # 分组
        buys = [a for a in actions if a['action'] == 'buy']
        holds = [a for a in actions if a['action'] == 'hold']
        sells = [a for a in actions if a['action'] == 'sell']
        
        return {
            "status": "success",
            "snapshot_date": snapshot['snapshot_date'],
            "summary": f"今日建议重点关注 {len(buys)} 只买入机会，持有 {len(holds)} 只优质资产。",
            "buys": buys[:5],
            "holds": holds[:5],
            "sells": sells[:5]
        }
        
    def _determine_action(self, fund: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """基于指标决定操作动作"""
        score = fund.get('score', 0)
        mdd = fund.get('max_drawdown', 0)
        # 兼容处理 Mdd 为负数
        mdd = abs(mdd) if mdd else 0
        cdd = fund.get('current_drawdown', 0)
        cdd = abs(cdd) if cdd else 0
        
        code = fund['code']
        name = fund.get('name', '未知基金')
        
        # 使用智能定投服务的均线偏离度逻辑辅助判断（如果有历史数据）
        # 这里为了快速响应，使用简单的均线预估或者只依赖已有指标
        # 真实的策略可能会在线获取最新的均线偏离度
        
        action = 'hold'
        reason = '基金表现稳健，建议继续持有观察。'
        level = 'normal'
        
        # 买入逻辑: 评分高 (>80)，且当前回撤较大 (>10%)，或者夏普极高
        if score > 80:
            if cdd > 10:
                action = 'buy'
                reason = f'优质资产当前回调了 {cdd:.1f}%，是逢低布局的好机会。'
                level = 'strong'
            elif score > 85 and mdd < 15:
                action = 'buy'
                reason = '综合实力极强且走势稳健，适合作为底仓买入。'
                level = 'normal'
        
        # 卖出/减仓逻辑: 评分降低 (<50) 或者回撤极大而没有修复迹象
        elif score < 50:
            action = 'sell'
            reason = '各项指标显著下降，继续持有风险较高，建议考虑减仓或转换。'
            level = 'strong'
        elif cdd > 25 and score < 70:
            action = 'sell'
            reason = '下跌趋势明显且基本面指标转弱，建议控制仓位。'
            level = 'normal'
            
        return {
            "code": code,
            "name": name,
            "action": action,
            "reason": reason,
            "level": level,
            "score": score,
            "metrics": {
                "latest_nav": fund.get('latest_nav'),
                "current_drawdown": f"-{cdd:.1f}%",
                "annual_return": f"{fund.get('annual_return', 0):.1f}%"
            }
        }

    async def perform_risk_inspection(self):
        """执行每日风险核查，异常情况发送通知"""
        holdings = self.db.get_holding_portfolio()
        if not holdings:
            return 0
            
        snapshot = self.db.get_latest_snapshot()
        if not snapshot:
            return 0
            
        alert_count = 0
        for pos in holdings:
            code = pos['fund_code']
            metrics = self.db.get_fund_metrics(snapshot['id'], code)
            if not metrics:
                continue
                
            score = metrics.get('score', 0)
            cdd = abs(metrics.get('current_drawdown', 0))
            
            # 风险触发条件
            if cdd > 20:
                self.db.add_notification(
                    type="risk",
                    title="高回撤警报",
                    content=f"持仓中的 {pos['fund_name']} ({code}) 当前回撤已达 {cdd:.1f}%，超过风险红线，建议检视底仓逻辑。",
                    fund_code=code
                )
                alert_count += 1
            elif score < 40:
                self.db.add_notification(
                    type="risk",
                    title="基本面恶化提示",
                    content=f"持仓中的 {pos['fund_name']} ({code}) 最新综合评分已降至 {score:.1f}，进入风险预警区间。",
                    fund_code=code
                )
                alert_count += 1
                
        return alert_count

_action_service = None

def get_action_service() -> ActionService:
    global _action_service
    if _action_service is None:
        _action_service = ActionService()
    return _action_service
