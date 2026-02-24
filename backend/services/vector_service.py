# backend/services/vector_service.py
import logging
import json
import os
import datetime
from typing import List, Dict, Optional
try:
    # import akshare as ak  <-- Lazy load
    import pandas as pd
except ImportError:
    pass

logger = logging.getLogger(__name__)

class VectorService:
    """
    轻量级向量检索服务 (针对研报和深度分析)
    目前使用关键词匹配 + 时间加权的简化 RAG 方案，
    后续可升级为 FAISS + Sentence-Transformers。
    """
    
    def __init__(self, data_dir: str = "data/knowledge"):
        self.data_dir = data_dir
        if not os.path.exists(data_dir):
            os.makedirs(data_dir)
        self.kb_file = os.path.join(data_dir, "research_reports.json")
        self.knowledge_base = self._load_kb()

    def _load_kb(self) -> List[Dict]:
        if os.path.exists(self.kb_file):
            try:
                with open(self.kb_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except Exception as e:
                logger.error(f"加载知识库失败: {e}")
        return []

    def _save_kb(self):
        try:
            with open(self.kb_file, 'w', encoding='utf-8') as f:
                json.dump(self.knowledge_base, f, ensure_ascii=False, indent=2)
        except Exception as e:
            logger.error(f"保存知识库失败: {e}")

    async def update_knowledge_base(self, keyword: str = "基金市场"):
        """抓取最新的券商研报并存入知识库"""
        try:
            logger.info(f"正在更新研报知识库: {keyword}")
            # 使用 akshare 获取研报 (东方财富个股研报)
            # 这里简化为获取行业/市场研报或大宗新闻的深度部分
            import akshare as ak
            df = ak.stock_report_em()
            
            if df is None or df.empty:
                return 0
            
            new_count = 0
            existing_titles = {item['title'] for item in self.knowledge_base}
            
            for _, row in df.head(50).iterrows():
                title = str(row.get('报告名称', ''))
                if title in existing_titles:
                    continue
                
                item = {
                    'title': title,
                    'summary': str(row.get('摘要', '')),
                    'content': str(row.get('报告内容', '')) or str(row.get('摘要', '')),
                    'date': str(row.get('日期', '')),
                    'source': str(row.get('机构名称', '券商')),
                    'tags': [str(row.get('行业名称', ''))],
                    'type': 'research_report'
                }
                self.knowledge_base.append(item)
                new_count += 1
            
            # 保持知识库大小
            if len(self.knowledge_base) > 500:
                self.knowledge_base = self.knowledge_base[-500:]
                
            self._save_kb()
            logger.info(f"知识库更新完成，新增 {new_count} 条记录")
            return new_count
        except Exception as e:
            logger.error(f"更新知识库失败: {e}")
            return 0

    def query_kb(self, query: str, limit: int = 5) -> List[Dict]:
        """语义/关键词检索知识库"""
        if not self.knowledge_base:
            return []
            
        # 简化版检索：关键词重合度 + 时间衰减
        results = []
        query_words = set(query.lower()) # 这里仅做字符级简化
        
        for item in self.knowledge_base:
            score = 0
            text = (item['title'] + item['summary'] + item['content']).lower()
            
            # 计算包含查询关键词的数量 (此处可用jieba分词优化)
            for word in query:
                if word in text:
                    score += 1
            
            if score > 0:
                results.append((score, item))
        
        # 排序
        results.sort(key=lambda x: x[0], reverse=True)
        return [item for score, item in results[:limit]]

_vector_service: Optional[VectorService] = None

def get_vector_service() -> VectorService:
    global _vector_service
    if _vector_service is None:
        _vector_service = VectorService()
    return _vector_service
