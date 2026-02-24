# backend/services/calendar_service.py
import akshare as ak
import pandas as pd
from datetime import datetime, timedelta
import logging
from typing import List, Dict, Any

logger = logging.getLogger(__name__)

class CalendarService:
    """投资日历服务"""
    
    def get_macro_events(self, date_str: str = None) -> List[Dict[str, Any]]:
        """获取宏观经济事件"""
        if not date_str:
            date_str = datetime.now().strftime('%Y%m%d')
        try:
            # 百度经济日历
            df = ak.news_economic_baidu(date=date_str)
            if df.empty:
                return []
            
            # 转换格式
            events = []
            for _, row in df.iterrows():
                # 根据重要性过滤 (可选)
                events.append({
                    'type': 'macro',
                    'date': row['日期'],
                    'time': row['时间'],
                    'event': row['事件'],
                    'importance': row['重要性'],
                    'previous': str(row.get('前值', '-')),
                    'actual': str(row.get('现值', '-')),
                    'forecast': str(row.get('预测值', '-')),
                    'region': 'Global' # 百度日历通常是全类型的
                })
            return events
        except Exception as e:
            logger.error(f"Failed to fetch macro events: {e}")
            return []

    def get_investment_calendar(self, start_date: str = None, days: int = 7) -> List[Dict[str, Any]]:
        """
        聚合多日事件
        """
        if not start_date:
            start_date_dt = datetime.now()
        else:
            try:
                start_date_dt = datetime.strptime(start_date, '%Y%m%d')
            except:
                start_date_dt = datetime.now()

        all_events = []
        for i in range(days):
            current_date = (start_date_dt + timedelta(days=i)).strftime('%Y%m%d')
            # 1. 宏观
            all_events.extend(self.get_macro_events(current_date))
            
            # 2. 这里可以扩展基金事件 (分红、折算等)
            # 由于 akshare 的分红接口数据量极大且目前无日期筛选，建议只针对自选基金查询或按需延迟加载
        
        # 按时间排序
        all_events.sort(key=lambda x: (x['date'], x['time']))
        return all_events

_calendar_service = None

def get_calendar_service() -> CalendarService:
    global _calendar_service
    if _calendar_service is None:
        _calendar_service = CalendarService()
    return _calendar_service
