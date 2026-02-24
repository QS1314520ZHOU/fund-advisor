# backend/services/money_flow_service.py
import akshare as ak
import pandas as pd
import logging
from typing import List, Dict, Any

logger = logging.getLogger(__name__)

class MoneyFlowService:
    """大额资金流动监测服务"""
    
    def __init__(self):
        pass
        
    def get_big_money_flows(self, top_n: int = 20) -> Dict[str, List[Dict[str, Any]]]:
        """
        获取大额资金流入流出监测结果
        """
        try:
            # 获取基金规模变动数据
            df = ak.fund_scale_change_em()
            if df.empty:
                return {"inflows": [], "outflows": []}
            
            # 转换数据类型
            # 列名参考: ['序号', '基金代码', '基金简称', '基金经理', '期初份额', '期间申购', '期间赎回', '期末份额', '期末净资产']
            # 注意: 数据可能是字符串，需要处理
            cols = df.columns
            df['期间申购'] = pd.to_numeric(df['期间申购'], errors='coerce').fillna(0)
            df['期间赎回'] = pd.to_numeric(df['期间赎回'], errors='coerce').fillna(0)
            df['期初份额'] = pd.to_numeric(df['期初份额'], errors='coerce').fillna(0)
            df['期末净资产'] = pd.to_numeric(df['期末净资产'], errors='coerce').fillna(0)
            
            # 计算净流入 (份额)
            df['net_flow'] = df['期间申购'] - df['期间赎回']
            
            # 过滤掉规模太小的 (例如期末净资产 < 1亿)
            df = df[df['期末净资产'] > 1.0] # 这里的单位可能是亿，根据查看到的数据 0: 375030.57 可能是万元
            # 如果是万元，1亿 = 10000万元
            if df['期末净资产'].max() > 100000: # 如果最大值很大，可能是万元
                 df = df[df['期末净资产'] > 10000] # 过滤掉 1亿 以下的
            
            # 流入排行榜
            inflows = df.sort_values(by='net_flow', ascending=False).head(top_n)
            # 流出排行榜
            outflows = df.sort_values(by='net_flow', ascending=True).head(top_n)
            
            def format_results(subset):
                res = []
                for _, row in subset.iterrows():
                    res.append({
                        "code": row['基金代码'],
                        "name": row['基金简称'],
                        "manager": row['基金经理'],
                        "net_flow": round(row['net_flow'], 2),
                        "subscription": round(row['期间申购'], 2),
                        "redemption": round(row['期间赎回'], 2),
                        "total_asset": round(row['期末净资产'], 2)
                    })
                return res
            
            return {
                "inflows": format_results(inflows),
                "outflows": format_results(outflows)
            }
            
        except Exception as e:
            logger.error(f"Failed to fetch money flow data: {e}")
            return {"inflows": [], "outflows": [], "error": str(e)}

_money_flow_service = None

def get_money_flow_service() -> MoneyFlowService:
    global _money_flow_service
    if _money_flow_service is None:
        _money_flow_service = MoneyFlowService()
    return _money_flow_service
