# backend/utils/pinyin.py
"""
拼音搜索工具 - 支持中文拼音首字母和全拼搜索
"""

# 常用汉字拼音映射表（简化版，覆盖常用基金名称字符）
PINYIN_MAP = {
    # 常见基金名称关键字
    '华': 'hua', '夏': 'xia', '易': 'yi', '方': 'fang', '达': 'da',
    '广': 'guang', '发': 'fa', '招': 'zhao', '商': 'shang', '嘉': 'jia',
    '实': 'shi', '鹏': 'peng', '中': 'zhong', '国': 'guo', '银': 'yin',
    '汇': 'hui', '添': 'tian', '富': 'fu', '天': 'tian', '弘': 'hong',
    '南': 'nan', '工': 'gong', '建': 'jian', '农': 'nong', '交': 'jiao',
    '申': 'shen', '万': 'wan', '博': 'bo', '时': 'shi', '信': 'xin',
    '诚': 'cheng', '泰': 'tai', '康': 'kang', '瑞': 'rui', '安': 'an',
    '平': 'ping', '民': 'min', '生': 'sheng', '兴': 'xing', '全': 'quan',
    '浦': 'pu', '景': 'jing', '顺': 'shun', '长': 'chang', '城': 'cheng',
    '创': 'chuang', '金': 'jin', '鑫': 'xin', '元': 'yuan', '盛': 'sheng',
    '德': 'de', '摩': 'mo', '根': 'gen', '大': 'da', '成': 'cheng',
    
    # 行业主题
    '科': 'ke', '技': 'ji', '消': 'xiao', '费': 'fei', '医': 'yi',
    '药': 'yao', '新': 'xin', '能': 'neng', '源': 'yuan', '金': 'jin',
    '融': 'rong', '制': 'zhi', '造': 'zao', '军': 'jun', '工': 'gong',
    '半': 'ban', '导': 'dao', '体': 'ti', '芯': 'xin', '片': 'pian',
    '人': 'ren', '智': 'zhi', '白': 'bai', '酒': 'jiu', '食': 'shi',
    '品': 'pin', '饮': 'yin', '料': 'liao', '家': 'jia', '电': 'dian',
    '网': 'wang', '络': 'luo', '互': 'hu', '联': 'lian', '计': 'ji',
    '算': 'suan', '机': 'ji', '软': 'ruan', '件': 'jian', '通': 'tong',
    '信': 'xin', '光': 'guang', '伏': 'fu', '锂': 'li', '池': 'chi',
    '电': 'dian', '动': 'dong', '车': 'che', '汽': 'qi', '地': 'di',
    '产': 'chan', '房': 'fang', '证': 'zheng', '券': 'quan', '保': 'bao',
    '险': 'xian', '养': 'yang', '老': 'lao', '健': 'jian', '农': 'nong',
    '业': 'ye', '港': 'gang', '股': 'gu', '债': 'zhai', '券': 'quan',
    
    # 风格类型
    '红': 'hong', '利': 'li', '成': 'cheng', '长': 'zhang', '价': 'jia',
    '值': 'zhi', '增': 'zeng', '强': 'qiang', '稳': 'wen', '健': 'jian',
    '核': 'he', '心': 'xin', '精': 'jing', '选': 'xuan', '优': 'you',
    '质': 'zhi', '蓝': 'lan', '筹': 'chou', '龙': 'long', '头': 'tou',
    '先': 'xian', '进': 'jin', '领': 'ling', '航': 'hang', '主': 'zhu',
    '题': 'ti', '灵': 'ling', '活': 'huo', '配': 'pei', '置': 'zhi',
    '量': 'liang', '化': 'hua', '策': 'ce', '略': 'lue', '对': 'dui',
    '冲': 'chong', '指': 'zhi', '数': 'shu', '增': 'zeng', '强': 'qiang',
    
    # 组合类型
    '混': 'hun', '合': 'he', '型': 'xing', '股': 'gu', '票': 'piao',
    '偏': 'pian', '债': 'zhai', '平': 'ping', '衡': 'heng', '灵': 'ling',
    
    # 数字
    '一': 'yi', '二': 'er', '三': 'san', '四': 'si', '五': 'wu',
    '六': 'liu', '七': 'qi', '八': 'ba', '九': 'jiu', '十': 'shi',
    '百': 'bai', '千': 'qian', '万': 'wan', '亿': 'yi',
    
    # 方位
    '东': 'dong', '西': 'xi', '北': 'bei', '上': 'shang', '下': 'xia',
    '前': 'qian', '后': 'hou', '左': 'zuo', '右': 'you',
    
    # 其他常用
    '和': 'he', '与': 'yu', '的': 'de', '在': 'zai', '有': 'you',
    '品': 'pin', '质': 'zhi', '高': 'gao', '低': 'di', '多': 'duo',
    '少': 'shao', '好': 'hao', '美': 'mei', '善': 'shan', '真': 'zhen',
    '诺': 'nuo', '睿': 'rui', '智': 'zhi', '慧': 'hui', '信': 'xin',
    '达': 'da', '通': 'tong', '明': 'ming', '亮': 'liang', '星': 'xing',
    '月': 'yue', '年': 'nian', '季': 'ji', '恒': 'heng', '永': 'yong',
    '基': 'ji', '础': 'chu', '产': 'chan', '业': 'ye', '链': 'lian',
    '环': 'huan', '保': 'bao', '清': 'qing', '洁': 'jie', '绿': 'lv',
    '色': 'se', '碳': 'tan', '海': 'hai', '外': 'wai', '全': 'quan',
    '球': 'qiu', '亚': 'ya', '洲': 'zhou', '欧': 'ou', '美': 'mei',
    '日': 'ri', '韩': 'han', '印': 'yin', '度': 'du', '越': 'yue',
}


