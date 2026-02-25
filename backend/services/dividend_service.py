# backend/services/dividend_service.py
import akshare as ak
import pandas as pd
import logging
from typing import List, Dict, Any, Optional
from datetime import datetime

logger = logging.getLogger(__name__)

class DividendService:
    """基金分红分析服务"""
    
    def __init__(self):
        pass
        
    async def get_fund_dividends(self, code: str) -> Dict[str, Any]:
        """
        获取基金分红历史与分析
        """
        try:
            # 获取全市场分红数据
            # 接口 ak.fund_dividend_em() 返回所有基金近期分红
            # 如果需要特定基金，需要过滤
            df = ak.fund_dividend_em()
            if df.empty:
                return {"success": True, "dividends": [], "summary": {}}
            
            # 过滤特定基金
            # 列名参考: ['序号', '基金代码', '基金简称', '权益登记日', '除息日', '分红发放日', '分红(元/10份)', '再投资已可查询日']
            fund_df = df[df['基金代码'] == code].copy()
            
            if fund_df.empty:
                return {"success": True, "dividends": [], "summary": {"msg": "该基金近期无分红记录"}}
            
            # 处理数值
            fund_df['amount_per_10'] = pd.to_numeric(fund_df['分红(元/10份)'], errors='coerce').fillna(0)
            
            dividends = []
            total_amount_per_unit = 0
            
            for _, row in fund_df.iterrows():
                amount = row['amount_per_10'] / 10.0
                total_amount_per_unit += amount
                dividends.append({
                    "record_date": str(row['权益登记日']),
                    "ex_date": str(row['除息日']),
                    "pay_date": str(row['分红发放日']),
                    "amount_per_unit": round(amount, 4),
                    "description": f"每份分红 {round(amount, 4)} 元"
                })
            
            # 简单汇总
            return {
                "success": True,
                "code": code,
                "dividends": sorted(dividends, key=lambda x: x['record_date'], reverse=True),
                "summary": {
                    "total_dividend_count": len(dividends),
                    "total_amount_per_unit": round(total_amount_per_unit, 4),
                    "last_dividend_date": dividends[0]['pay_date'] if dividends else None
                }
            }
            
        except Exception as e:
            logger.error(f"Failed to fetch dividend data for {code}: {e}")
            return {"success": False, "error": str(e)}

_dividend_service = None

def get_dividend_service() -> DividendService:
    global _dividend_service
    if _dividend_service is None:
        _dividend_service = DividendService()
    return _dividend_service
