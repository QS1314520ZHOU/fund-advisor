
import logging
import asyncio
import httpx
from typing import List, Dict, Any
from datetime import datetime
import pandas as pd

# Logger setup
logger = logging.getLogger(__name__)

# Essential Imports
try:
    import akshare as ak
except ImportError:
    ak = None
    logger.error("akshare is not installed. Some news sources will be unavailable.")

try:
    import yfinance as yf
except ImportError:
    yf = None

class FreeNewsCollector:
    """免费全球财经新闻聚合器 (零API Key)"""
    
    async def fetch_all(self, limit: int = 100) -> List[Dict]:
        """并发获取所有免费源的新闻"""
        tasks = [
             self.fetch_cls_telegraph(), # 财联社
             self.fetch_baidu_finance(), # 百度财经
             self.fetch_eastmoney_market(), # 东方财富
             self.fetch_yahoo_market(),   # Yahoo Finance (Global)
             self.fetch_us_news(), # 美股新闻
             self.fetch_hk_news(), # 港股新闻
             self.fetch_global_indices_news() # 全球指数
        ]
        
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        all_news = []
        for res in results:
            if isinstance(res, list):
                all_news.extend(res)
            elif isinstance(res, Exception):
                logger.debug(f"新闻源获取异常: {res}")
                
        # 去重 (Title based)
        seen = set()
        unique_news = []
        for n in all_news:
            if n['title'] and n['title'] not in seen:
                seen.add(n['title'])
                unique_news.append(n)
        
        # Sort by date desc
        unique_news.sort(key=lambda x: str(x.get('date', '')) + str(x.get('time', '')), reverse=True)
        
        return unique_news[:limit]

    async def fetch_cls_telegraph(self) -> List[Dict]:
        """财联社电报 (akshare: stock_info_global_cls)"""
        if not ak: return []
        try:
            # User suggested stock_info_global_cls
            df = await asyncio.to_thread(ak.stock_info_global_cls, symbol="全部")
            news_list = []
            if not df.empty:
                for _, row in df.head(50).iterrows():
                    news_list.append({
                        "title": str(row.get('标题', row.get('内容', ''))),
                        "content": str(row.get('内容', '')),
                        "source": "财联社",
                        "date": str(row.get('日期', datetime.now().strftime('%Y-%m-%d'))),
                        "time": str(row.get('时间', '')),
                        "url": "#",
                        "sentiment": "neutral",
                        "tags": ["A-Share", "Fast"]
                    })
            return news_list
        except Exception as e:
            logger.warning(f"财联社获取失败 (stock_info_global_cls): {e}")
            # Try backup method name if exists
            try:
                df = await asyncio.to_thread(ak.stock_telegraph_cls)
                news_list = []
                if not df.empty:
                    for _, row in df.head(15).iterrows():
                        news_list.append({
                            "title": str(row.get('标题', '')),
                            "content": str(row.get('内容', '')),
                            "source": "财联社",
                            "date": str(row.get('日期', '')),
                            "time": str(row.get('时间', '')),
                            "sentiment": "neutral",
                            "tags": ["A-Share", "Fast"]
                        })
                return news_list
            except:
                return []

    async def fetch_baidu_finance(self) -> List[Dict]:
        """百度财经 (akshare: news_economic_baidu)"""
        if not ak: return []
        try:
            df = await asyncio.to_thread(ak.news_economic_baidu)
            news_list = []
            if not df.empty:
                for _, row in df.head(30).iterrows():
                    news_list.append({
                        "title": str(row.get('标题', '')),
                        "content": str(row.get('内容', '')), # Assuming content column exists or is inferred
                        "source": "百度财经",
                        "date": str(row.get('日期', datetime.now().strftime('%Y-%m-%d'))),
                        "time": str(row.get('时间', '')),
                        "url": "#",
                        "sentiment": "neutral",
                        "tags": ["China", "Macro"]
                    })
            return news_list
        except Exception as e:
            if "ProxyError" in str(e):
                logger.warning("获取财经新闻失败: 检测到代理连接异常。建议检查系统代理或环境变量。")
            else:
                logger.warning(f"百度财经获取失败: {e}")
            return []

    async def fetch_eastmoney_market(self) -> List[Dict]:
        """东方财富 (akshare: stock_news_em) - market proxy via 000001"""
        if not ak: return []
        try:
            df = await asyncio.to_thread(ak.stock_news_em, symbol="sh000001")
            news_list = []
            if not df.empty:
                for _, row in df.head(20).iterrows():
                    news_list.append({
                        "title": str(row.get('新闻标题', '')),
                        "content": str(row.get('新闻内容', '')),
                        "source": "东方财富",
                        "date": str(row.get('发布时间', '')),
                        "url": str(row.get('文章链接', '')),
                        "sentiment": "neutral",
                        "tags": ["Market"]
                    })
            return news_list
        except Exception as e:
            if "ProxyError" in str(e):
                logger.warning("获取东方财富新闻失败: 网络被代理拦截。")
            else:
                logger.warning(f"东方财富获取失败: {e}")
            return []

    async def fetch_yahoo_market(self) -> List[Dict]:
        """Yahoo Finance - Global Markets (No Key)"""
        if not yf:
            return []
            
        try:
            # Major Global Indices & Tech
            tickers = ["^GSPC", "^IXIC", "000300.SS", "AAPL", "NVDA"] 
            
            news_list = []
            
            def get_yf_news_batch(syms):
                batch_news = []
                for s in syms:
                    try:
                        t = yf.Ticker(s)
                        if t.news:
                            batch_news.extend(t.news[:3]) # Take top 3 per ticker
                    except:
                        continue
                return batch_news
            
            raw_news = await asyncio.to_thread(get_yf_news_batch, tickers)
            
            for item in raw_news:
                ts = item.get('providerPublishTime', 0)
                pub_date = datetime.fromtimestamp(ts).strftime('%Y-%m-%d %H:%M')
                news_list.append({
                    "title": item.get('title'),
                    "content": f"Global Market. {item.get('type', '')}",
                    "source": f"Yahoo ({item.get('publisher', 'Finance')})",
                    "date": pub_date,
                    "url": item.get('link'),
                    "sentiment": "neutral",
                    "tags": ["Global", "US"]
                })
            
            return news_list
        except Exception as e:
            logger.warning(f"Yahoo Finance failed: {e}")
            return []

    async def fetch_us_news(self) -> List[Dict]:
        """美股新闻 (yf.Ticker("AAPL").news)"""
        if not yf: return []
        try:
            tickers = ["AAPL", "NVDA", "MSFT", "TSLA", "GOOGL"] 
            
            def get_us_news_sync():
                batch = []
                for t in tickers:
                    try:
                        tk = yf.Ticker(t)
                        if tk.news:
                            batch.extend(tk.news[:2])
                    except: pass
                return batch

            raw_news = await asyncio.to_thread(get_us_news_sync)
            
            news_list = []
            for item in raw_news:
                ts = item.get('providerPublishTime', 0)
                pub_date = datetime.fromtimestamp(ts).strftime('%Y-%m-%d %H:%M')
                news_list.append({
                    "title": item.get('title'),
                    "content": f"US Stock News. {item.get('type', '')}",
                    "source": f"Yahoo ({item.get('publisher', 'US')})",
                    "date": pub_date,
                    "url": item.get('link'),
                    "sentiment": "neutral",
                    "tags": ["US", "Stock"]
                })
            return news_list
        except Exception as e:
            logger.warning(f"美股新闻获取失败: {e}")
            return []

    async def fetch_hk_news(self) -> List[Dict]:
        """港股新闻 (yf.Ticker("0700.HK").news)"""
        if not yf: return []
        try:
            tickers = ["0700.HK", "9988.HK", "3690.HK", "1810.HK"]
            
            def get_hk_news_sync():
                batch = []
                for t in tickers:
                    try:
                        tk = yf.Ticker(t)
                        if tk.news:
                            batch.extend(tk.news[:2])
                    except: pass
                return batch

            raw_news = await asyncio.to_thread(get_hk_news_sync)
            
            news_list = []
            for item in raw_news:
                ts = item.get('providerPublishTime', 0)
                pub_date = datetime.fromtimestamp(ts).strftime('%Y-%m-%d %H:%M')
                news_list.append({
                    "title": item.get('title'),
                    "content": f"HK Stock News. {item.get('type', '')}",
                    "source": f"Yahoo ({item.get('publisher', 'HK')})",
                    "date": pub_date,
                    "url": item.get('link'),
                    "sentiment": "neutral",
                    "tags": ["HK", "Stock"]
                })
            return news_list
        except Exception as e:
            logger.warning(f"港股新闻获取失败: {e}")
            return []

    async def fetch_global_indices_news(self) -> List[Dict]:
        """全球指数 (ak.index_global_spot_em())"""
        if not ak: return []
        try:
            # ak.index_global_spot_em() returns a DF with columns like "名称", "最新价", "涨跌幅", etc.
            df = await asyncio.to_thread(ak.index_global_spot_em)
            if df is None or df.empty: return []

            key_indices = ["道琼斯", "标普500", "纳斯达克", "恒生指数", "英国富时100", "法国CAC40", "德国DAX", "日经225"]
            summary_parts = []
            
            for _, row in df.iterrows():
                name = str(row.get('名称', ''))
                if any(k in name for k in key_indices):
                    rate = row.get('涨跌幅', 0)
                    price = row.get('最新价', 0)
                    summary_parts.append(f"{name} {price}({rate}%)")
            
            if summary_parts:
                content = " | ".join(summary_parts[:5]) # Take top 5 to avoid too long
                return [{
                    "title": f"全球市场实时行情速递 ({datetime.now().strftime('%H:%M')})",
                    "content": content,
                    "source": "AKShare Global",
                    "date": datetime.now().strftime('%Y-%m-%d %H:%M'),
                    "url": "#",
                    "sentiment": "neutral",
                    "tags": ["Global", "Index"]
                }]
            return []
        except Exception as e:
            logger.warning(f"全球指数获取失败: {e}")
            return []