def get_pinyin(char: str) -> str:
    """获取单个汉字的拼音"""
    return PINYIN_MAP.get(char, char.lower())


def get_pinyin_initials(text: str) -> str:
    """获取文本的拼音首字母"""
    result = []
    for char in text:
        if '\u4e00' <= char <= '\u9fff':  # 中文字符
            pinyin = PINYIN_MAP.get(char, '')
            if pinyin:
                result.append(pinyin[0])
        elif char.isalpha():
            result.append(char.lower())
    return ''.join(result)


def get_full_pinyin(text: str) -> str:
    """获取文本的全拼"""
    result = []
    for char in text:
        if '\u4e00' <= char <= '\u9fff':  # 中文字符
            pinyin = PINYIN_MAP.get(char, '')
            if pinyin:
                result.append(pinyin)
        elif char.isalnum():
            result.append(char.lower())
    return ''.join(result)


def pinyin_match(name: str, query: str) -> bool:
    """
    判断名称是否匹配拼音查询
    
    支持：
    - 首字母匹配: hxjj -> 华夏基金
    - 全拼匹配: huaxia -> 华夏
    - 混合匹配: hx -> 华夏, huax -> 华夏
    """
    query = query.lower().strip()
    name = name.strip()
    
    # 空查询
    if not query:
        return False
    
    # 直接中文匹配（如果查询包含中文）
    if any('\u4e00' <= c <= '\u9fff' for c in query):
        return query in name
    
    # 拼音首字母匹配
    initials = get_pinyin_initials(name)
    if query in initials:
        return True
    
    # 全拼匹配
    full_pinyin = get_full_pinyin(name)
    if query in full_pinyin:
        return True
    
    # 首字母开头匹配
    if initials.startswith(query):
        return True
    
    # 全拼开头匹配
    if full_pinyin.startswith(query):
        return True
    
    return False


def rank_pinyin_match(name: str, query: str) -> int:
    """
    对拼音匹配进行排序评分，分数越高越精确
    
    Returns:
        0: 不匹配
        1: 全拼包含
        2: 首字母包含
        3: 全拼开头
        4: 首字母开头
        5: 完全匹配
    """
    query = query.lower().strip()
    name = name.strip()
    
    if not query:
        return 0
    
    # 中文完全包含（最高优先级）
    if any('\u4e00' <= c <= '\u9fff' for c in query):
        if query in name:
            return 10
        return 0
    
    initials = get_pinyin_initials(name)
    full_pinyin = get_full_pinyin(name)
    
    # 完全匹配
    if initials == query or full_pinyin == query:
        return 5
    
    # 首字母开头
    if initials.startswith(query):
        return 4
    
    # 全拼开头
    if full_pinyin.startswith(query):
        return 3
    
    # 首字母包含
    if query in initials:
        return 2
    
    # 全拼包含
    if query in full_pinyin:
        return 1
    
    return 0
