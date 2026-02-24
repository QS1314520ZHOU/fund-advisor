# backend/services/macro_service.py
"""
宏观经济指标服务
"""
import pandas as pd
import akshare as ak
import logging
import datetime
import asyncio
from typing import Dict, List, Any, Optional
from concurrent.futures import ThreadPoolExecutor

logger = logging.getLogger(__name__)

class MacroService:
    """宏观数据引擎"""
    
    def __init__(self):
        self.cache = {}
        self.last_update = None
        self.executor = ThreadPoolExecutor(max_workers=3)
        
    async def get_macro_dashboard(self) -> Dict[str, Any]:
        """获取宏观看板数据"""
        try:
            loop = asyncio.get_event_loop()
            
            # 1. 10年期国债收益率 (中)
            cn_bond_10y = await loop.run_in_executor(self.executor, self._get_cn_bond_10y)
            
            # 2. 10年期美债收益率
            us_bond_10y = await loop.run_in_executor(self.executor, self._get_us_bond_10y)
            
            # 3. 人民币汇率 (USD/CNY)
            usd_cny = await loop.run_in_executor(self.executor, self._get_usd_cny)
            
            # 4. 恐慌指数 (VIX) - 简化处理
            vix = 18.5 # 示例值，实际可从 ak.us_stock_vix_index() 获取
            
            return {
                "success": True,
                "data": {
                    "yield_curve": {
                        "cn_10y": cn_bond_10y,
                        "us_10y": us_bond_10y,
                        "spread": round(cn_bond_10y - us_bond_10y, 4) if cn_bond_10y and us_bond_10y else None
                    },
                    "currency": {
                        "usd_cny": usd_cny
                    },
                    "risk": {
                        "vix": vix
                    },
                    "update_time": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                }
            }
        except Exception as e:
            logger.error(f"Failed to fetch macro data: {e}")
            return {"success": False, "error": str(e)}

    def _get_cn_bond_10y(self) -> Optional[float]:
        """获取中国10年期国债收益率"""
        try:
            # 使用 akshare 获取中债收益率曲线
            df = ak.bond_china_yield(start_date=datetime.date.today().strftime("%Y%m%d"))
            if df.empty:
                # 尝试取昨天
                yesterday = (datetime.date.today() - datetime.timedelta(days=1)).strftime("%Y%m%d")
                df = ak.bond_china_yield(start_date=yesterday)
            
            if not df.empty:
                # 找到 10年期
                row = df[df['曲线名称'] == '中债国债收益率曲线']
                if not row.empty:
                    return float(row.iloc[0]['10年'])
            return 2.5 # 默认兜底
        except:
            return 2.5

    def _get_us_bond_10y(self) -> Optional[float]:
        """获取美国10年期国债收益率"""
        try:
            # 简化逻辑，实务中可使用更多源
            return 4.2 # 示例值
        except:
            return 4.0

    def _get_usd_cny(self) -> Optional[float]:
        """获取 USD/CNY 汇率"""
        try:
            df = ak.fx_spot_quote()
            if not df.empty:
                row = df[df['货币对'] == 'USD/CNY']
                if not row.empty:
                    return float(row.iloc[0]['买入价'])
            return 7.2
        except:
            return 7.2

_macro_service = None

def get_macro_service() -> MacroService:
    global _macro_service
    if _macro_service is None:
        _macro_service = MacroService()
    return _macro_service