class NewsService:
    def __init__(self):
        self._cache = {
             "market": {"data": [], "updated_at": None},
             "breadth": {"data": None, "updated_at": None},
             "fund": {}
        }
        self._cache_ttl = 300 # 5 minutes
        self._breadth_ttl = 600 # 10 minutes
        self.collector = FreeNewsCollector()

    async def get_market_news(self, limit: int = 20) -> List[Dict[str, Any]]:
        """Unified Market News Access"""
        now = datetime.now()
        
        # Check Cache
        if self._cache["market"]["updated_at"]:
            elapsed = (now - self._cache["market"]["updated_at"]).seconds
            if elapsed < self._cache_ttl and self._cache["market"]["data"]:
                return self._cache["market"]["data"][:limit]

        # Fetch Fresh
        news = await self.collector.fetch_all(limit=limit * 2)
        
        # Update Cache
        self._cache["market"] = {
            "data": news,
            "updated_at": now
        }
        
        return news[:limit]

    async def get_market_breadth(self) -> Dict[str, Any]:
        """获取 A 股全市场涨跌分布 (Breadth)"""
        now = datetime.now()
        if self._cache["breadth"]["updated_at"]:
            elapsed = (now - self._cache["breadth"]["updated_at"]).seconds
            if elapsed < self._breadth_ttl and self._cache["breadth"]["data"]:
                return self._cache["breadth"]["data"]

        if not ak: return {"up": 0, "down": 0, "flat": 0, "total": 0}
        
        try:
            # 获取全 A 实时数据进行统计
            df = await asyncio.to_thread(ak.stock_zh_a_spot_em)
            if df is None or df.empty:
                return {"up": 0, "down": 0, "flat": 0, "total": 0}
            
            changes = df['涨跌幅'].dropna()
            up = int((changes > 0).sum())
            down = int((changes < 0).sum())
            flat = int((changes == 0).sum())
            total = len(df)
            
            data = {
                "up": up,
                "down": down,
                "flat": flat,
                "total": total,
                "up_ratio": round(up / total * 100, 1) if total > 0 else 0,
                "updated_at": now.strftime('%H:%M:%S')
            }
            
            self._cache["breadth"] = {
                "data": data,
                "updated_at": now
            }
            return data
        except Exception as e:
            logger.warning(f"获取市场宽度失败: {e}")
            return {"up": 0, "down": 0, "flat": 0, "total": 0}

    async def analyze_market_sentiment(self) -> Dict[str, Any]:
        """使用统一计算器进行市场情绪分析"""
        news = await self.get_market_news(limit=50)
        breadth = await self.get_market_breadth()
        
        from .calculator import get_calculator
        calc = get_calculator()
        
        return calc.analyze_market_sentiment(news, breadth)

    async def get_fund_news(self, code: str) -> List[Dict]:
        """Get Fund Specific News"""
        if not ak: return []
        try:
            # Use ak.stock_news_em for specific code (Works for stocks, less reliable for funds but worth a try)
            df = await asyncio.to_thread(ak.stock_news_em, symbol=code)
            if df is None or df.empty:
                return []
            
            news = []
            for _, row in df.head(10).iterrows():
                news.append({
                    "title": str(row.get('新闻标题', '')),
                    "source": str(row.get('新闻来源', 'EastMoney')),
                    "date": str(row.get('发布时间', '')),
                    "url": str(row.get('文章链接', '')),
                    "type": "个股资讯"
                })
            return news
        except Exception as e:
            if "ProxyError" in str(e):
                 logger.warning(f"获取基金 {code} 新闻受代理干扰。")
            return []

_news_service_instance = None

def get_news_service():
    global _news_service_instance
    if _news_service_instance is None:
        _news_service_instance = NewsService()
    return _news_service_instance
