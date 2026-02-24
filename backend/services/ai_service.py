# backend/services/ai_service.py
"""
AI 服务模块 - 支持模型管理与降级
"""

import logging
import httpx
import json
import hashlib
from datetime import datetime, timedelta
from typing import Optional, List, Dict, Any

try:
    from ..config import get_settings
    # from .vector_service import get_vector_service
    from ..utils.cache import get_cache_manager
except (ImportError, ValueError):
    # Fallback for direct script execution or different import paths
    from config import get_settings
    # from services.vector_service import get_vector_service
    from utils.cache import get_cache_manager
from ..database import get_db

logger = logging.getLogger(__name__)


class AIService:
    """AI 服务类"""
    
    # 推荐模型优先级（根据用户强制要求的 DeepSeek-V3 系列）
    RECOMMENDED_MODELS = [
        'DeepSeek-V3',
        'DeepSeek-V3-0324',
        'deepseek-v3-1-250821',
        'deepseek-v3-1-terminus',
        'deepseek-v3-2-251201',
        'deepseek-v3.2-speciale',
        'gpt-oss-120b'
    ]
    
    def __init__(self):
        self.settings = get_settings()
        self.db = get_db()
        
        self.api_key = self.settings.AI_API_KEY
        self.base_url = self.settings.AI_BASE_URL.rstrip('/')
        # 自动纠正：如果用户提供的 URL 包含了 /chat/completions，我们需要去掉它，
        # 因为后续代码会自动拼接这个后缀，或者在获取模型列表时需要拼接 /models
        if self.base_url.endswith('/chat/completions'):
            self.base_url = self.base_url.replace('/chat/completions', '').rstrip('/')
            
        self.current_model = self.settings.AI_MODEL
        self.fallback_models = self.settings.AI_FALLBACK_MODELS
        self.timeout = self.settings.AI_TIMEOUT
        
        # 缓存
        self._available_models: List[str] = []
        self._models_cache_time: Optional[datetime] = None
        self._models_cache_ttl = 3600  # 1小时
        
        logger.info(f"AI服务初始化: model={self.current_model}, base_url={self.base_url}")
    
    async def fetch_available_models(self, force_refresh: bool = False) -> List[str]:
        """获取可用模型列表"""
        # 检查缓存
        if not force_refresh and self._available_models and self._models_cache_time:
            if (datetime.now() - self._models_cache_time).seconds < self._models_cache_ttl:
                return self._available_models
        
        try:
            async with httpx.AsyncClient(timeout=30) as client:
                response = await client.get(
                    f"{self.base_url}/models",
                    headers={"Authorization": f"Bearer {self.api_key}"}
                )
                
                if response.status_code == 200:
                    data = response.json()
                    models = []
                    
                    # 解析模型列表
                    if isinstance(data, dict) and 'data' in data:
                        for item in data['data']:
                            if isinstance(item, dict) and 'id' in item:
                                models.append(item['id'])
                            elif isinstance(item, str):
                                models.append(item)
                    elif isinstance(data, list):
                        for item in data:
                            if isinstance(item, dict) and 'id' in item:
                                models.append(item['id'])
                            elif isinstance(item, str):
                                models.append(item)
                    
                    self._available_models = sorted(models)
                    self._models_cache_time = datetime.now()
                    logger.info(f"获取到 {len(models)} 个可用模型")
                    return self._available_models
                else:
                    # 如果返回 404，说明该提供商可能不支持通用模型查询接口，这在很多中转 API 中很常见
                    if response.status_code == 404:
                        logger.debug(f"模型列表接口不可用 (404): {self.base_url}/models")
                    else:
                        logger.warning(f"获取模型列表失败: {response.status_code}")
                    
        except Exception as e:
            logger.error(f"获取模型列表异常: {e}")
        
        return self._available_models or []

    # generate_deep_analysis 已删除
    
    def get_recommended_models(self) -> List[str]:
        """获取推荐模型列表（按优先级排序）"""
        if not self._available_models:
            return self.RECOMMENDED_MODELS
        
        # 返回可用且推荐的模型
        recommended = []
        for model in self.RECOMMENDED_MODELS:
            if model in self._available_models:
                recommended.append(model)
        
        return recommended if recommended else self._available_models[:10]
    
    def get_model_info(self) -> Dict[str, Any]:
        """获取模型信息"""
        return {
            'current_model': self.current_model,
            'fallback_models': self.fallback_models,
            'available_count': len(self._available_models),
            'available_models': self._available_models[:50],
            'recommended_models': self.get_recommended_models(),
            'api_configured': bool(self.api_key),
            'base_url': self.base_url
        }
    
    def _get_models_to_try(self) -> List[str]:
        """获取要尝试的模型列表（智能选择：优先可用且推荐的模型）"""
        models = []
        
        # 如果有可用模型列表，使用它来过滤
        if self._available_models:
            # 1. 先加入主模型（如果可用）
            if self.current_model in self._available_models:
                models.append(self.current_model)
            
            # 2. 加入推荐模型中可用的（按优先级）
            for m in self.RECOMMENDED_MODELS:
                if m in self._available_models and m not in models:
                    models.append(m)
            
            # 3. 加入fallback模型中可用的
            for m in self.fallback_models:
                if m in self._available_models and m not in models:
                    models.append(m)
            
            # 4. 如果上述都没有，从可用模型中选择前10个
            if not models:
                models = self._available_models[:10]
        else:
            # 没有可用模型列表时，使用默认顺序
            models = [self.current_model]
            for m in self.fallback_models:
                if m not in models:
                    models.append(m)
            # 添加推荐模型作为额外备选
            for m in self.RECOMMENDED_MODELS:
                if m not in models:
                    models.append(m)
        
        logger.debug(f"将尝试的模型列表: {models[:5]}...")
        return models
    
    async def _call_ai(
        self, 
        system_prompt: str, 
        user_prompt: str, 
        max_tokens: int = 2000,
        timeout: int = None
    ) -> Optional[str]:
        """调用 AI API（支持智能模型降级）"""
        # 使用自定义超时或默认超时
        request_timeout = timeout if timeout is not None else self.timeout
        # 先尝试获取可用模型列表
        if not self._available_models:
            await self.fetch_available_models()
        
        models_to_try = self._get_models_to_try()
        errors = []
        
        for model in models_to_try:
            try:
                async with httpx.AsyncClient(timeout=request_timeout) as client:
                    response = await client.post(
                        f"{self.base_url}/chat/completions",
                        headers={
                            "Authorization": f"Bearer {self.api_key}",
                            "Content-Type": "application/json"
                        },
                        json={
                            "model": model,
                            "messages": [
                                {"role": "system", "content": system_prompt},
                                {"role": "user", "content": user_prompt}
                            ],
                            "max_tokens": max_tokens,
                            "temperature": 0.3
                        }
                    )
                    
                    if response.status_code == 200:
                        data = response.json()
                        content = data['choices'][0]['message']['content']
                        logger.info(f"AI 调用成功: model={model}")
                        self.current_model = model # 更新为主选模型
                        return content
                    else:
                        error_msg = response.json().get('error', {}).get('message', '未知错误')
                        errors.append(f"{model}: {error_msg}")
                        logger.warning(f"AI 模型 {model} 调用失败: {response.status_code} - {error_msg}")
            except Exception as e:
                errors.append(f"{model}: {str(e)}")
                logger.error(f"AI 模型 {model} 异常: {e}")
        
        
        logger.error(f"所有模型尝试均失败: {'; '.join(errors)}")
        return None

    def _generate_metrics_hash(self, metrics: Any) -> str:
        """生成指标的 MD5 哈希"""
        if not metrics:
            return "empty"
        # 确保字典键有序
        metrics_str = json.dumps(metrics, sort_keys=True, ensure_ascii=False)
        return hashlib.md5(metrics_str.encode()).hexdigest()
    
    async def ask_ai(self, prompt: str, system_prompt: str = None, max_tokens: int = 2000, timeout: int = None) -> Dict[str, Any]:
        """通用AI问答接口（供其他模块调用）"""
        if system_prompt is None:
            system_prompt = "你是一位专业的金融分析师，提供准确、专业的分析和建议。"
        
        content = await self._call_ai(system_prompt, prompt, max_tokens, timeout=timeout)
        
        if content:
            return {
                'success': True,
                'content': content
            }
        else:
            return {
                'success': False,
                'error': '所有AI模型都不可用，请稍后重试'
            }
    
    async def generate_fund_analysis(
        self, 
        code: str, 
        metrics: Dict[str, Any]
    ) -> Dict[str, Any]:
        """生成基金分析"""
        # 统一缓存键策略: 功能:代码:指标哈希
        metrics_hash = self._generate_metrics_hash(metrics)
        cache_key = f"fund_analysis:{code}:{metrics_hash}"
        cached = self.db.get_ai_cache(cache_key)
        if cached:
            return {
                'success': True,
                'content': cached,
                'source': 'cache'
            }
        
        # 构建提示词
        system_prompt = """你是一位专业的基金分析师，擅长解读基金的量化指标并给出投资建议。
请用简洁专业的语言分析基金，包括：
1. 总体评价（1-2句话）
2. 主要优势（2-3点）
3. 潜在风险（1-2点）
4. 投资建议（适合什么类型的投资者）

使用 Markdown 格式，保持简洁，总字数控制在 300 字以内。"""
        
        user_prompt = self._build_fund_prompt(code, metrics)
        
        # 调用 AI
        content = await self._call_ai(system_prompt, user_prompt, max_tokens=1000)
        
        if content:
            # 保存缓存
            self.db.set_ai_cache(cache_key, content, self.current_model, ttl_hours=24)
            return {
                'success': True,
                'content': content,
                'source': 'ai',
                'model': self.current_model
            }
        
        # 降级为规则化分析
        fallback_content = self._generate_fallback_analysis(code, metrics)
        return {
            'success': True,
            'content': fallback_content,
            'source': 'fallback'
        }
    
    def _build_fund_prompt(self, code: str, metrics: Dict) -> str:
        """构建基金分析提示词"""
        name = metrics.get('name', code)
        
        prompt = f"""请分析以下基金：

**基金名称**: {name}
**基金代码**: {code}
**数据日期**: {metrics.get('nav_date', '未知')}

**核心指标**:
- Alpha: {metrics.get('alpha', 'N/A')}%
- Beta: {metrics.get('beta', 'N/A')}
- 夏普比率: {metrics.get('sharpe', 'N/A')}
- 年化收益: {metrics.get('annual_return', 'N/A')}%
- 年化波动率: {metrics.get('volatility', 'N/A')}%
- 最大回撤: {metrics.get('max_drawdown', 'N/A')}%
- 当前回撤: {metrics.get('current_drawdown', 'N/A')}%
- 胜率: {metrics.get('win_rate', 'N/A')}%
- 盈亏比: {metrics.get('profit_loss_ratio', 'N/A')}

**收益表现**:
- 近1周: {metrics.get('return_1w', 'N/A')}%
- 近1月: {metrics.get('return_1m', 'N/A')}%
- 近3月: {metrics.get('return_3m', 'N/A')}%
- 近6月: {metrics.get('return_6m', 'N/A')}%
- 近1年: {metrics.get('return_1y', 'N/A')}%

**综合评分**: {metrics.get('score', 'N/A')}/100
"""
        return prompt
    
    def _generate_fallback_analysis(self, code: str, metrics: Dict) -> str:
        """生成规则化降级分析"""
        name = metrics.get('name', code)
        score = metrics.get('score', 0)
        alpha = metrics.get('alpha', 0)
        sharpe = metrics.get('sharpe', 0)
        max_dd = metrics.get('max_drawdown', 0)
        annual_return = metrics.get('annual_return', 0)
        
        # 评级
        if score >= 80:
            rating = "优秀"
            rating_desc = "该基金综合表现突出"
        elif score >= 60:
            rating = "良好"
            rating_desc = "该基金综合表现较好"
        elif score >= 40:
            rating = "一般"
            rating_desc = "该基金表现中规中矩"
        else:
            rating = "较弱"
            rating_desc = "该基金表现欠佳"
        
        # 优势分析
        advantages = []
        if alpha > 5:
            advantages.append(f"超额收益能力强，Alpha 达 {alpha}%")
        if sharpe > 1.5:
            advantages.append(f"风险调整后收益优秀，夏普比率 {sharpe}")
        if max_dd < 15:
            advantages.append(f"回撤控制良好，最大回撤仅 {max_dd}%")
        if annual_return > 20:
            advantages.append(f"年化收益可观，达 {annual_return}%")
        
        if not advantages:
            advantages.append("各项指标表现均衡")
        
        # 风险提示
        risks = []
        if max_dd > 30:
            risks.append(f"回撤较大（{max_dd}%），需关注风险承受能力")
        if metrics.get('volatility', 0) > 25:
            risks.append(f"波动较高，适合风险偏好较高的投资者")
        if alpha < 0:
            risks.append("Alpha 为负，跑输基准")
        
        if not risks:
            risks.append("暂无明显风险点，但投资需谨慎")
        
        # 组装分析
        analysis = f"""## {name} 分析报告

### 总体评价
{rating_desc}，综合评分 **{score}** 分（{rating}）。

### 主要优势
"""
        for adv in advantages[:3]:
            analysis += f"- {adv}\n"
        
        analysis += "\n### 潜在风险\n"
        for risk in risks[:2]:
            analysis += f"- {risk}\n"
        
        analysis += f"""
### 投资建议
"""
        if score >= 70 and max_dd < 20:
            analysis += "适合追求稳健收益的长期投资者，可考虑作为核心配置。"
        elif score >= 60:
            analysis += "适合有一定风险承受能力的投资者，建议作为卫星配置。"
        else:
            analysis += "建议谨慎考虑，或等待更好的入场时机。"
        
        analysis += "\n\n*（此分析由规则引擎生成，仅供参考）*"
        
        return analysis
    
    async def generate_portfolio_diagnosis(
        self, 
        portfolio_data: List[Dict],
        stats: Dict = None
    ) -> Dict[str, Any]:
        """生成持仓诊断报告 (带缓存)"""
        if not portfolio_data:
            return {
                'success': False,
                'error': '无持仓数据'
            }
        
        # 如果没有传 stats，简单的计算一些基础统计
        if stats is None:
            total_shares = sum(p.get('shares', 0) for p in portfolio_data)
            stats = {
                'position_count': len(portfolio_data),
                'total_cost': sum(p.get('shares', 0) * p.get('cost_price', 0) for p in portfolio_data),
                'total_value': 0, # 这里没有最新净值无法准确计算，提示里会说明
                'category_distribution': {},
                'theme_distribution': {}
            }
        
        try:
            # 0. 检查缓存
            metrics_hash = self._generate_metrics_hash({
                "portfolio": [{"c": p['fund_code'], "s": p.get('shares', 0)} for p in portfolio_data],
                "stats": stats
            })
            cache_key = f"portfolio_diagnosis:{metrics_hash}"
            cache = get_cache_manager()
            cached = cache.get(cache_key)
            if cached:
                logger.info(f"持仓诊断命中缓存: {cache_key}")
                return cached

            # 1. 构建提示词
            prompt = self._build_portfolio_prompt(portfolio_data, stats)
            
            system_prompt = """你是一个专业的财富管理顾问和定投专家。
请根据用户的基金持仓数据，从以下维度进行深度诊断：
1. 资产配置：股债比例是否合理，分散度如何。
2. 风格穿透：是否存在特定行业或风格的过度暴露。
3. 风险提示：当前组合最大的潜在回撤风险。
4. 调仓建议：给出具体、可执行的操作建议。
请使用 Markdown 格式，语气专业且富有同理心。"""

            # 2. 调用 AI
            content = await self.ask_ai(prompt, system_prompt=system_prompt)
            result = {
                'success': True,
                'content': content
            }
            # 缓存 10 分钟
            cache.set(cache_key, result, expire=600)
            return result
        except Exception as e:
            logger.error(f"AI 生成持仓诊断失败: {e}")
            return {'success': False, 'error': str(e)}
    
    def _build_portfolio_prompt(self, portfolio_data: List[Dict], stats: Dict) -> str:
        """构建持仓诊断提示词"""
        prompt = f"""请对以下个人投资组合进行深度诊断：

**组合汇总**:
- 持仓基金数: {stats.get('position_count', 0)}
- 总投入成本: {stats.get('total_cost', 0):.2f}
- 当前预估市值: {stats.get('total_value', 0):.2f} (该数据仅供参考)
- 历史盈亏: {stats.get('total_profit', 0):.2f} ({stats.get('profit_pct', 0):.2f}%)

**资产分类分布**:
"""
        for cat, weight in stats.get('category_distribution', {}).items():
            prompt += f"- {cat}: {weight:.1f}%\n"
            
        prompt += "\n**核心行业/主题分布**:\n"
        for theme, weight in stats.get('theme_distribution', {}).items():
            prompt += f"- {theme}: {weight:.1f}%\n"
            
        prompt += "\n**个股穿透分布 (前10大重仓股)**:\n"
        for stock, weight in stats.get('stock_exposure', {}).items():
            # stock_exposure 里的权重是 0-100 的百分比
            prompt += f"- {stock}: {weight:.1f}%\n"
            
        prompt += "\n**详细持仓明细**:\n"
        for i, p in enumerate(portfolio_data, 1):
            prompt += f"{i}. {p.get('fund_name')} ({p.get('fund_code')}): 份额 {p.get('shares')}, 成本价 {p.get('cost_price')}\n"
            
        return prompt

    async def generate_recommendation_summary(
        self, 
        funds: List[Dict], 
        theme: str = None,
        news_list: List[Dict] = None
    ) -> Dict[str, Any]:
        """生成推荐摘要"""
        if not funds:
            return {
                'success': False,
                'error': '无基金数据'
            }
        
        # 统计数据
        total_funds = len(funds)
        avg_score = sum(f.get('score', 0) for f in funds) / total_funds if total_funds else 0
        high_alpha_count = sum(1 for f in funds if f.get('alpha', 0) > 10)
        low_risk_count = sum(1 for f in funds if f.get('max_drawdown', 0) < 15)
        
        theme_text = theme if theme else "全市场"
        
        # News Analysis (Simple Keyword Based)
        sentiment_text = "市场情绪平稳"
        sentiment_class = "text-muted"
        hot_topic = "无明显热点"
        
        if news_list:
            pos_words = ["上涨", "新高", "大涨", "突破", "利好", "surge", "record"]
            neg_words = ["下跌", "跳水", "新低", "破位", "利空", "crash", "drop"]
            
            pos_count = sum(1 for n in news_list for w in pos_words if w in n['title'])
            neg_count = sum(1 for n in news_list for w in neg_words if w in n['title'])
            
            if pos_count > neg_count * 1.5:
                sentiment_text = "多头情绪主导"
                sentiment_class = "highlight-gold"
            elif neg_count > pos_count * 1.5:
                sentiment_text = "避险情绪升温"
            
            # Simple topic extraction
            topics = {}
            for n in news_list:
                for k in ["科技", "医药", "新能源", "券商", "半导体", "美股", "港股"]:
                    if k in n['title']:
                        topics[k] = topics.get(k, 0) + 1
            if topics:
                hot_topic = max(topics.items(), key=lambda x: x[1])[0]

        # 生成符合用户要求的 HTML 结构 (仅保留摘要部分，各模块独立渲染)
        html_content = f"""
<div class="analysis-intro">
  <p style="margin-bottom: 0.5rem; color: rgba(255,255,255,0.9); font-size: 0.95rem;">
    基于本周最新数据复盘，<b>{theme_text}</b> 共筛选出 <b>{total_funds}</b> 只优质基金。
  </p>
  
  <div class="ai-pulse" style="display: flex; flex-wrap: wrap; gap: 0.5rem; align-items: center;">
    <span class="pulse-tag" style="background: rgba(255,255,255,0.1); padding: 4px 10px; border-radius: 20px; font-size: 0.8rem; display: flex; align-items: center; color: #bdc3c7;">
        🤖 覆盖 {len(news_list) if news_list else 0} 条快讯
    </span>
    <span class="pulse-tag {sentiment_class}" style="background: rgba(255,255,255,0.1); padding: 4px 10px; border-radius: 20px; font-size: 0.8rem; display: flex; align-items: center;">
        📊 {sentiment_text}
    </span>
    <span class="pulse-tag" style="background: rgba(255,255,255,0.1); padding: 4px 10px; border-radius: 20px; font-size: 0.8rem; display: flex; align-items: center; color: #f1c40f;">
        🔥 {hot_topic}
    </span>
  </div>
</div>
"""
        return {
            'success': True,
            'content': html_content,
            'source': 'rule_html'
        }

    async def analyze_fund_news(self, code: str, news_list: List[Dict]) -> str:
        """分析基金新闻与公告"""
        try:
            if not news_list:
                return "近期无重要新闻公告。"
                
            news_text = "\n".join([f"- {n['date']} [{n.get('type','新闻')}] {n['title']}" for n in news_list[:5]])
            
            prompt = f"请根据以下新闻公告，分析基金 {code} 的近期动向和潜在影响：\n{news_text}\n请简短总结（100字以内）。"
            system_prompt = "你是一位专业的金融舆情分析师。"
            
            result = await self.ask_ai(prompt, system_prompt=system_prompt, max_tokens=300)
            
            if result.get('success'):
                return result.get('content')
            return "分析不可用"
        except Exception as e:
            logger.error(f"News analysis failed: {e}")
            return f"分析失败: {e}"


    async def generate_market_macro_analysis(self, news_list: List[Dict]) -> str:
        """生成市场宏观 AI 分析报告 (基于新闻、局势)"""
        try:
            if not news_list:
                return "当前缺乏足够的实时新闻数据进行宏观分析。"

            news_text = "\n".join([f"- {n['date']} {n['title']} ({n.get('source', '未知')})" for n in news_list[:10]])
            
            system_prompt = """你是一位顶级的首席经济学家和投资策略师。
请根据提供的实时新闻、政治局势和市场热点，进行深度宏观分析。
你的回复必须包含：
1. **行情综述**：一句话概括当前市场核心驱动力。
2. **AI 预判**：基于当前新闻（如降准、美联储加息、大选、政策导向等）预测短期走势。
3. **策略建议**：
   - ✅ **推荐关注**：哪些板块/风格目前具备投资价值，简述理由。
   - ⚠️ **规避警告**：哪些板块/风格目前存在较高风险，明确说明原因（即用户提到的“哪些不能买”）。
请使用 Markdown 格式，语气专业、权威、果断。控制在 300 字以内。"""

            user_prompt = f"以下是最近的市场热点新闻和公告事项：\n\n{news_text}\n\n请以此生成最新的投资策略指导。"
            
            # 检查缓存
            import hashlib
            cache_key = f"macro_analysis:{hashlib.md5(user_prompt.encode()).hexdigest()}"
            cached = self.db.get_ai_cache(cache_key)
            if cached:
                 return cached

            result = await self.ask_ai(user_prompt, system_prompt=system_prompt, max_tokens=1000)
            
            if result.get('success'):
                content = result.get('content')
                self.db.set_ai_cache(cache_key, content, self.current_model, ttl_hours=2)
                return content
            return "AI 服务暂时无法处理宏观数据分析。"
        except Exception as e:
            logger.error(f"Macro analysis failed: {e}")
            return f"分析失败: {e}"

    async def generate_structured_fund_analysis(self, fund_name: str, code: str, metrics: Dict[str, Any]) -> Dict[str, Any]:
        """生成结构化基金分析 - 遵循 v4.0 JSON 协议"""
        try:
            # Create a unique cache key based on metrics hash
            metrics_hash = self._generate_metrics_hash(metrics)
            cache_key = f"structured_analysis:{code}:{metrics_hash}"
            
            cached_result = self.db.get_ai_cache(cache_key)
            if cached_result:
                try:
                    return json.loads(cached_result)
                except json.JSONDecodeError:
                    logger.warning(f"Cached structured analysis for {code} is not valid JSON. Re-generating.")
                    # If cached content is invalid, proceed to generate new content

            system_prompt = """你是一个专业的基金投研助手。你的输出将被前端直接渲染为 UI 卡片，必须严格遵守 JSON 格式。
每一个结论必须带有 [citation] 字段说明数据来源。语气客观、冷静，禁止使用营销话术。
如果数据不足，直接输出 null，不要编造。
"""
            user_prompt = f"""请对基金 {fund_name} ({code}) 进行结构化深度分析。
数据 Context:
- 复权净值日期: {metrics.get('nav_date')}
- 近1年收益率: {metrics.get('return_1y', 0)}%
- 最大回撤: {metrics.get('max_drawdown', 0)}%
- 夏普比率: {metrics.get('sharpe', 0)}
- Beta值: {metrics.get('beta', 1.0)}

请返回如下格式的 JSON (不要包含 Markdown 格式块):
{{
  "summary_card": {{
    "title": "基调总结",
    "verdict": "适合...的投资者。",
    "tags": ["...", "..."],
    "citation": "基于..."
  }},
  "attribution_card": {{
    "title": "近期表现归因",
    "points": [
      {{ "reason": "...", "impact": "...", "source": "..." }}
    ]
  }},
  "stress_test": {{
    "scenario": "若沪深300下跌10%",
    "prediction": "预计下跌...",
    "beta_ref": "历史Beta值为..."
  }},
  "manager_report": {{
    "style": "价值/成长/均衡/博弈",
    "rating": "A/B/C",
    "description": "精炼的一句话描述经理风格"
  }}
}}
"""
            result = await self.ask_ai(user_prompt, system_prompt=system_prompt, max_tokens=1000)
            
            if result.get('success'):
                content = result.get('content', '')
                # Clean content
                if "```json" in content:
                    content = content.split("```json")[1].split("```")[0].strip()
                elif "```" in content:
                    content = content.split("```")[1].split("```")[0].strip()
                
                try:
                    parsed_content = json.loads(content)
                    self.db.set_ai_cache(cache_key, content, self.current_model, ttl_hours=24) # Cache for 24 hours
                    return parsed_content
                except Exception as e:
                    logger.error(f"JSON Parse Error: {e}\nContent: {content}")
                    return {"error": "解析失败", "raw": content}
            
            return {"error": "AI 调用失败"}
        except Exception as e:
            logger.error(f"Structured analysis failed: {e}")
            return {"error": str(e)}

    async def translate_semantic_query(self, query: str) -> Dict[str, Any]:
        """将自然语言查询转换为结构化过滤条件 (Deep Search) + 智能对话"""
        try:
            system_prompt = """你是一个专业的基金投资助手 (AI Fund Advisor)。
你的目标是理解用户的自然语言输入，并返回一个 JSON 对象。

请根据用户意图选择不同的返回策略：

1. **意图：筛选基金/查找数据**
   - 提取结构化过滤条件到 `filters` 字段。
   - 在 `interpretation` 字段中用自然语言（中文）描述你的筛选逻辑。
   - 可用维度：
     - themes (列表): ['科技', '医疗', '消费', '新能源', '人工智能', '红利', '白酒', '半导体', '军工', '稳健']
     - return_1y (对象): { "op": ">"|"<", "val": 数值(百分比) }
     - max_drawdown_1y (对象): { "op": ">"|"<", "val": 数值(百分比) }
     - sharpe_1y (对象): { "op": ">"|"<", "val": 数值 }
     - risk_level (字符串): '低风险'|'中风险'|'高风险'

2. **意图：闲聊/问候/通用理财问题**
   - `filters` 字段设为空对象 `{}`。
   - 在 `interpretation` 字段中直接回答用户的问题，或者进行礼貌的对话。语气要专业、亲切且有帮助。
   - 如果用户问“你买什么能赚钱”，这属于通用理财问题，你可以建议用户关注“高评分”或“近期热点”基金，并尝试转换成宽松的筛选条件（如 score > 80）。

**输出格式示例 (JSON)**:
{
  "filters": { "themes": ["科技"], "return_1y": { "op": ">", "val": 10 } },
  "interpretation": "明白了，正在为您筛选近一年收益率超过 10% 的科技类基金..."
}

或 (闲聊):
{
  "filters": {},
  "interpretation": "您好！我是您的 AI 私人管家，可以帮您筛选基金、诊断持仓或分析市场热点。请问有什么可以帮您？"
}

请直接返回 JSON，不要包含 Markdown 标记。"""
            
            user_prompt = f"用户输入: \"{query}\"\n请分析意图并生成 JSON 响应。"
            
            result = await self.ask_ai(user_prompt, system_prompt=system_prompt, max_tokens=500)
            
            if result.get('success'):
                content = result.get('content', '{}')
                # Clean block markings if any
                if "```" in content:
                    content = content.split("```")[1]
                    if content.startswith("json"):
                        content = content[4:]
                try:
                    data = json.loads(content.strip())
                    # Flatten logic for backward compatibility
                    parsed = data.get('filters', {})
                    parsed['interpretation'] = data.get('interpretation', '正在搜索...')
                    return parsed
                except:
                    logger.error(f"Semantic parse failed: {content}")
                    # Fallback
                    return {"themes": [query], "interpretation": f"正在为您搜索包含 '{query}' 的基金..."}
            return {}
        except Exception as e:
            logger.error(f"Semantic translation error: {e}")
            return {}



    async def generate_manager_rating(self, name: str, career_summary: str) -> Dict[str, Any]:
        """生成经理 AI 评级与风格画像"""
        try:
            # 检查缓存
            summary_hash = hashlib.md5(career_summary.encode()).hexdigest()
            cache_key = f"manager_rating:{name}:{summary_hash}"
            cached_json = self.db.get_ai_cache(cache_key)
            if cached_json:
                try:
                    return json.loads(cached_json)
                except:
                    pass

            system_prompt = "你是一位资深的基金评价专家，擅长从过往业绩和投教言论中总结经理风格。"
            user_prompt = f"请根据基金经理 {name} 的履历总结，给出 AI 风格标签和能力评级：\n{career_summary}\n请返回 JSON: {{'style': '...', 'rating': 'A/B/C', 'pros': ['...', '...']}}"
            
            result = await self.ask_ai(user_prompt, system_prompt=system_prompt, max_tokens=500)
            if result.get('success'):
                content = result.get('content', '{}')
                if "```" in content:
                    content = content.split("```")[1]
                    if content.startswith("json"): content = content[4:]
                
                content = content.strip()
                try:
                     parsed = json.loads(content)
                     self.db.set_ai_cache(cache_key, content, self.current_model, ttl_hours=24*7) # 经理风格长期不变
                     return parsed
                except:
                     return {"style": "数据解析错误", "rating": "C", "pros": []}

            return {"style": "均衡型", "rating": "B", "pros": ["数据不足"]}
        except Exception as e:
            logger.error(f"Manager rating failed: {e}")
            return {"style": "未知", "rating": "B", "pros": []}

# 全局单例
_ai_service: Optional[AIService] = None

def get_ai_service() -> Optional[AIService]:
    """获取 AI 服务实例"""
    global _ai_service
    
    settings = get_settings()
    if not settings.AI_API_KEY:
        return None
    
    if _ai_service is None:
        _ai_service = AIService()
    
    return _ai_service
