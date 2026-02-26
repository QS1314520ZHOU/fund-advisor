# backend/services/data_fetcher.py
"""
基金数据获取服务 - 多接口版本
"""

import time
import logging
import re
# import akshare as ak <-- deleted
import pandas as pd
import requests
import datetime
import threading
from typing import Optional, List, Dict, Any
from functools import wraps

logger = logging.getLogger(__name__)


class RateLimiter:
    """请求限速器 - 线程安全版"""
    def __init__(self, min_interval: float = 0.6):
        self.min_interval = min_interval
        self.last_request_time = 0
        self.lock = threading.Lock()
    
    def wait(self):
        with self.lock:
            elapsed = time.time() - self.last_request_time
            if elapsed < self.min_interval:
                time.sleep(self.min_interval - elapsed)
            self.last_request_time = time.time()


def with_retry(max_retries: int = 5, delay: float = 3, backoff: float = 2.0):
    """重试装饰器"""
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            last_error = None
            current_delay = delay
            for attempt in range(max_retries):
                try:
                    return func(*args, **kwargs)
                except Exception as e:
                    last_error = e
                    if attempt < max_retries - 1:
                        logger.warning(f"{func.__name__} 第{attempt+1}次失败: {e}, {current_delay:.1f}秒后重试")
                        time.sleep(current_delay)
                        current_delay *= backoff
            raise last_error
        return wrapper
    return decorator


