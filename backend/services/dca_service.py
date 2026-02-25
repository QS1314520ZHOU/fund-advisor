
import logging
import datetime
from typing import List, Dict, Any

try:
    from database import get_db
except ImportError:
    from backend.database import get_db

logger = logging.getLogger(__name__)

class DcaService:
    def __init__(self):
        self.db = get_db()

    def check_and_execute_plans(self) -> int:
        """
        检查所有激活的定投计划，如果到了执行日期则进行记录。
        返回执行次数。
        """
        plans = self.db.get_dca_plans()
        now = datetime.datetime.now()
        today_weekday = now.weekday() # 0-6 (Mon-Sun)
        today_day = now.day
        
        executed_count = 0
        for plan in plans:
            if not plan.get('is_active'):
                continue
                
            should_execute = False
            freq = plan.get('frequency', 'weekly')
            
            # 检查频率
            if freq == 'weekly':
                # 注意：数据库存的是 0-6，对应 Mon-Sun
                if plan.get('day_of_week') == today_weekday:
                    should_execute = True
            elif freq == 'monthly':
                if plan.get('day_of_month') == today_day:
                    should_execute = True
            elif freq == 'daily':
                should_execute = True
                
            if should_execute:
                # 检查今天是否已经执行过 (避免重复执行，比如由于重启导致的 job 重跑)
                # 简单逻辑：检查 last_executed_at 是否是今天
                last_exec = plan.get('last_executed_at')
                if last_exec:
                    if last_exec.split(' ')[0] == now.strftime('%Y-%m-%d'):
                        continue # 今天已执行
                
                success = self.execute_plan(plan)
                if success:
                    executed_count += 1
                    
        return executed_count

    def execute_plan(self, plan: Dict[str, Any]) -> bool:
        """执行单个定投计划：记录并发送通知"""
        try:
            plan_id = plan['id']
            fund_code = plan['fund_code']
            fund_name = plan['fund_name']
            amount = plan['base_amount']
            
            # 1. 保存执行记录
            # 在模拟系统中，我们假设以当前参考净值成交
            # 这里可以进一步扩展为获取实时估值
            success = self.db.save_dca_record(plan_id, fund_code, fund_name, amount)
            
            if success:
                # 2. 发送系统通知
                self.db.add_notification(
                    type='dca_exec',
                    title='定投执行成功',
                    content=f'您的定投计划 [{fund_name}] 已成功执行，金额: ¥{amount}',
                    fund_code=fund_code
                )
                logger.info(f"DCA plan {plan_id} executed for {fund_code}")
                return True
        except Exception as e:
            logger.error(f"Error executing DCA plan: {e}")
        return False

_dca_service = None

def get_dca_service() -> DcaService:
    global _dca_service
    if _dca_service is None:
        _dca_service = DcaService()
    return _dca_service
