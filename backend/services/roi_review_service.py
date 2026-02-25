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
        
    async def get_historical_roi(self, limit: int = 10) -> Dict[str, Any]:
        """
        获取历史推荐的收益回顾
        
        Args:
            limit: 回顾最近多少个快照
            
        Returns:
            快照回顾列表
        """
        try:
            # 1. 获取最近成功的快照
            snapshots = self.db.get_successful_snapshots(limit=limit)
            if not snapshots:
                return {"success": True, "history": []}
            
            # 2. 获取当前全市场最新净值（用于计算收益）
            # 获取所有涉及到的基金代码
            all_codes = set()
            snapshot_data = []
            
            for snp in snapshots:
                # 每个快照取前 10 名
                top_funds = self.db.get_recommendations(snapshot_id=snp['id'], limit=10)
                snp['top10'] = top_funds
                for f in top_funds:
                    all_codes.add(f['code'])
                snapshot_data.append(snp)
            
            # 批量获取实时估值
            current_valuations = self.fetcher.get_realtime_valuation_batch(list(all_codes))
            
            history = []
            for snp in snapshot_data:
                valid_items = []
                total_roi = 0
                count = 0
                
                for fund in snp['top10']:
                    code = fund['code']
                    old_nav = fund['latest_nav']
                    
                    # 获取最新确认净值 (来自 nav_history)
                    curr_nav = 0
                    db = get_db()
                    recent_navs = db.get_nav_history(code, limit=1)
                    if recent_navs:
                        curr_nav = recent_navs[0].get('nav', 0)
                    
                    # 补丁：如果 confirmed nav 缺失，回退到今日估值
                    if curr_nav == 0:
                        val = current_valuations.get(code, {})
                        curr_nav = val.get('nav', val.get('estimation_nav', 0))
                    
                    if curr_nav > 0 and old_nav > 0:
                        roi = (curr_nav / old_nav - 1) * 100
                        total_roi += roi
                        count += 1
                        
                        valid_items.append({
                            "code": code,
                            "name": fund.get('name', ''),
                            "old_nav": round(old_nav, 4),
                            "current_nav": round(curr_nav, 4),
                            "roi": round(roi, 2),
                            "score_then": fund.get('score', 0)
                        })
                
                if count > 0:
                    history.append({
                        "snapshot_id": snp['id'],
                        "date": snp['snapshot_date'],
                        "avg_roi": round(total_roi / count, 2),
                        "count": count,
                        "top_performers": sorted(valid_items, key=lambda x: -x['roi'])[:3],
                        "details": valid_items
                    })
            
            return {
                "success": True,
                "history": history,
                "overall_avg_roi": round(sum(h['avg_roi'] for h in history) / len(history), 2) if history else 0
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
