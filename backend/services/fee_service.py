# backend/services/fee_service.py
import logging
from typing import List, Dict, Any, Optional
import akshare as ak
import pandas as pd

from .data_fetcher import get_data_fetcher

logger = logging.getLogger(__name__)

class FeeService:
    """基金费率分析服务"""
    
    def __init__(self):
        self.fetcher = get_data_fetcher()
        
    def get_fund_fees(self, code: str) -> Dict[str, Any]:
        """获取单量基金的费率详情"""
        try:
            # 使用 akshare 获取基金基本信息，包含费率
            df = ak.fund_individual_basic_info_xq(symbol=code)
            if df.empty:
                return {}
            
            # 提取费率字段 (注意：AkShare 的字段名可能随版本变化)
            # 我们寻找关键词：管理费、托管费、销售服务费、认购、申购、赎回
            info = {}
            for _, row in df.iterrows():
                item = row['item']
                value = row['value']
                
                if "管理费" in item: info['management_fee'] = value
                elif "托管费" in item: info['custody_fee'] = value
                elif "销售服务费" in item: info['sales_fee'] = value
                elif "最高申购费" in item: info['purchase_fee'] = value
                elif "最高赎回费" in item: info['redemption_fee'] = value
                
            return info
        except Exception as e:
            logger.error(f"Failed to fetch fees for {code}: {e}")
            return {}

    def compare_fees(self, codes: List[str]) -> List[Dict[str, Any]]:
        """对比多只基金的费率"""
        results = []
        for code in codes:
            fee_info = self.get_fund_fees(code)
            if fee_info:
                # 解析百分比字符串为数值
                total_annual = 0
                for k in ['management_fee', 'custody_fee', 'sales_fee']:
                    val_str = fee_info.get(k, "0%")
                    if isinstance(val_str, str) and "%" in val_str:
                        try:
                            val = float(val_str.replace('%', ''))
                            total_annual += val
                        except:
                            pass
                
                fee_info['code'] = code
                fee_info['total_annual_fee'] = f"{total_annual:.2f}%"
                results.append(fee_info)
                
        # 按总费率从低到高排序
        results.sort(key=lambda x: float(x['total_annual_fee'].replace('%', '')))
        return results

_fee_service = None

def get_fee_service() -> FeeService:
    global _fee_service
    if _fee_service is None:
        _fee_service = FeeService()
    return _fee_service
