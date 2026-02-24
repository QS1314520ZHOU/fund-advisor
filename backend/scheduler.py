# backend/scheduler.py
"""
定时任务调度器
"""
import logging
from datetime import datetime
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger

from .config import get_settings
from .services.snapshot import get_snapshot_service

logger = logging.getLogger(__name__)

scheduler = BackgroundScheduler()


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
    success, message, snapshot_id = service.create_full_snapshot()
    
    if success:
        logger.info(f"每日更新成功: {message}")
    else:
        logger.error(f"每日更新失败: {message}")


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
    
    scheduler.start()
    logger.info("调度器已启动: 每60分钟检测一次自动同步条件")


def nightly_sync_check():
    """夜间同步检测逻辑"""
    now = datetime.now()
    hour = now.hour
    
    # 1. 时间窗口检查 (0:00 - 5:00)
    if not (0 <= hour < 5):
        # logger.debug(f"当前时间 {now.strftime('%H:%M')} 不在更新窗口 (0-5点)，跳过")
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
        else:
            # 今天已经有快照了
            pass

    if should_run:
        # 3. 执行更新
        logger.info("满足自动更新条件，开始执行全量同步...")
        # 0-5点期间执行无过滤同步
        success, message, _ = service.create_full_snapshot(skip_filter=True)
        if success:
            logger.info(f"自动更新完成: {message}")
        else:
            logger.error(f"自动更新失败: {message}")


def shutdown_scheduler():
    """关闭调度器"""
    if scheduler.running:
        scheduler.shutdown()
        logger.info("调度器已关闭")
