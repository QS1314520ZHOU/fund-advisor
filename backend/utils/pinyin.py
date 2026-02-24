# backend/utils/pinyin.py
"""
拼音搜索工具 - 支持中文拼音首字母和全拼搜索 (使用 pypinyin)
"""

from pypinyin import lazy_pinyin, Style

def get_pinyin_initials(text: str) -> str:
    """获取文本的拼音首字母"""
    #Style.FIRST_LETTER 获取首字母
    initials = lazy_pinyin(text, style=Style.FIRST_LETTER)
    return "".join(initials).lower()

def get_full_pinyin(text: str) -> str:
    """获取文本的全拼"""
    # 默认全拼
    full = lazy_pinyin(text)
    return "".join(full).lower()

def pinyin_match(name: str, query: str) -> bool:
    """
    判断名称是否匹配拼音查询
    """
    query = query.lower().strip()
    name = name.strip()
    
    if not query:
        return False
    
    # 直接中文包含匹配
    if any('\u4e00' <= c <= '\u9fff' for c in query):
        return query in name
    
    # 拼音匹配
    initials = get_pinyin_initials(name)
    full_pinyin = get_full_pinyin(name)
    
    return query in initials or query in full_pinyin

def rank_pinyin_match(name: str, query: str) -> int:
    """
    对拼音匹配进行排序评分
    """
    query = query.lower().strip()
    name = name.strip()
    
    if not query:
        return 0
    
    if any('\u4e00' <= c <= '\u9fff' for c in query):
        return 10 if query in name else 0
    
    initials = get_pinyin_initials(name)
    full_pinyin = get_full_pinyin(name)
    
    if initials == query or full_pinyin == query:
        return 5
    if initials.startswith(query):
        return 4
    if full_pinyin.startswith(query):
        return 3
    if query in initials:
        return 2
    if query in full_pinyin:
        return 1
        
    return 0