class DataFetcher:
    """数据获取服务"""
    
    TARGET_FUND_TYPES = {'混合型', '股票型', '股票指数', 'QDII-混合型', 'QDII-股票型'}
    
    EXCLUDE_KEYWORDS = [
        '货币', '债券', 'FOF', '定开', '持有', '封闭',
        '养老', '理财', 'ETF联接', '联接',
        '中短债', '纯债', '增强债', '双债', '添利', '添益',
        '稳健', '安心', '安享', '月月', '季季', '年年'
    ]
    
    THEME_KEYWORDS = {
        # 1. 主流行业板块（核心赛道）
        '大消费': ['消费', '商贸', '零售', '休闲', '餐饮', '乳业'],
        '白酒': ['白酒', '酒'],
        '食品饮料': ['食品', '饮料'],
        '家电': ['家电', '电器'],
        '美妆': ['美妆', '洗护', '化妆品', '个护'],
        '旅游酒店': ['酒店', '旅游'],
        '农业养殖': ['农业', '养殖', '畜牧', '猪'],
        
        '科技TMT': ['科技', '核心科技', '技术', '前沿', 'TMT'],
        '半导体芯片': ['半导体', '芯片', '集成电路'],
        '计算机': ['计算机', '软件', '信创', '云计算', '互联网'],
        '电子': ['电子', '消费电子'],
        '通信': ['通信', '5G', '6G'],
        '传媒游戏': ['传媒', '游戏', '文化', '娱乐'],
        
        '新能源': ['新能源', '碳中和', '绿色', '环保'],
        '光伏': ['光伏', '太阳能'],
        '新能源车': ['新能源车', '电车', '整车', '锂', '锂电', '电池'],
        '风电': ['风电'],
        '储能': ['储能'],
        
        '医药医疗': ['医药', '医疗', '健康', '药', '生命'],
        '创新药': ['创新药', '生物'],
        '医疗器械': ['器械', '医疗器械'],
        '医疗服务': ['医疗服务', 'CXO', '医院', '药店'],
        '中药': ['中药'],
        '生物疫苗': ['疫苗'],
        
        '金融': ['金融', '非银'],
        '银行': ['银行'],
        '券商': ['证券', '券商'],
        '保险': ['保险'],
        '房地产': ['地产', '房地产', '建筑', '不动产'],
        
        '周期': ['周期', '资源', '基础能源', '交通', '基建'],
        '煤炭': ['煤炭'],
        '钢铁': ['钢铁'],
        '有色金属': ['有色', '金属', '黄金', '铜', '铝'],
        '化工': ['化工', '石化', '炼化'],
        
        '高端制造': ['制造', '工业', '智造', '母机', '装备'],
        '航天军工': ['军工', '国防', '航空', '航天'],
        '航空航天': ['航空', '航天', '卫星', '大飞机'],
        '国防军工': ['国防', '军工', '武器'],
        '机器人': ['机器人', '机电', '工业母机'],
        
        # 2. 概念与风格主题
        '红利': ['红利', '高股息', '股息'],
        '人工智能': ['人工智能', 'AI', '大模型', '算力', '智能'],
        'ESG': ['ESG', '社会责任', '治理'],
        '中特估': ['中特估', '央企', '国企', '特估'],
        '出海': ['出海', '跨境', '海外', '纳斯达克', '美股', '全球', '越南', '印度'],
        
        # 3. 基础资产分类
        '权益类': ['股票型', '混合型', '偏股'],
        '固收类': ['债券', '债', '固收', '中短债', '纯债'],
        '商品类': ['黄金ETF', '豆粕ETF', '原油', '大宗商品'],
        'REITs': ['REITs', '不动产信托', '产业园']
    }
    
    def __init__(self):
        self.rate_limiter = RateLimiter(min_interval=0.6)
        self._fund_list_cache = None
        self._fund_list_cache_time = None
        self._benchmark_cache = {}  # {symbol_start_date: df}
        self._cache_ttl = 3600
        self._debug_count = 0
        self.last_valuation_time = 0
        self.valuation_cache = {}
        self.VALUATION_CACHE_SECONDS = 60
    
    @with_retry(max_retries=5, delay=3)
    def get_all_fund_info(self) -> pd.DataFrame:
        """获取所有基金基础信息"""
        self.rate_limiter.wait()
        logger.info("获取全市场基金基础信息...")
        import akshare as ak
        df = ak.fund_name_em()
        logger.info(f"获取到 {len(df)} 只基金的基础信息")
        return df
    
    def filter_candidate_funds(self, progress_callback=None, skip_filter: bool = False) -> List[Dict]:
        """快速筛选候选基金"""
        if self._fund_list_cache and self._fund_list_cache_time and not skip_filter:
            if (datetime.datetime.now() - self._fund_list_cache_time).seconds < self._cache_ttl:
                logger.info(f"使用缓存的基金列表，共 {len(self._fund_list_cache)} 只")
                return self._fund_list_cache
        
        if progress_callback:
            progress_callback("filtering", 0, 1, "正在获取全市场基金列表...")
        
        all_funds_df = self.get_all_fund_info()
        total_count = len(all_funds_df)
        
        if progress_callback:
            progress_callback("filtering", 0, 1, f"全市场共 {total_count} 只基金，正在筛选...")
        
        candidates = []
        # Nightly sync (skip_filter=True) keeps all target types without name filtering
        # Loose match for fund types (e.g. "混合型-偏股" matches "混合型")
        def is_target_type(t):
            t_str = str(t)
            return any(target in t_str for target in self.TARGET_FUND_TYPES)
        
        type_filtered = all_funds_df[all_funds_df['基金类型'].apply(is_target_type)]
        logger.info(f"类型筛选后: {len(type_filtered)} 只 (Loose match)")
        
        for _, row in type_filtered.iterrows():
            code = str(row['基金代码']).zfill(6)
            name = row['基金简称']
            fund_type = row['基金类型']
            
            if not skip_filter:
                # 排除指定的关键字
                if any(kw in name for kw in self.EXCLUDE_KEYWORDS):
                    continue
                
                # 正则判定基金份额 (A/C/B等)
                # 通常我们优先关注 A 类或无后缀类，排除 C, B, D, E, H, R 等
                # 规则：如果简称以 B, C, D, E, H, R 结尾，且前面不是数字（排除像 '300' 这种）
                if re.search(r'(?<!\d)[BCDEHR]$', name):
                    continue
                
                # 排除 ETF 联接基金的 C 类 (重复)
                if '联接C' in name or '联接E' in name:
                    continue
            
            themes = self.identify_themes(name)
            candidates.append({
                'code': code,
                'name': name,
                'fund_type': fund_type,
                'themes': themes
            })
        
        logger.info(f"名称筛选后: {len(candidates)} 只候选基金")
        
        self._fund_list_cache = candidates
        self._fund_list_cache_time = datetime.datetime.now()
        
        if progress_callback:
            progress_callback("filtering", 1, 1, f"筛选完成，共 {len(candidates)} 只候选基金")
        
        return candidates
    
    def identify_themes(self, fund_name: str) -> List[str]:
        """识别基金主题"""
        themes = []
        for theme, keywords in self.THEME_KEYWORDS.items():
            if any(kw in fund_name for kw in keywords):
                themes.append(theme)
        return themes if themes else ['综合']
    
    def get_fund_nav(self, code: str) -> Optional[pd.DataFrame]:
        """获取单只基金的净值数据"""
        self.rate_limiter.wait()
        code = str(code).zfill(6)
        
        try:
            import akshare as ak
            df = ak.fund_open_fund_info_em(
                symbol=code, 
                indicator="单位净值走势",
                period="成立来"
            )
            
            self._debug_count += 1
            if self._debug_count <= 10:
                if df is None:
                    logger.info(f"[调试] 基金 {code}: 返回 None")
                elif len(df) == 0:
                    logger.info(f"[调试] 基金 {code}: 返回空 DataFrame")
                else:
                    logger.info(f"[调试] 基金 {code}: 获取到 {len(df)} 条数据")
            
            if df is not None and len(df) > 0:
                if '净值日期' in df.columns:
                    df = df.rename(columns={
                        '净值日期': 'date',
                        '单位净值': 'nav',
                        '日增长率': 'daily_return'
                    })
                else:
                    if len(df.columns) >= 3:
                        df.columns = ['date', 'nav', 'daily_return']
                    elif len(df.columns) == 2:
                        df.columns = ['date', 'nav']
                        df['daily_return'] = 0
                
                df['date'] = pd.to_datetime(df['date'])
                df['nav'] = pd.to_numeric(df['nav'], errors='coerce')
                
                # Recalculate daily_return from NAV to ensure accuracy and avoid 0s from API
                # pct_change gives 0.01 for 1%, so * 100
                calculated_return = df['nav'].pct_change() * 100
                
                # Use calculated return if available, fallback to column (which might be 0)
                if 'daily_return' in df.columns:
                    # Fill NaNs in column with calculated values
                    df['daily_return'] = pd.to_numeric(df['daily_return'], errors='coerce')
                    df['daily_return'] = df['daily_return'].fillna(calculated_return)
                    
                    # If column is all 0s (common API issue), overwrite with calculated
                    if (df['daily_return'] == 0).all() and not (calculated_return == 0).all():
                         logger.info(f"基金 {code} 原始日增长率全为0，使用计算值覆盖")
                         df['daily_return'] = calculated_return.fillna(0)
                else:
                    df['daily_return'] = calculated_return.fillna(0)
                    
                # Fill remaining NaNs with 0
                df['daily_return'] = df['daily_return'].fillna(0)
                
                # Filter future dates (sanity check)
                df = df[df['date'] <= datetime.datetime.now() + datetime.timedelta(days=1)]
                
                df = df.dropna(subset=['nav'])
                df = df.sort_values('date').reset_index(drop=True)
                return df
                
        except Exception as e:
            self._debug_count += 1
            if self._debug_count <= 10:
                logger.info(f"[调试] 基金 {code} 获取异常: {type(e).__name__}: {e}")
        
        return None
    
    def _get_ex_symbol(self, symbol: str) -> str:
        """根据代码判断交易所前缀"""
        if symbol.startswith(('60', '68', '000', '001', '002', '003', '51', '58')):
            if symbol == '000300': return f"sh{symbol}" # 特例：沪深300在ak里常用sh
            if symbol.startswith(('000', '001', '002', '003')): return f"sz{symbol}" if not symbol.startswith('000300') else f"sh{symbol}"
            return f"sh{symbol}"
        if symbol.startswith(('000', '001', '002', '003', '30', '39')):
            return f"sz{symbol}"
        # 默认返回sh
        return f"sh{symbol}"

    def get_benchmark_data(self, symbol: str = '000300', start_date: str = None) -> Optional[pd.DataFrame]:
        """
        获取基准指数数据 - 多接口轮询
        按稳定性排序尝试多个数据源
        """
        # 兼容性处理：如果是399开头，强制sz
        if symbol.startswith('399'):
            ex_symbol = f"sz{symbol}"
        else:
            ex_symbol = self._get_ex_symbol(symbol)
            
        if start_date is None:
            start_date = (datetime.datetime.now() - datetime.timedelta(days=730)).strftime('%Y%m%d')
        
        # Check cache
        cache_key = f"{symbol}_{start_date}"
        if cache_key in self._benchmark_cache:
            # logger.info(f"使用缓存的基准数据: {symbol}")
            return self._benchmark_cache[cache_key]

        logger.info(f"获取基准数据: {symbol}, 起始日期: {start_date}")
        
        # 接口1: stock_zh_index_daily (最稳定)
        df = self._get_benchmark_via_index_daily(symbol, ex_symbol, start_date)
        if df is not None and len(df) >= 60:
            self._benchmark_cache[cache_key] = df
            return df
        
        # 接口2: index_zh_a_hist
        df = self._get_benchmark_via_hist(symbol, start_date)
        if df is not None and len(df) >= 60:
            self._benchmark_cache[cache_key] = df
            return df
        
        # 接口3: 新浪接口
        df = self._get_benchmark_via_sina(symbol, ex_symbol)
        if df is not None and len(df) >= 60:
            self._benchmark_cache[cache_key] = df
            return df
        
        logger.error(f"所有基准数据接口都失败了 ({symbol})")
        return None
    
    def _get_benchmark_via_index_daily(self, symbol: str, ex_symbol: str, start_date: str) -> Optional[pd.DataFrame]:
        """通过 stock_zh_index_daily 获取基准数据（最稳定）"""
        self.rate_limiter.wait()
        try:
            import akshare as ak
            df = ak.stock_zh_index_daily(symbol=ex_symbol)
            if df is not None and len(df) > 0:
                df = df.reset_index()
                df = df.rename(columns={'date': 'date', 'close': 'close'})
                df['date'] = pd.to_datetime(df['date'])
                start_dt = pd.to_datetime(start_date)
                df = df[df['date'] >= start_dt]
                df['benchmark_return'] = df['close'].pct_change()
                logger.info(f"[stock_zh_index_daily] 基准数据获取成功: {len(df)} 条")
                return df[['date', 'close', 'benchmark_return']]
        except Exception as e:
            logger.debug(f"[stock_zh_index_daily] 失败: {e}")
        return None
    
    def _get_benchmark_via_hist(self, symbol: str, start_date: str) -> Optional[pd.DataFrame]:
        """通过 index_zh_a_hist 获取基准数据"""
        self.rate_limiter.wait()
        try:
            import akshare as ak
            df = ak.index_zh_a_hist(symbol=symbol, period="daily", start_date=start_date)
            if df is not None and len(df) > 0:
                df = df.rename(columns={'日期': 'date', '收盘': 'close'})
                df['date'] = pd.to_datetime(df['date'])
                df['benchmark_return'] = df['close'].pct_change()
                logger.info(f"[index_zh_a_hist] 基准数据获取成功: {len(df)} 条")
                return df[['date', 'close', 'benchmark_return']]
        except Exception as e:
            logger.debug(f"[index_zh_a_hist] 失败: {e}")
        return None
    
    def _get_benchmark_via_sina(self, symbol: str, ex_symbol: str) -> Optional[pd.DataFrame]:
        """通过新浪接口获取基准数据"""
        self.rate_limiter.wait()
        try:
            # 新浪K线数据接口
            url = f"https://quotes.sina.cn/cn/api/jsonp_v2.php/var%20_{symbol}=/KC_MarketDataService.getKLineData"
            params = {
                'symbol': ex_symbol,
                'scale': '240',  # 日线
                'ma': 'no',
                'datalen': '500'
            }
            
            response = requests.get(url, params=params, timeout=10)
            if response.status_code == 200:
                # 解析 JSONP 响应
                text = response.text
                json_str = text[text.find('(') + 1:text.rfind(')')]
                import json
                data = json.loads(json_str)
                
                if data:
                    df = pd.DataFrame(data)
                    df = df.rename(columns={'day': 'date', 'close': 'close'})
                    df['date'] = pd.to_datetime(df['date'])
                    df['close'] = pd.to_numeric(df['close'])
                    df['benchmark_return'] = df['close'].pct_change()
                    logger.info(f"[新浪接口] 基准数据获取成功: {len(df)} 条")
                    return df[['date', 'close', 'benchmark_return']]
        except Exception as e:
            logger.debug(f"[新浪接口] 失败: {e}")
        return None
    
    def get_fund_nav_batch(
        self, 
        codes: List[str], 
        progress_callback=None,
        batch_size: int = 50,
        min_data_days: int = 60,
        concurrent: bool = False,
        max_workers: int = 8
    ) -> Dict[str, pd.DataFrame]:
        """
        批量获取基金净值数据
        
        Args:
            codes: 基金代码列表
            progress_callback: 进度回调函数
            batch_size: 日志打印批次大小
            min_data_days: 最少需要的数据天数
            concurrent: 是否启用并发模式（更快但可能触发限流）
            max_workers: 并发模式下的最大线程数
        """
        results = {}
        total = len(codes)
        insufficient_count = 0
        fail_count = 0
        
        self._debug_count = 0
        
        logger.info(f"开始批量获取 {total} 只基金的净值数据（最少需要 {min_data_days} 天，并发={concurrent}）...")
        
        if concurrent and total > 1:
            # 并发模式
            from concurrent.futures import ThreadPoolExecutor, as_completed
            import threading
            
            processed = [0]  # 使用列表以便在闭包中修改
            lock = threading.Lock()
            
            def fetch_single(code):
                nav_data = self.get_fund_nav(code)
                with lock:
                    processed[0] += 1
                    if progress_callback and processed[0] % 10 == 0:
                        progress_callback(
                            "fetching_nav", 
                            processed[0],
                            total, 
                            f"并发获取中 {processed[0]}/{total}..."
                        )
                return code, nav_data
            
            with ThreadPoolExecutor(max_workers=max_workers) as executor:
                futures = {executor.submit(fetch_single, code): code for code in codes}
                
                for future in as_completed(futures):
                    try:
                        code, nav_data = future.result(timeout=60)
                        if nav_data is not None:
                            data_days = len(nav_data)
                            if data_days >= min_data_days:
                                results[code] = nav_data
                            else:
                                insufficient_count += 1
                        else:
                            fail_count += 1
                    except Exception as e:
                        fail_count += 1
                        logger.warning(f"并发获取基金 {futures[future]} 失败: {e}")
        else:
            # 顺序模式（原逻辑）
            for i, code in enumerate(codes):
                nav_data = self.get_fund_nav(code)
                
                if nav_data is not None:
                    data_days = len(nav_data)
                    if data_days >= min_data_days:
                        results[code] = nav_data
                    else:
                        insufficient_count += 1
                else:
                    fail_count += 1
                
                if progress_callback:
                    progress_callback(
                        "fetching_nav", 
                        i + 1,
                        total, 
                        f"进度 {i+1}/{total} - 成功 {len(results)}，不足 {insufficient_count}，失败 {fail_count}"
                    )
                
                if (i + 1) % batch_size == 0:
                    logger.info(f"进度: {i+1}/{total}，成功 {len(results)}，数据不足 {insufficient_count}，获取失败 {fail_count}")
        
        logger.info(f"批量获取完成: 成功 {len(results)}/{total}，数据不足 {insufficient_count}，获取失败 {fail_count}")
        return results
    
    def get_fund_nav_concurrent(
        self, 
        codes: List[str], 
        max_workers: int = 5,
        timeout: int = 30
    ) -> Dict[str, pd.DataFrame]:
        """
        并发获取多只基金净值数据（简化版，适用于小批量）
        
        Args:
            codes: 基金代码列表
            max_workers: 最大并发数
            timeout: 单个任务超时秒数
        
        Returns:
            {code: DataFrame} 字典
        """
        from concurrent.futures import ThreadPoolExecutor, as_completed
        
        results = {}
        
        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            future_to_code = {executor.submit(self.get_fund_nav, code): code for code in codes}
            
            for future in as_completed(future_to_code):
                code = future_to_code[future]
                try:
                    nav_data = future.result(timeout=timeout)
                    if nav_data is not None:
                        results[code] = nav_data
                except Exception as e:
                    logger.warning(f"并发获取基金 {code} 净值失败: {e}")
        
        return results
    
    def get_realtime_index_quote(self, symbol: str = '000300') -> Optional[Dict]:
        """
        获取指数实时行情（用于今日估算）
        
        Returns:
            {'symbol': '000300', 'name': '沪深300', 'price': 4000.0, 'change_pct': 0.5}
        """
        try:
            # 尝试通过akshare获取实时行情
            import akshare as ak
            df = ak.stock_zh_index_spot_sina()
            if df is not None and len(df) > 0:
                # 查找对应指数
                row = df[df['代码'].str.contains(symbol)]
                if len(row) > 0:
                    row = row.iloc[0]
                    return {
                        'symbol': symbol,
                        'name': row.get('名称', ''),
                        'price': float(row.get('最新价', 0)),
                        'change_pct': float(row.get('涨跌幅', 0))
                    }
        except Exception as e:
            logger.warning(f"获取指数 {symbol} 实时行情失败: {e}")
        
        # 备用方案：新浪实时行情
        try:
            url = f"https://hq.sinajs.cn/list=sh{symbol}"
            headers = {'Referer': 'https://finance.sina.com.cn'}
            response = requests.get(url, headers=headers, timeout=5)
            if response.status_code == 200:
                text = response.text
                # 解析新浪行情格式
                if '="' in text:
                    data = text.split('"')[1].split(',')
                    if len(data) > 8:
                        name = data[0]
                        current = float(data[3])
                        prev_close = float(data[2])
                        change_pct = ((current / prev_close) - 1) * 100 if prev_close > 0 else 0
                        return {
                            'symbol': symbol,
                            'name': name,
                            'price': current,
                            'change_pct': round(change_pct, 2)
                        }
        except Exception as e:
            logger.warning(f"新浪接口获取指数 {symbol} 失败: {e}")
        
        return None
    
    def get_batch_fund_latest_gains(self, codes: List[str], max_workers: int = 10) -> List[Dict]:
        """
        批量获取基金最新日涨幅（用于昨日涨幅榜）
        
        Args:
            codes: 基金代码列表
            max_workers: 最大并发数
            
        Returns:
            List of {'code': str, 'name': str, 'nav': float, 'nav_date': str, 'daily_return': float}
        """
        from concurrent.futures import ThreadPoolExecutor, as_completed
        
        results = []
        
        def fetch_single(code):
            try:
                # 使用akshare获取最新净值
                self.rate_limiter.wait()
                import akshare as ak
                df = ak.fund_open_fund_info_em(
                    symbol=code,
                    indicator="单位净值走势",
                    period="近1月"  # 只获取最近1个月数据更快
                )
                
                if df is not None and len(df) > 0:
                    # 获取最新一条记录
                    if '净值日期' in df.columns:
                        latest = df.iloc[-1]
                        return {
                            'code': code,
                            'nav_date': str(latest['净值日期']),
                            'nav': float(latest['单位净值']),
                            'daily_return': float(latest.get('日增长率', 0)) if pd.notna(latest.get('日增长率')) else 0
                        }
                    else:
                        latest = df.iloc[-1]
                        return {
                            'code': code,
                            'nav_date': str(latest.iloc[0]) if len(latest) > 0 else '',
                            'nav': float(latest.iloc[1]) if len(latest) > 1 else 0,
                            'daily_return': float(latest.iloc[2]) if len(latest) > 2 and pd.notna(latest.iloc[2]) else 0
                        }
            except Exception as e:
                logger.debug(f"获取基金 {code} 最新涨幅失败: {e}")
            return None
        
        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            futures = {executor.submit(fetch_single, code): code for code in codes}
            
            for future in as_completed(futures):
                try:
                    result = future.result(timeout=30)
                    if result:
                        results.append(result)
                except Exception as e:
                    pass
        
        # 按日涨幅排序
        results.sort(key=lambda x: x.get('daily_return', 0), reverse=True)
        return results
    
    # 指数基金跟踪指数映射
    INDEX_FUND_MAPPING = {
        # 沪深300相关
        '沪深300': '000300', '300': '000300', 'HS300': '000300',
        # 中证500相关
        '中证500': '000905', '500': '000905',
        # 创业板相关
        '创业板': '399006', '创业': '399006', 'GEM': '399006',
        # 科创50相关
        '科创50': '000688', '科创': '000688',
        # 上证50相关
        '上证50': '000016', '50': '000016',
        # 中证1000相关
        '中证1000': '000852', '1000': '000852',
        # MSCI相关
        # 纳斯达克
        '纳斯达克': 'NDX', '纳指': 'NDX',
        # 标普500
        '标普': 'SPX', 'S&P': 'SPX',
    }
    
    def get_market_breadth(self) -> Dict[str, Any]:
        """获取全市场涨跌家数概览"""
        try:
            self.rate_limiter.wait()
            # 获取全市场股票实时行情
            import akshare as ak
            df = ak.stock_zh_a_spot_em()
            
            if df is None or len(df) == 0:
                return {'up': 0, 'down': 0, 'flat': 0, 'total': 0}
            
            # 使用涨跌额判断
            up_count = int((df['涨跌额'] > 0).sum())
            down_count = int((df['涨跌额'] < 0).sum())
            flat_count = int((df['涨跌额'] == 0).sum())
            
            return {
                'up': up_count,
                'down': down_count,
                'flat': flat_count,
                'total': len(df),
                'up_pct': round(up_count / len(df) * 100, 1) if len(df) > 0 else 0
            }
        except (requests.exceptions.ProxyError, requests.exceptions.ConnectionError) as e:
            logger.warning(f"获取全市场涨跌家数网络失败 (可能是代理或网络问题): {e}")
            return {'up': 0, 'down': 0, 'flat': 0, 'total': 0}
        except Exception as e:
            logger.error(f"获取全市场涨跌家数失败: {e}")
            return {'up': 0, 'down': 0, 'flat': 0, 'total': 0}

    
    def identify_tracking_index(self, fund_name: str) -> Optional[str]:
        """识别指数基金跟踪的指数代码"""
        for keyword, index_code in self.INDEX_FUND_MAPPING.items():
            if keyword in fund_name:
                return index_code
        return None
    
    def get_market_top_gainers(self, period: str = 'day', fund_type: str = '全部', limit: int = 20) -> List[Dict]:
        """
        获取全市场基金涨幅排行榜（实时联网获取）
        
        Args:
            period: 周期 - 'day'(日涨幅), 'week'(周涨幅), 'month'(月涨幅), '3month', '6month', '1year'
            fund_type: 基金类型 - '全部', '股票型', '混合型', '债券型', '指数型', 'QDII'
            limit: 返回数量
            
        Returns:
            List of {'code': str, 'name': str, 'gain': float, 'nav': float, 'nav_date': str, ...}
        """
        try:
            self.rate_limiter.wait()
            
            # 使用 akshare 获取基金排行数据
            import akshare as ak
            df = ak.fund_open_fund_rank_em(symbol=fund_type)
            
            if df is None or len(df) == 0:
                logger.warning("获取基金排行数据为空")
                return []
            
            # 根据周期选择排序字段
            period_column = {
                'day': '日增长率',
                'week': '近1周',
                'month': '近1月',
                '3month': '近3月',
                '6month': '近6月',
                '1year': '近1年'
            }.get(period, '日增长率')
            
            # 确保列存在
            if period_column not in df.columns:
                # 尝试找到类似的列
                for col in df.columns:
                    if period in col or ('日' in period and '日' in col):
                        period_column = col
                        break
            
            # 转换为数值并排序
            df[period_column] = pd.to_numeric(df[period_column], errors='coerce')
            df = df.dropna(subset=[period_column])
            df = df.sort_values(by=period_column, ascending=False)
            
            results = []
            for _, row in df.head(limit).iterrows():
                try:
                    results.append({
                        'code': str(row.get('基金代码', '')).zfill(6),
                        'name': str(row.get('基金简称', '')),
                        'gain': float(row.get(period_column, 0)),
                        'nav': float(row.get('单位净值', 0)) if pd.notna(row.get('单位净值')) else 0,
                        'nav_date': str(row.get('日期', ''))[:10] if pd.notna(row.get('日期')) else '',
                        'fund_type': str(row.get('基金类型', ''))
                    })
                except Exception as e:
                    continue
            
            logger.info(f"获取全市场涨幅榜成功: {len(results)} 只基金")
            return results
            
        except Exception as e:
            logger.error(f"获取全市场涨幅榜失败: {e}")
            return []
    def get_fund_holdings(self, fund_code: str) -> List[Dict]:
        """获取基金前十大重仓股"""
        try:
            # 兼容处理代码格式
            code = fund_code.strip().zfill(6)
            
            # 使用 akshare 获取选定基金持仓
            # 注意: 该接口返回的是最近一期的季度持仓
            import akshare as ak
            df = ak.fund_portfolio_hold_em(symbol=code)
            
            if df is None or df.empty:
                return []
            
            # 处理列名 (不同版本akshare可能有差异)
            # 典型列名: '股票代码', '股票名称', '占净值比例', '持股数', '持仓市值'
            holdings = []
            # 限制取前10个
            for _, row in df.head(10).iterrows():
                try:
                    holdings.append({
                        'code': str(row.get('股票代码', '')),
                        'name': str(row.get('股票名称', '')),
                        'ratio': float(row.get('占净值比例', 0)) if row.get('占净值比例') else 0,
                        'market_value': float(row.get('持仓市值', 0)) if row.get('持仓市值') else 0
                    })
                except:
                    continue
            return holdings
        except Exception as e:
            logger.error(f"获取基金 {fund_code} 重仓股失败: {e}")
            return []



    def get_fund_manager_info(self, code: str) -> Dict[str, Any]:
        """获取基金经理信息 (真实数据版)"""
        import akshare as ak
        try:
            code = str(code).zfill(6)
            df = ak.fund_manager_em(symbol=code)
            if df is not None and not df.empty:
                # 获取当前任职的经理（通常是第一行或根据“是否在任”筛选）
                # 列名参考: ['基金代码', '基金简称', '现任基金经理', '任职时间', '下任基金经理', '管理规模', '基金公司']
                latest = df.iloc[0]
                return {
                    "name": str(latest.get("现任基金经理", "未知")),
                    "tenure": str(latest.get("任职时间", "未知")),
                    "scale": str(latest.get("管理规模", "未知")),
                    "company": str(latest.get("基金公司", "未知")),
                    "is_real": True
                }
        except Exception as e:
            logger.warning(f"获取基金 {code} 经理信息失败: {e}")
        return {}

    def get_fund_ranks(self, code: str) -> List[Dict[str, Any]]:
        """获取基金同类排名 (真实数据版)"""
        import akshare as ak
        try:
            code = str(code).zfill(6)
            # 使用开考开放式基金排行获取同类排名
            # 这里逻辑较复杂，建议从排行中查找单只
            df = ak.fund_open_fund_rank_em()
            if df is not None and not df.empty:
                fund_row = df[df['基金代码'] == code]
                if not fund_row.empty:
                    row = fund_row.iloc[0]
                    # 构造与前端兼容的排名结构
                    periods = [
                        ("近1周", "近1周"),
                        ("近1月", "近1月"),
                        ("近3月", "近3月"),
                        ("近6月", "近6月"),
                        ("近1年", "近1年")
                    ]
                    ranks = []
                    for label, col in periods:
                        val = row.get(col)
                        if val is not None and str(val) != '---':
                            ranks.append({
                                "period": label,
                                "rank": val, # 排行接口通常直接返回百分比或具体排行
                                "is_real": True
                            })
                    return ranks
        except Exception as e:
            logger.warning(f"获取基金 {code} 排名失败: {e}")
        
        # Fallback to local logic if needed or return empty
        return []

    def get_realtime_valuation(self, code: str) -> Optional[Dict]:
        """获取单只基金实时估值"""
        res = self.get_realtime_valuation_batch([code])
        return res.get(str(code).zfill(6))

    def get_realtime_valuation_batch(self, codes: List[str]) -> Dict[str, Dict]:
        """
        批量获取基金实时估值
        
        Args:
            codes: 基金代码列表
            
        Returns:
            {code: {estimation_nav, estimation_growth, nav, nav_date, time}}
        """
        now = time.time()
        # 缓存检查
        if not self.valuation_cache or (now - self.last_valuation_time > self.VALUATION_CACHE_SECONDS):
            try:
                import akshare as ak
                df = ak.fund_value_estimation_em()
                if df is not None and not df.empty:
                    # Dynamic column mapping
                    # Clean column names
                    cols = [str(c).strip() for c in df.columns.tolist()]
                    df.columns = cols  # Update dataframe columns
                    
                    logger.info(f"Realtime valuation columns: {cols}")
                    
                    code_col = next((c for c in cols if '代码' in c), '基金代码')
                    name_col = next((c for c in cols if '基金' in c and ('名称' in c or '简称' in c)), '基金简称')
                    # Flexible matching for value and growth
                    val_col = next((c for c in cols if '估算' in c and '值' in c), None)
                    growth_col = next((c for c in cols if '估算' in c and ('增长率' in c or '涨幅' in c)), None)
                    nav_col = next((c for c in cols if '单位净值' in c), None)
                    time_col = next((c for c in cols if '时间' in c or '日期' in c), '时间')

                    def safe_float(val):
                        if val is None or val == '---': return 0.0
                        try:
                            return float(str(val).replace('%', ''))
                        except:
                            return 0.0

                    new_cache = {}
                    for _, row in df.iterrows():
                        code = str(row[code_col]).zfill(6)
                        try:
                            # Use '时间' as date if '日期' is missing
                            nav_date = str(row.get('日期', row.get(time_col, '')))[:10]
                            update_time = str(row.get(time_col, ''))
                            
                            new_cache[code] = {
                                'code': code,
                                'name': str(row[name_col]),
                                'estimation_nav': safe_float(row.get(val_col)),
                                'estimation_growth': safe_float(row.get(growth_col)),
                                'nav': safe_float(row.get(nav_col)),
                                'nav_date': nav_date,
                                'time': update_time
                            }
                        except Exception as e:
                            continue
                    self.valuation_cache = new_cache
                    self.last_valuation_time = now
                    logger.info(f"更新实时估值缓存成功: {len(new_cache)} 条")
            except Exception as e:
                logger.error(f"获取实时估值失败: {e}")
        
        results = {}
        for code in codes:
            code = str(code).zfill(6)
            if code in self.valuation_cache:
                results[code] = self.valuation_cache[code]
        return results

    # get_realtime_estimation_chart 已删除 ( fake data)

_data_fetcher: Optional[DataFetcher] = None

def get_data_fetcher() -> DataFetcher:
    global _data_fetcher
    if _data_fetcher is None:
        _data_fetcher = DataFetcher()
    return _data_fetcher


