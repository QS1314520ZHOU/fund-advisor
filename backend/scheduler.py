# backend/scheduler.py
"""
定时任务调度器
"""
import logging
import asyncio
from datetime import datetime
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger

from .config import get_settings
from .services.snapshot import get_snapshot_service

logger = logging.getLogger(__name__)

scheduler = AsyncIOScheduler()


def daily_update_job():
    """每日更新任务"""
    logger.info("="*50)
    logger.info("开始每日自动更新任务")
    logger.info("="*50)
    
    service = get_snapshot_service()
    
    # 检查是否正在更新
    if service.is_updating():
        logger.warning("已有更新任务在运行，跳过本次")
        return
    
    # 执行全量更新
    result = service.create_full_snapshot()
    success = result.get('success', False)
    message = result.get('message', '')
    
    if success:
        logger.info(f"每日更新成功: {message}")
    else:
        logger.error(f"每日更新失败: {message}")


async def dca_check_job():
    """每日定投执行核查任务 (建议在收盘后运行)"""
    try:
        from .services.dca_service import get_dca_service
        service = get_dca_service()
        count = await service.check_and_execute_plans()
        if count > 0:
            logger.info(f"DCA check job completed: {count} plans executed.")
    except Exception as e:
        logger.error(f"DCA check job failed: {e}")


async def daily_risk_check_job():
    """每日持仓风险核查任务"""
    try:
        from .services.action_service import get_action_service
        service = get_action_service()
        count = await service.perform_risk_inspection()
        if count > 0:
            logger.info(f"Risk check completed: {count} alerts generated.")
    except Exception as e:
        logger.error(f"Risk check job failed: {e}")


def init_scheduler():
    """初始化调度器"""
    # 使用间隔触发器 (每小时检查一次)
    from apscheduler.triggers.interval import IntervalTrigger
    
    scheduler.add_job(
        nightly_sync_check,
        IntervalTrigger(minutes=60),
        id="nightly_sync_check",
        name="夜间同步检测",
        replace_existing=True
    )
    
    # 添加每日定投核查 (每天 15:30 以后执行)
    scheduler.add_job(
        dca_check_job,
        CronTrigger(hour=15, minute=35),
        id="dca_check_job",
        name="每日定投执行核查",
        replace_existing=True
    )
    
    # 添加每日风险核查 (每天 15:40)
    scheduler.add_job(
        daily_risk_check_job,
        CronTrigger(hour=15, minute=40),
        id="daily_risk_check_job",
        name="每日持仓风险核查",
        replace_existing=True
    )
    
    scheduler.start()
    logger.info("调度器已启动: 每60分钟检测一次自动同步条件，15:35 执行定投核查，15:40 执行风险核查")


async def nightly_sync_check():
    """夜间同步检测逻辑 (异步包装以防阻塞)"""
    now = datetime.now()
    hour = now.hour
    
    # 1. 时间窗口检查 (0:00 - 5:00)
    if not (0 <= hour < 5):
        return

    # 2. 检查今天是否已经有成功的快照
    service = get_snapshot_service()
    today_str = now.strftime('%Y-%m-%d')
    
    # 获取最新成功快照
    last_snapshot = service.db.get_latest_snapshot()
    
    should_run = False
    if not last_snapshot:
        should_run = True
    else:
        # 检查快照日期是否是今天
        last_date = last_snapshot.get('snapshot_date')
        if last_date != today_str:
            should_run = True
            logger.info(f"今日 ({today_str}) 尚未有成功快照 (上次: {last_date})，准备执行同步...")

    if should_run:
        # 3. 执行更新 (使用 to_thread 防止阻塞事件循环)
        logger.info("满足自动更新条件，开始执行全量同步...")
        try:
            result = await asyncio.to_thread(service.create_full_snapshot, skip_filter=True)
            success = result.get('success', False)
            message = result.get('message', '')
            if success:
                logger.info(f"自动更新完成: {message}")
            else:
                logger.error(f"自动更新失败: {message}")
        except Exception as e:
            logger.error(f"自动更新过程中出现异常: {e}")


def shutdown_scheduler():
    """关闭调度器"""
    if scheduler.running:
        scheduler.shutdown()
        logger.info("调度器已关闭")
