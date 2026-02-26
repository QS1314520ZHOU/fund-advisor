# backend/services/action_service.py
import logging
import datetime
from datetime import datetime, timedelta
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
        snapshots = self.db.get_successful_snapshots(limit=2)
        if not snapshots:
            return {"status": "no_data", "message": "暂无快照数据"}
        
        snapshot = snapshots[0]
        prev_snapshot = snapshots[1] if len(snapshots) > 1 else None
        
        # 获取上次推荐过的基金（去重最近7天）
        recent_actions = []
        for i in range(7):
            date_str = (datetime.now() - timedelta(days=i)).strftime('%Y-%m-%d')
            recent_actions.extend([a['fund_code'] for a in self.db.get_daily_actions(date_str)])
        recent_recommended = set(recent_actions)

        # 获取上一个快照的前50名（用于判断“新进入”）
        prev_top_50 = set()
        if prev_snapshot:
            prev_top_50 = {f['code'] for f in self.db.get_ranking(snapshot_id=prev_snapshot['id'], limit=50)}

        # 获取当前市场 TOP 50
        top_funds = self.db.get_ranking(snapshot_id=snapshot['id'], limit=50)
        
        # 额外拉取用户持仓基金，确保覆盖
        holdings = self.db.get_holding_portfolio()
        holding_codes = {h['fund_code'] for h in holdings}
        
        # 合并扫描列表 (TOP 50 + 持仓)
        scan_list = top_funds[:]
        top_codes = {f['code'] for f in top_funds}
        
        for h_code in holding_codes:
            if h_code not in top_codes:
                # 获取该持仓基金的最新指标
                m = self.db.get_fund_metrics(snapshot['id'], h_code)
                if m:
                    scan_list.append(m)
        
        actions = []
        for fund in scan_list:
            # 基础过滤：如果是买入建议，检查是否最近7天已推荐
            action_data = self._determine_action(fund, prev_top_50)
            if not action_data:
                continue
            
            # 去重：如果最近7天已作为 "buy" 推荐过，跳过（或者改为 hold）
            if action_data['action'] == 'buy' and action_data['code'] in recent_recommended:
                action_data['action'] = 'hold'
                action_data['reason'] = '优质资产，建议继续持有。'
            
            actions.append(action_data)
                
            if len([a for a in actions if a['action'] == 'buy']) >= limit:
                # 限制买入推荐数量，但不限制持有建议
                pass
                
        # 分组并持久化
        buys = [a for a in actions if a['action'] == 'buy']
        holds = [a for a in actions if a['action'] == 'hold']
        sells = [a for a in actions if a['action'] == 'sell']
        
        # 排序：评分高优先
        buys.sort(key=lambda x: x['score'], reverse=True)
        
        # 保存到数据库（可选，但推荐，这样前端刷新不消失且能去重）
        all_to_save = (buys[:5] + holds[:5] + sells[:5])
        self.db.save_daily_actions(snapshot['snapshot_date'], all_to_save)
        
        return {
            "status": "success",
            "snapshot_date": snapshot['snapshot_date'],
            "summary": f"今日建议重点关注 {len(buys[:5])} 只买入机会，持有 {len(holds[:5])} 只优质资产。",
            "buys": buys[:5],
            "holds": holds[:5],
            "sells": sells[:5]
        }
        
    def _determine_action(self, fund: Dict[str, Any], prev_top_50: Optional[set] = None) -> Optional[Dict[str, Any]]:
        """基于指标决定操作动作"""
        score = fund.get('score', 0)
        # cdd 来自快照中的记录 (上一交易日相对于高点的振幅)
        cdd = abs(fund.get('current_drawdown', 0))
        # return_1w (本周增长)
        ret_1w = fund.get('return_1w', 0)
        
        code = fund['code']
        name = fund.get('name', '未知基金')
        
        action = 'hold'
        reason = '基金表现稳健，建议继续持有观察。'
        level = 'normal'
        
        # 约束1：新进入 TOP 50
        is_new_top = prev_top_50 is not None and code not in prev_top_50
        # 约束2：本周显著回调 (>5%) 但评分仍极高
        is_dip_buy = ret_1w < -5 and score > 80
        
        # 优化后的买入逻辑
        if score > 80:
            if is_new_top:
                action = 'buy'
                reason = '新晋评分 TOP 50，综合动能正在走强，建议关注。'
                level = 'normal'
            elif is_dip_buy:
                action = 'buy'
                reason = f'本周深度回调 {abs(ret_1w):.1f}%，虽有波动但基本面依然极佳，适合博弈。'
                level = 'strong'
            elif score > 88: # 长期大白马
                # 增加了安全阀：如果本周涨幅过快 (>10%) 或当前处于高位 (回撤 < 1%)，则不给出强烈买入建议，避免高位站岗
                if ret_1w > 10 or cdd < 1:
                    action = 'hold'
                    reason = '评分极高，但近期涨幅过大，建议等待小坑回调再入场。'
                else:
                    action = 'buy'
                    reason = '评分极其卓越的长跑冠军，任何回调都是定投好时点。'
                    level = 'strong'
                
        # 卖出/减仓逻辑: 评分降低 (<45) 或者短期回撤太大且分数滑坡
        elif score < 45:
            action = 'sell'
            reason = '评分已降至及格线以下，趋势转弱，建议先离场观望。'
            level = 'strong'
        elif cdd > 20 and score < 70:
            action = 'sell'
            reason = '近期最大回撤过快，且综合评价同步下滑，建议减仓规避风险。'
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
