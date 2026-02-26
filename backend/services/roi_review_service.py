# backend/services/roi_review_service.py
import logging
from typing import Dict, Any, List, Optional
from datetime import datetime

try:
    from database import get_db
    from services.data_fetcher import get_data_fetcher
except ImportError:
    from backend.database import get_db
    from backend.services.data_fetcher import get_data_fetcher

logger = logging.getLogger(__name__)

class ROIReviewService:
    """推荐历史回顾服务"""
    
    def __init__(self):
        self.db = get_db()
        self.fetcher = get_data_fetcher()
        
    async def get_historical_roi(self, limit: int = 15) -> Dict[str, Any]:
        """
        获取历史推荐的收益回顾 - 对接 Phase 7 HistoryView.js
        
        Returns:
            { "date": { "category": [funds] } }
        """
        try:
            # 1. 获取最近成功的快照
            snapshots = self.db.get_successful_snapshots(limit=limit)
            if not snapshots:
                return {"success": True, "data": {}}
            
            # 2. 准备分类映射
            categories = ['top10', 'high_alpha', 'long_term', 'short_term', 'low_beta']
            
            # 3. 结果容器
            result_data = {}
            all_codes = set()
            
            # 预处理：收集所有涉及的基金并按快照组织
            snapshot_funds_map = {}
            for snp in snapshots:
                funds = self.db.get_recommendations(snapshot_id=snp['id'], limit=100)
                snapshot_funds_map[snp['id']] = funds
                for f in funds:
                    all_codes.add(f['code'])
            
            # 批量获取估值补丁 (如果有实时数据更好)
            current_valuations = self.fetcher.get_realtime_valuation_batch(list(all_codes))
            
            for snp in snapshots:
                date_key = snp['snapshot_date']
                day_data = {cat: [] for cat in categories}
                
                funds = snapshot_funds_map.get(snp['id'], [])
                for fund in funds:
                    labels = fund.get('labels', [])
                    
                    # 计算 ROI
                    old_nav = fund.get('latest_nav', 0)
                    code = fund['code']
                    
                    # 获取当前净值 (优先使用数据库历史，再使用实时估值)
                    curr_nav = 0.0
                    try:
                        # 1. 尝试从数据库获取最新记录
                        recent_navs = self.db.get_nav_history(code, limit=1)
                        if recent_navs:
                            curr_nav = float(recent_navs[0].get('nav', 0.0))
                        
                        # 2. 如果数据库没有，从批量估值缓存中拿
                        if curr_nav == 0.0:
                            val = current_valuations.get(code, {})
                            curr_nav = float(val.get('nav', val.get('estimation_nav', 0.0)))
                            
                        # 3. 兜底：如果还是 0，尝试单个实时拉取
                        if curr_nav == 0.0:
                            val = self.fetcher.get_realtime_valuation(code)
                            if val:
                                curr_nav = float(val.get('nav', val.get('estimation_nav', 0.0)))
                    except Exception as e:
                        logger.warning(f"Failed to fetch current NAV for ROI review of {code}: {e}")
                    
                    roi = 0
                    if curr_nav > 0 and old_nav > 0:
                        roi = (curr_nav / old_nav - 1) * 100
                    
                    fund_item = {
                        "fund_code": code,
                        "fund_name": fund.get('name', ''),
                        "return_since_recommend": round(roi, 2),
                        "nav_at_recommend": round(old_nav, 4),
                        "current_nav": round(curr_nav, 4),
                        "score": fund.get('score', 0)
                    }
                    
                    # 分类投递
                    if 'TOP10' in labels: day_data['top10'].append(fund_item)
                    if '高Alpha' in labels: day_data['high_alpha'].append(fund_item)
                    if '长线' in labels: day_data['long_term'].append(fund_item)
                    if '短线' in labels: day_data['short_term'].append(fund_item)
                    if '防守' in labels: day_data['low_beta'].append(fund_item)
                
                # 过滤掉空的分类
                filtered_day_data = {k: v for k, v in day_data.items() if v}
                if filtered_day_data:
                    result_data[date_key] = filtered_day_data
            
            return {
                "success": True,
                "data": result_data
            }
            
        except Exception as e:
            logger.error(f"ROI history review failed: {e}")
            return {"success": False, "error": str(e)}

_roi_service = None

def get_roi_service() -> ROIReviewService:
    global _roi_service
    if _roi_service is None:
        _roi_service = ROIReviewService()
    return _roi_service
