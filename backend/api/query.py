# backend/api/query.py
"""
查询接口 - 无需鉴权
"""

from fastapi import APIRouter, Query, HTTPException, Request
from typing import Optional, List, Dict, Any
from pydantic import BaseModel
import json
import datetime
import logging
logger = logging.getLogger(__name__)

try:
    from services.snapshot import get_snapshot_service
    from services.ai_service import get_ai_service
    # from services.vector_service import get_vector_service
    from services.data_fetcher import get_data_fetcher
    from services.news_service import get_news_service
    # from services.prediction_service import get_trend_predictor
    from services.backtest_service import get_backtest_service
    from services.macro_service import get_macro_service
    from services.sector_service import get_sector_service
    # from services.watchlist_service import get_watchlist_service
    from database import get_db
    from services.fee_service import get_fee_service
    from services.health_service import get_health_service
    from services.style_service import get_style_service
    from services.investment_service import get_investment_service
    from services.calendar_service import get_calendar_service
    from services.money_flow_service import get_money_flow_service
    from services.portfolio_service import get_portfolio_service
    from services.roi_review_service import get_roi_service
    from services.dividend_service import get_dividend_service
    from services.action_service import get_action_service
    from services.dca_service import get_dca_service
    from services.portfolio_builder import get_portfolio_builder
    from api.responses import ApiResponse, success_response, error_response
except (ImportError, ValueError):
    from backend.services.snapshot import get_snapshot_service
    from backend.services.ai_service import get_ai_service
    from backend.services.data_fetcher import get_data_fetcher
    from backend.services.news_service import get_news_service
    from backend.services.backtest_service import get_backtest_service
    from backend.services.macro_service import get_macro_service
    from backend.services.sector_service import get_sector_service
    from backend.database import get_db
    from backend.services.fee_service import get_fee_service
    from backend.services.health_service import get_health_service
    from backend.services.style_service import get_style_service
    from backend.services.investment_service import get_investment_service
    from backend.services.calendar_service import get_calendar_service
    from backend.services.money_flow_service import get_money_flow_service
    from backend.services.portfolio_service import get_portfolio_service
    from backend.services.roi_review_service import get_roi_service
    from backend.services.dividend_service import get_dividend_service
    from backend.services.action_service import get_action_service
    from backend.services.dca_service import get_dca_service
    from backend.services.portfolio_builder import get_portfolio_builder
    from backend.api.responses import ApiResponse, success_response, error_response
import logging
import time
import datetime

logger = logging.getLogger(__name__)

router = APIRouter()

class SearchDeepRequest(BaseModel):
    q: str

class CompareRequest(BaseModel):
    codes: List[str]

class AIChatQueryRequest(BaseModel):
    query: str
    history: Optional[List[Dict[str, str]]] = []

class PortfolioDiagnoseRequest(BaseModel):
    funds: List[Dict[str, Any]]

class WatchlistAddRequest(BaseModel):
    code: str
    name: str

class WatchlistRemoveRequest(BaseModel):
    code: str

class DcaPlanRequest(BaseModel):
    fund_code: str
    fund_name: str
    base_amount: float
    frequency: str = 'weekly'
    day_of_week: Optional[int] = None
    day_of_month: Optional[int] = None

class PortfolioBuyRequest(BaseModel):
    fund_code: str
    fund_name: str
    shares: float
    cost_price: float
    buy_date: str
    notes: Optional[str] = None

class PortfolioSellRequest(BaseModel):
    position_id: int
    sell_price: float
    sell_date: str

class PortfolioBuildRequest(BaseModel):
    amount: float
    risk_level: str


@router.get("/recommend")
async def get_recommendations(
    theme: Optional[str] = Query(None, description="主题筛选: 科技/消费/医药/新能源/金融/制造/红利"),
    category: Optional[str] = Query(None, description="分类: TOP10/高Alpha/长线/短线/防守")
):
    """
    获取智能推荐列表
    
    - theme: 按主题筛选
    - category: 按投资标签筛选
    """
    try:
        service = get_snapshot_service()
        result = await service.get_recommendations(theme=theme, category=category)
        return success_response(data=result)
    except Exception as e:
        logger.error(f"Failed to get recommendations: {e}")
        return error_response(error=str(e))

# /predict_tomorrow 已删除


# 在全局范围添加简单的缓存来加速在线搜索
_online_fund_cache = {
    'data': None,
    'last_updated': 0
}

# 市场热点缓存 (Result Cache)
_hotspots_cache = {
    'data': None,
    'updated_at': None
}

@router.get("/search")
async def search_funds(q: str, limit: int = 10):
    """
    搜索基金（名称或代码），支持数据库外实时检索
    """
    try:
        db = get_db()
        q = q.strip()
        if not q:
            return success_response(data={'results': [], 'total': 0})
            
        # 1. 6位数字精确匹配代码
        if q.isdigit() and len(q) == 6:
            fund = db.get_fund(q)
            if fund:
                return success_response(data={
                    'results': [{**fund, 'is_online': False}],
                    'total': 1
                })
            
            # 本地未找到，尝试在线查找
            try:
                import akshare as ak
                import time
                
                # 使用缓存或获取新数据
                now = time.time()
                if _online_fund_cache['data'] is None or (now - _online_fund_cache['last_updated'] > 3600):
                    _online_fund_cache['data'] = ak.fund_name_em()
                    _online_fund_cache['last_updated'] = now
                
                all_funds_df = _online_fund_cache['data']
                fund_row = all_funds_df[all_funds_df['基金代码'] == q]
                if not fund_row.empty:
                    return success_response(data={
                        'results': [{
                            'code': q,
                            'name': fund_row.iloc[0]['基金简称'],
                            'fund_type': fund_row.iloc[0]['基金类型'],
                            'is_online': True
                        }],
                        'total': 1
                    })
            except Exception as e:
                logger.warning(f"在线查找代码 {q} 失败: {e}")

            return success_response(data={'results': [], 'total': 0}, message=f'未找到代码为 {q} 的基金')
        
        # 2. 模糊搜索名称
        # 优先在本地寻找
        results = db.search_funds(q, limit=limit)
        for r in results:
            r['is_online'] = False
            
        # 3. 如果本地结果较少，尝试在线搜索（合并结果）
        try:
            import akshare as ak
            import time
            
            now = time.time()
            if _online_fund_cache['data'] is None or (now - _online_fund_cache['last_updated'] > 3600):
                logger.info("在线获取全市场基金列表用于搜索...")
                _online_fund_cache['data'] = ak.fund_name_em()
                _online_fund_cache['last_updated'] = now
            
            all_funds_df = _online_fund_cache['data']
            
            # 判断是否为拼音查询（纯英文字母）
            is_pinyin_query = q.isalpha() and all(c.isascii() for c in q)
            
            if is_pinyin_query:
                # 使用拼音匹配
                try:
                    try:
                        from ..utils.pinyin import pinyin_match, rank_pinyin_match
                    except (ImportError, ValueError):
                        from utils.pinyin import pinyin_match, rank_pinyin_match
                    
                    matched_funds = []
                    for _, row in all_funds_df.iterrows():
                        name = row['基金简称']
                        rank = rank_pinyin_match(name, q)
                        if rank > 0:
                            matched_funds.append({
                                'code': str(row['基金代码']).zfill(6),
                                'name': name,
                                'fund_type': row['基金类型'],
                                'is_online': True,
                                '_rank': rank
                            })
                    
                    # 按匹配度排序
                    matched_funds.sort(key=lambda x: x['_rank'], reverse=True)
                    
                    for fund in matched_funds[:limit * 2]:
                        code = fund['code']
                        if any(r['code'] == code for r in results):
                            continue
                        del fund['_rank']
                        results.append(fund)
                        if len(results) >= limit * 2:
                            break
                except ImportError:
                    logger.warning("拼音模块导入失败，使用普通搜索")
                    # 回退到普通搜索
                    mask = all_funds_df['基金简称'].str.contains(q, na=False, case=False)
                    online_matches = all_funds_df[mask].head(limit * 2)
                    for _, row in online_matches.iterrows():
                        code = str(row['基金代码']).zfill(6)
                        if any(r['code'] == code for r in results):
                            continue
                        results.append({
                            'code': code,
                            'name': row['基金简称'],
                            'fund_type': row['基金类型'],
                            'is_online': True
                        })
                        if len(results) >= limit * 2:
                            break
            else:
                # 普通中文/数字搜索
                mask = (
                    all_funds_df['基金简称'].str.contains(q, na=False) |
                    all_funds_df['基金代码'].str.contains(q, na=False)
                )
                online_matches = all_funds_df[mask].head(limit * 2)
                
                for _, row in online_matches.iterrows():
                    code = str(row['基金代码']).zfill(6)
                    # 避免与本地结果重复
                    if any(r['code'] == code for r in results):
                        continue
                        
                    results.append({
                        'code': code,
                        'name': row['基金简称'],
                        'fund_type': row['基金类型'],
                        'is_online': True
                    })
                    
                    if len(results) >= limit * 2:
                        break
        except Exception as online_err:
            logger.warning(f"在线名称搜索失败: {online_err}")

        # 4. 后处理：为搜索结果注入评分并二次排序
        try:
            # 获取结果中所有基金的评分
            codes = [r['code'] for r in results]
            snapshot = db.get_latest_snapshot()
            if snapshot and codes:
                # 批量获取本地数据库中的指标（含评分）
                db_funds = db.get_funds_by_codes(snapshot['id'], codes)
                score_map = {f['code']: f.get('score', 0) for f in db_funds}
                
                # 注入评分
                for r in results:
                    r['score'] = score_map.get(r['code'], 0)
                    
                # 二次排序：(匹配权重 * 0.3) + (评分权重 * 0.7)
                def sort_key(x):
                    match_weight = x.get('_rank', 50) 
                    score_weight = x.get('score', 0)
                    return match_weight * 0.3 + score_weight * 0.7
                    
                results.sort(key=sort_key, reverse=True)
        except Exception as e:
            logger.warning(f"搜索结果评分排序优化失败: {e}")

        # 统一使用 success_response 返回，确保前端结构一致
        return success_response(data={
            'results': results[:limit], 
            'total': len(results)
        })
    except Exception as e:
        import traceback
        logger.error(f"搜索接口异常: {e}\n{traceback.format_exc()}")
        return {
            'success': False,
            'error': str(e),
            'results': []
        }


@router.get("/analyze/{code}")
async def analyze_fund(code: str):
    """
    分析单只基金
    
    返回基金的详细指标和AI分析
    """
    try:
        # 验证代码格式
        code = str(code).zfill(6)
        if not code.isdigit() or len(code) != 6:
            raise HTTPException(status_code=400, detail="无效的基金代码，需要6位数字")
        
        service = get_snapshot_service()
        result = service.analyze_single_fund(code)
        
        # 如果成功且有AI服务，添加AI分析
        if result.get('status') == 'success':
            try:
                data_fetcher = get_data_fetcher()
                result['manager'] = data_fetcher.get_fund_manager_info(code)
                result['ranks'] = data_fetcher.get_fund_ranks(code)
                result['holdings'] = data_fetcher.get_fund_holdings(code)

                ai_service = get_ai_service()
                if ai_service:
                    import asyncio
                    
                    # Store manager info for use in rating task
                    mgr_info = result.get('manager', {})
                    
                    # Define tasks
                    async def task_basic():
                        return await ai_service.generate_fund_analysis(
                            code=code,
                            metrics=result.get('metrics', {})
                        )
                    
                    async def task_struct():
                        return await ai_service.generate_structured_fund_analysis(
                            fund_name=result.get('name', ''),
                            code=code,
                            metrics=result.get('metrics', {})
                        )
                        
                    async def task_mgr():
                        if mgr_info:
                            return await ai_service.generate_manager_rating(
                                name=mgr_info.get('name', '未知'),
                                career_summary=f"在管规模{mgr_info.get('scale')}, 公司{mgr_info.get('company')}"
                            )
                        return None

                    # Execute in parallel
                    res_basic, res_struct, res_mgr = await asyncio.gather(
                        task_basic(),
                        task_struct(),
                        task_mgr()
                    )

                    # 1. 基础文本分析 (V3)
                    if res_basic.get('success'):
                        result['ai_analysis'] = res_basic.get('content', '暂无AI分析')
                    
                    # 2. 结构化深度分析 (V4)
                    result['ai_v4_analysis'] = res_struct

                    # 3. 基金经理 AI 评测 (V4)
                    if res_mgr:
                        result['manager_ai'] = res_mgr
                else:
                    result['ai_analysis'] = 'AI服务未配置'

                # 4. 注入实时估值 (修复 0% 涨跌幅问题)
                try:
                    realtime_vals = data_fetcher.get_realtime_valuation_batch([code])
                    if code in realtime_vals:
                        val = realtime_vals[code]
                        result['metrics']['estimation_nav'] = val.get('estimation_nav')
                        result['metrics']['estimation_growth'] = val.get('estimation_growth')
                        result['metrics']['realtime_time'] = val.get('time')
                except Exception as e:
                    logger.warning(f"Failed to inject realtime valuation for {code}: {e}")

            except Exception as ai_error:
                logger.error(f"Analysis update error for {code}: {ai_error}")
                if 'ai_analysis' not in result:
                    result['ai_analysis'] = f'分析服务部分异常: {str(ai_error)}'
        return result
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"分析服务异常: {e}")
        return {
            'status': 'error',
            'error': str(e)
        }

@router.post("/portfolio/diagnose")
async def diagnose_portfolio(portfolio: List[Dict[str, Any]]):
    """投资组合 AI 诊断"""
    try:
        ai_service = get_ai_service()
        if not ai_service:
            return {"error": "AI 服务不可用"}
            
        report = await ai_service.generate_portfolio_diagnosis(portfolio)
        return {"success": True, "report": report}
    except Exception as e:
        logger.error(f"Portfolio diagnosis failed: {e}")
        return {"success": False, "error": str(e)}

# /search/deep 已删除

@router.get("/analyze/{code}/v4")
async def analyze_fund_v4(code: str):
    """获取基金 v4 结构化分析 (AI 卡片协议)"""
    try:
        code = str(code).zfill(6)
        service = get_snapshot_service()
        # 获取基础指标 (优先从快照或实时获取)
        basic_info = service.analyze_single_fund(code)
        if basic_info.get('status') != 'success':
            raise HTTPException(status_code=404, detail="未找到基金基础数据")
            
        ai_service = get_ai_service()
        if not ai_service:
            return {"error": "AI 服务未配置"}
            
        structured_analysis = await ai_service.generate_structured_fund_analysis(
            fund_name=basic_info.get('name', '未知基金'),
            code=code,
            metrics=basic_info.get('metrics', {})
        )
        return structured_analysis
        
    except Exception as e:
        logger.error(f"V4 分析异常: {e}")
        return {"error": str(e)}





@router.get("/fund/{code}")
async def get_fund_info(code: str):
    """
    获取基金基础信息（快速查询，不含完整分析）
    """
    try:
        code = str(code).zfill(6)
        db = get_db()
        
        fund = db.get_fund(code)
        if not fund:
            return {
                'success': False,
                'error': f'未找到基金 {code}'
            }
        
        # 获取最新快照中的指标
        snapshot = db.get_latest_snapshot()
        metrics = None
        if snapshot:
            metrics = db.get_fund_metrics(snapshot['id'], code)
        
        return {
            'success': True,
            'fund': fund,
            'metrics': metrics,
            'snapshot_date': snapshot.get('snapshot_date') if snapshot else None
        }
    except Exception as e:
        return {
            'success': False,
            'error': str(e)
        }


@router.get("/update-status")
async def get_update_status():
    """
    获取更新状态
    
    用于前端轮询更新进度
    """
    try:
        service = get_snapshot_service()
        db = get_db()
        
        progress = service.get_progress()
        latest_snapshot = db.get_latest_snapshot()
        
        response = {
            'is_updating': service.is_updating(),
            'progress': progress,
            'latest_snapshot': None
        }
        
        if latest_snapshot:
            response['latest_snapshot'] = {
                'snapshot_date': latest_snapshot.get('snapshot_date'),
                'qualified_funds': latest_snapshot.get('qualified_funds', 0),
                'total_funds': latest_snapshot.get('total_funds', 0),
                'completed_at': latest_snapshot.get('completed_at'),
                'benchmark': latest_snapshot.get('benchmark', '000300.SH')
            }
        
        return response
    except Exception as e:
        return {
            'is_updating': False,
            'progress': None,
            'latest_snapshot': None,
            'error': str(e)
        }


@router.get("/models")
async def get_models():
    """
    获取AI模型信息
    """
    try:
        ai_service = get_ai_service()
        if ai_service:
            return ai_service.get_model_info()
        return {
            'success': False,
            'error': 'AI服务未配置',
            'current_model': None,
            'available_models': []
        }
    except Exception as e:
        return {
            'success': False,
            'error': str(e)
        }



@router.get("/models/refresh")
async def refresh_models():
    """
    刷新可用模型列表
    """
    try:
        ai_service = get_ai_service()
        if ai_service:
            models = await ai_service.fetch_available_models(force_refresh=True)
            return {
                'success': True,
                'count': len(models),
                'models': models[:30]  # 最多返回30个
            }
        return {
            'success': False,
            'error': 'AI服务未配置'
        }
    except Exception as e:
        return {
            'success': False,
            'error': str(e)
        }


@router.get("/health")
async def health_check():
    """
    健康检查
    """
    try:
        db = get_db()
        snapshot = db.get_latest_snapshot()
        fund_count = db.get_fund_count()
        
        # 检查AI服务
        ai_status = 'not_configured'
        try:
            ai_service = get_ai_service()
            if ai_service:
                ai_status = 'configured'
        except:
            ai_status = 'error'
        
        return {
            'status': 'healthy',
            'database': 'connected',
            'ai_service': ai_status,
            'latest_snapshot': snapshot.get('snapshot_date') if snapshot else None,
            'qualified_funds': snapshot.get('qualified_funds', 0) if snapshot else 0,
            'fund_count': fund_count
        }
    except Exception as e:
        return {
            'status': 'unhealthy',
            'error': str(e)
        }


@router.get("/snapshot/latest")
async def get_latest_snapshot():
    """
    获取最新快照信息
    """
    try:
        db = get_db()
        snapshot = db.get_latest_snapshot()
        
        if not snapshot:
            return {
                'success': False,
                'error': '暂无快照数据',
                'snapshot': None
            }
        
        return {
            'success': True,
            'snapshot': snapshot
        }
    except Exception as e:
        return {
            'success': False,
            'error': str(e)
        }


@router.get("/themes")
async def get_available_themes():
    """
    获取可用的主题列表（动态从数据库获取统计，但保留全量分类）
    """
    try:
        db = get_db()
        # 从数据库获取有数据的统计
        db_themes = db.get_all_themes()
        db_theme_map = {t['name']: t['count'] for t in db_themes}
        
        # 主题图标映射
        theme_icons = {
            '大消费': '🛒', '白酒': '🍷', '食品饮料': '🍔', '家电': '📺', '美妆': '💄', '旅游酒店': '🏨', '农业养殖': '🐷',
            '科技TMT': '💻', '半导体芯片': '🔌', '计算机': '💾', '电子': '📱', '通信': '📡', '传媒游戏': '🎮',
            '新能源': '⚡', '光伏': '☀️', '新能源车': '🚗', '风电': '🌬️', '储能': '🔋',
            '医药医疗': '🏥', '创新药': '🧪', '医疗器械': '🩺', '医疗服务': '👨‍⚕️', '中药': '🌿', '生物疫苗': '💉',
            '金融': '🏦', '银行': '🏧', '券商': '📈', '保险': '🛡️', '房地产': '🏠',
            '周期': '🔩', '煤炭': '🌑', '钢铁': '🏗️', '有色金属': '🔶', '化工': '🧪',
            '高端制造': '⚙️', '军工': '🚀', '航空航天': '🛰️', '国防军工': '🛡️', '机器人': '🤖',
            '红利': '💰', '人工智能': '🧠', 'AI': '🤖', '算力': '🏢', 'ESG': '🌱', '中特估': '🏛️', '出海': '🌐',
            '权益类': '📈', '固收类': '💵', '商品类': '🏆', 'REITs': '🏢',
            '全部': '🌐'
        }
        
        # 主题分类映射 (主列表 - 尽可能完整覆盖用户要求的细分)
        theme_categories = {
            '主流行业': [
                '大消费', '白酒', '食品饮料', '家电', '美妆', '旅游酒店', '农业养殖', 
                '科技TMT', '半导体芯片', '计算机', '电子', '通信', '传媒游戏', 
                '新能源', '光伏', '新能源车', '风电', '储能', 
                '医药医疗', '创新药', '医疗器械', '医疗服务', '中药', '生物疫苗', 
                '金融', '银行', '券商', '保险', '房地产', 
                '周期', '煤炭', '钢铁', '有色金属', '化工', 
                '高端制造', '航天军工', '航空航天', '国防军工', '机器人'
            ],
            '概念风格': ['红利', '人工智能', 'AI', '算力', 'ESG', '中特估', '出海'],
            '资产分类': ['权益类', '固收类', '商品类', 'REITs']
        }
        
        def get_icon(name):
            return theme_icons.get(name, '📊')
        
        # 构建完整的分组主题
        grouped_themes = {}
        for cat, names in theme_categories.items():
            cat_list = []
            for name in names:
                cat_list.append({
                    'id': name,
                    'name': name,
                    'icon': get_icon(name),
                    'count': db_theme_map.get(name, 0)
                })
            grouped_themes[cat] = cat_list
            
        # 处理不在主列表中的其他主题
        other_themes = []
        master_names = set()
        for names in theme_categories.values():
            master_names.update(names)
            
        for t in db_themes:
            if t['name'] not in master_names:
                other_themes.append({
                    'id': t['name'],
                    'name': t['name'],
                    'icon': get_icon(t['name']),
                    'count': t['count']
                })
        
        return {
            'success': True,
            'themes': db_themes, # 兼容
            'grouped_themes': grouped_themes,
            'other_themes': other_themes,
            'categories': [
                {'id': cat, 'name': cat} for cat in theme_categories.keys()
            ]
        }
    except Exception as e:
        logger.error(f"主题接口异常: {e}")
        return {
            'success': False,
            'error': str(e),
            'themes': [{'id': 'all', 'name': '全部', 'icon': '🌐'}]
        }


@router.get("/sectors/list")
async def get_sectors():
    """
    获取可用板块列表
    """
    try:
        try:
            from ..services.sector_service import get_sector_service
        except (ImportError, ValueError):
            from services.sector_service import get_sector_service
        service = get_sector_service()
        
        if not service:
            return {
                'success': False,
                'error': '板块服务未初始化',
                'sectors': []
            }
        
        sectors = service.get_available_sectors()
        return {
            'success': True,
            'sectors': sectors
        }
    except Exception as e:
        return {
            'success': False,
            'error': str(e),
            'sectors': []
        }


@router.get("/sectors/{sector}/metrics")
async def get_sector_metrics(sector: str):
    """
    获取板块指标及情绪分析
    
    Args:
        sector: 板块名称
    """
    try:
        service = get_sector_service()
        if not service:
            return {'success': False, 'error': '板块服务未初始化'}
        
        # 获取基础指标
        result = service.get_sector_metrics(sector)
        
        # 获取市场情绪 (Async)
        try:
            sentiment = await service.get_sector_sentiment(sector)
            if result.get('success'):
                result['sentiment'] = sentiment
        except Exception as se:
            logger.warning(f"获取板块情绪失败: {se}")
            
        return result
    except Exception as e:
        return {'success': False, 'error': str(e)}

@router.get("/news/market")
async def get_market_news():
    """获取市场新闻"""
    try:
        service = get_news_service()
        news = await service.get_market_news()
        sentiment = await service.analyze_market_sentiment()
        return {
            'success': True,
            'news': news,
            'sentiment': sentiment
        }
    except Exception as e:
        return {'success': False, 'error': str(e)}

@router.get("/news/fund/{code}")
async def get_fund_news(code: str):
    """获取基金新闻"""
    try:
        service = get_news_service()
        news = await service.get_fund_news(code)
        
        # 尝试AI分析
        ai_service = get_ai_service()
        analysis = ""
        if ai_service:
            analysis = await ai_service.analyze_fund_news(code, news)
            
        return {
            'success': True,
            'news': news,
            'analysis': analysis
        }
    except Exception as e:
        return {'success': False, 'error': str(e)}
# /sectors/{sector}/predict 已删除, 逻辑整合至 /metrics

@router.get("/fund/{code}/fees")
async def get_fund_fees(code: str):
    """获取基金费率分析"""
    try:
        service = get_fee_service()
        return await service.get_fund_fees(code)
    except Exception as e:
        return {'success': False, 'error': str(e)}

@router.get("/fund/{code}/health")
async def get_fund_health(code: str):
    """获取基金健康度诊断"""
    try:
        service = get_health_service()
        return await service.get_fund_health(code)
    except Exception as e:
        return {'success': False, 'error': str(e)}

@router.get("/fund/{code}/style")
async def get_fund_style(code: str):
    """获取基金投资风格分析"""
    try:
        service = get_style_service()
        return await service.get_fund_style(code)
    except Exception as e:
        return {'success': False, 'error': str(e)}

@router.get("/fund/{code}/smart-dca")
async def get_fund_smart_dca(code: str):
    """获取基金智能定投建议"""
    try:
        service = get_investment_service()
        return await service.get_smart_dca_suggestion(code)
    except Exception as e:
        return {'success': False, 'error': str(e)}

@router.post("/fund/{code}/simulate-dca")
async def simulate_fund_dca(code: str, params: Dict[str, Any]):
    """定投模拟分析"""
    try:
        service = get_investment_service()
        fetcher = get_data_fetcher()
        nav_df = fetcher.get_fund_nav(code)
        return service.simulate_dca(
            nav_df, 
            base_amount=params.get('base_amount', 1000),
            frequency=params.get('frequency', 'weekly'),
            start_date=params.get('start_date')
        )
    except Exception as e:
        return {'success': False, 'error': str(e)}

@router.post("/portfolio/performance")
async def get_portfolio_performance(holdings: List[Dict[str, Any]]):
    """获取持仓组合性能分析"""
    try:
        service = get_portfolio_service()
        return await service.calculate_portfolio_performance(holdings)
    except Exception as e:
        return {'success': False, 'error': str(e)}

@router.get("/recommendations/history")
async def get_recommendation_history(limit: int = 10):
    """获取历史推荐回顾"""
    try:
        service = get_roi_service()
        return await service.get_historical_roi(limit=limit)
    except Exception as e:
        return {'success': False, 'error': str(e)}

@router.get("/market/money-flow")
async def get_market_money_flow():
    """获取市场大额资金流向"""
    try:
        service = get_money_flow_service()
        return service.get_big_money_flows()
    except Exception as e:
        return {'success': False, 'error': str(e)}

@router.get("/fund/{code}/dividends")
async def get_fund_dividends(code: str):
    """获取基金分红信息"""
    try:
        service = get_dividend_service()
        return await service.get_fund_dividends(code)
    except Exception as e:
        return {'success': False, 'error': str(e)}

@router.get("/calendar")
async def get_investment_calendar():
    """获取投资日历"""
    try:
        service = get_calendar_service()
        return await service.get_calendar()
    except Exception as e:
        return {'success': False, 'error': str(e)}

@router.get("/money-flow")
async def get_money_flow():
    """获取大额资金流向"""
    try:
        service = get_money_flow_service()
        return await service.get_money_flow()
    except Exception as e:
        return {'success': False, 'error': str(e)}


@router.get("/watchlist")
async def get_watchlist():
    """
    获取自选基金列表（包含最新指标）
    """
    try:
        db = get_db()
        watchlist = db.get_watchlist()
        
        # 获取最新快照
        snapshot = db.get_latest_snapshot()
        
        # 为每个自选基金获取最新指标
        result = []
        for item in watchlist:
            code = item['fund_code']
            fund_data = {
                'code': code,
                'name': item.get('fund_name', ''),
                'notes': item.get('notes', ''),
                'added_at': item.get('added_at', '')
            }
            
            # 尝试获取快照中的指标
            if snapshot:
                metrics = db.get_fund_metrics(snapshot['id'], code)
                if metrics:
                    fund_data.update({
                        'score': metrics.get('score'),
                        'alpha': metrics.get('alpha'),
                        'sharpe': metrics.get('sharpe'),
                        'return_1m': metrics.get('return_1m'),
                        'return_1y': metrics.get('annual_return')
                    })
            
            result.append(fund_data)
        
        return {
            'success': True,
            'data': result,
            'total': len(result)
        }
    except Exception as e:
        return {
            'success': False,
            'error': str(e),
            'data': []
        }


# ==================== 基金对比接口 ====================

@router.post("/compare")
async def compare_funds(request: CompareRequest):
    """
    多基金对比分析 (POST)
    """
    try:
        db = get_db()
        code_list = [c.strip().zfill(6) for c in request.codes if c.strip()]
        
        if len(code_list) < 2:
            return error_response(error='至少需要2只基金进行对比')
        
        if len(code_list) > 10: # 放宽限制到10只
            return error_response(error='最多支持10只基金对比')
        
        snapshot = db.get_latest_snapshot()
        service = get_snapshot_service()
        
        results = []
        for code in code_list:
            analysis = service.analyze_single_fund(code)
            if analysis.get('status') == 'success':
                results.append(analysis)
        
        return success_response(data=results)
    except Exception as e:
        logger.error(f"Compare failed: {e}")
        return error_response(error=str(e))


# ==================== 每日操作接口 ====================

@router.get("/daily-actions")
async def get_daily_actions(limit: int = 10):
    """获取每日操作清单"""
    try:
        service = get_action_service()
        result = await service.get_daily_actions(limit=limit)
        return success_response(data=result)
    except Exception as e:
        logger.error(f"Daily actions failed: {e}")
        return error_response(error=str(e))


# ==================== 定投计划接口 ====================

@router.get("/dca/plans")
async def get_dca_plans():
    """获取所有定投计划"""
    try:
        db = get_db()
        plans = db.get_dca_plans()
        return success_response(data=plans)
    except Exception as e:
        return error_response(error=str(e))

@router.post("/dca/plans")
async def add_dca_plan(plan: DcaPlanRequest):
    """添加或更新定投计划"""
    try:
        db = get_db()
        success = db.add_dca_plan(
            fund_code=plan.fund_code,
            fund_name=plan.fund_name,
            base_amount=plan.base_amount,
            frequency=plan.frequency,
            day_of_week=plan.day_of_week,
            day_of_month=plan.day_of_month
        )
        if success:
            return success_response(message="计划已保存")
        return error_response(error="保存失败")
    except Exception as e:
        return error_response(error=str(e))


# ==================== 资产持仓接口 ====================

@router.get("/portfolio/holding")
async def get_portfolio_holding():
    """获取当前持仓"""
    try:
        db = get_db()
        holdings = db.get_holding_portfolio()
        return success_response(data=holdings)
    except Exception as e:
        return error_response(error=str(e))

@router.post("/portfolio/buy")
async def buy_fund(
    req: Optional[PortfolioBuyRequest] = None,
    code: Optional[str] = Query(None),
    shares: Optional[float] = Query(None),
    cost_price: Optional[float] = Query(None),
    name: Optional[str] = Query(None)
):
    """买入基金 - 支持 Body 或 Query Params (兼容前端)"""
    try:
        db = get_db()
        # 优先使用 query params (如前端 app.js:865 所示)
        f_code = code or (req.fund_code if req else None)
        f_shares = shares or (req.shares if req else None)
        f_price = cost_price or (req.cost_price if req else 0)
        f_name = name or (req.fund_name if req else "")
        
        if not f_code or f_shares is None:
            return error_response(error="缺少必要参数")
            
        success = db.add_portfolio_position(
            fund_code=f_code,
            fund_name=f_name,
            shares=f_shares,
            cost_price=f_price,
            buy_date=datetime.now().strftime('%Y-%m-%d'),
            notes=""
        )
        if success:
            return success_response(message="买入记录已保存")
        return error_response(error="保存失败")
    except Exception as e:
        return error_response(error=str(e))

@router.post("/portfolio/sell")
async def sell_fund(
    req: Optional[PortfolioSellRequest] = None,
    position_id: Optional[int] = Query(None),
    sell_price: Optional[float] = Query(None)
):
    """卖出基金 - 支持 Body 或 Query Params"""
    try:
        db = get_db()
        p_id = position_id or (req.position_id if req else None)
        s_price = sell_price or (req.sell_price if req else 0)
        
        if p_id is None:
            return error_response(error="缺少持仓ID")
            
        success = db.sell_portfolio_position(
            position_id=p_id,
            sell_price=s_price,
            sell_date=datetime.now().strftime('%Y-%m-%d')
        )
        if success:
            return success_response(message="卖出记录已保存")
        return error_response(error="保存失败")
    except Exception as e:
        return error_response(error=str(e))

@router.post("/portfolio/build")
async def build_portfolio_plan(req: PortfolioBuildRequest):
    """一键生成组合方案"""
    try:
        builder = get_portfolio_builder()
        result = builder.build_portfolio(amount=req.amount, risk_level=req.risk_level)
        return success_response(data=result)
    except Exception as e:
        return error_response(error=str(e))


# ==================== 消息通知接口 ====================

@router.get("/notifications")
async def get_notifications():
    """获取未读通知"""
    try:
        db = get_db()
        notifs = db.get_unread_notifications()
        return success_response(data=notifs)
    except Exception as e:
        return error_response(error=str(e))

@router.post("/notifications/{id}/read")
async def mark_notification_read(id: int):
    """标记通知为已读"""
    try:
        db = get_db()
        db.mark_notification_read(id)
        return success_response(message="已标记为已读")
    except Exception as e:
        return error_response(error=str(e))


# ==================== 市场与排行榜 ====================

@router.get("/watchlist/realtime")
async def get_watchlist_realtime():
    """获取带实时估值的自选列表"""
    try:
        db = get_db()
        watchlist = db.get_watchlist()
        if not watchlist:
            return success_response(data=[])
            
        codes = [item['fund_code'] for item in watchlist]
        fetcher = get_data_fetcher()
        valuations = fetcher.get_realtime_valuation_batch(codes)
        
        results = []
        for item in watchlist:
            code = item['fund_code']
            val = valuations.get(code, {})
            results.append({
                **item,
                'latest_nav': val.get('nav'),
                'estimation_nav': val.get('estimation_nav'),
                'estimation_growth': val.get('estimation_growth'),
                'update_time': val.get('time')
            })
        return success_response(data=results)
    except Exception as e:
        return error_response(error=str(e))

@router.get("/market/hotspots")
async def get_market_hotspots():
    """获取市场热点聚合"""
    try:
        service = get_news_service()
        hotspots = await service.get_market_hotspots()
        return success_response(data=hotspots)
    except Exception as e:
        # Fallback
        return success_response(data=[{"title": "智算中心建设加速", "score": 95}, {"title": "红利低波持续走强", "score": 88}])

@router.get("/sectors/hot")
async def get_hot_sectors():
    """热门板块"""
    try:
        db = get_db()
        themes = db.get_all_themes()
        return success_response(data=themes[:10])
    except Exception as e:
        return error_response(error=str(e))

@router.get("/rankings")
async def get_rankings(sort_by: str = 'score', limit: int = 50):
    """多维排行"""
    try:
        db = get_db()
        snapshot = db.get_latest_snapshot()
        if not snapshot:
            return error_response(error="暂无数据")
        rankings = db.get_ranking(snapshot_id=snapshot['id'], sort_by=sort_by, limit=limit)
        return success_response(data=rankings)
    except Exception as e:
        return error_response(error=str(e))


# ==================== 管理员与其它 ====================

@router.post("/admin/build-static")
async def admin_build_static():
    """管理员：重新构建全量数据快照"""
    try:
        service = get_snapshot_service()
        # 异步启动，不阻断请求
        import threading
        thread = threading.Thread(target=service.create_full_snapshot)
        thread.start()
        return success_response(message="后台更新任务已启动")
    except Exception as e:
        return error_response(error=str(e))

@router.post("/diagnose/pro")
async def diagnose_pro(req: PortfolioDiagnoseRequest):
    """Pro 穿透式诊断"""
    try:
        ai_service = get_ai_service()
        if not ai_service:
            return error_response(error="AI 服务不可用")
        report = await ai_service.generate_portfolio_diagnosis(req.funds)
        return success_response(data={"report": report})
    except Exception as e:
        return error_response(error=str(e))



# ==================== 净值历史接口 ====================

@router.get("/fund/{code}/nav-history")
async def get_nav_history(
    code: str,
    days: int = Query(60, ge=7, le=365, description="获取天数")
):
    """
    获取基金净值历史（用于走势图）
    """
    try:
        db = get_db()
        code = code.strip().zfill(6)
        
        # 先检查本地缓存
        cached = db.get_nav_history(code, days)
        
        # 如果缓存数据足够，直接返回
        if len(cached) >= days * 0.8:  # 80%的数据就认为足够
            return {
                'success': True,
                'data': {
                    'code': code,
                    'nav_history': list(reversed(cached)),  # 按日期正序
                    'source': 'cache'
                }
            }
        
        # 否则在线获取
        try:
            try:
                from ..services.data_fetcher import get_data_fetcher
            except (ImportError, ValueError):
                from services.data_fetcher import get_data_fetcher
            fetcher = get_data_fetcher()
            nav_df = fetcher.get_fund_nav(code)
            
            if nav_df is not None and not nav_df.empty:
                # 保存到缓存
                nav_data = []
                for _, row in nav_df.iterrows():
                    nav_data.append({
                        'date': row['date'].strftime('%Y-%m-%d') if hasattr(row['date'], 'strftime') else str(row['date']),
                        'nav': float(row['nav']) if row['nav'] else None,
                        'acc_nav': float(row.get('acc_nav', row['nav'])) if row.get('acc_nav') else None
                    })
                
                db.save_nav_history(code, nav_data)
                
                # 返回最近N天
                recent = nav_data[-days:] if len(nav_data) > days else nav_data
                
                return {
                    'success': True,
                    'data': {
                        'code': code,
                        'nav_history': recent,
                        'source': 'online'
                    }
                }
        except Exception as fetch_err:
            logger.warning(f"在线获取净值历史失败: {fetch_err}")
        
        # 如果都失败，返回缓存的数据（即使不完整）
        return {
            'success': True,
            'data': {
                'code': code,
                'nav_history': list(reversed(cached)) if cached else [],
                'source': 'cache_partial'
            }
        }
    except Exception as e:
        return {
            'success': False,
            'error': str(e),
            'data': {}
        }


@router.get("/fund/{code}/in-watchlist")
async def check_in_watchlist(code: str):
    """
    检查基金是否在自选中
    """
    try:
        db = get_db()
        code = code.strip().zfill(6)
        in_watchlist = db.is_in_watchlist(code)
        
        return {
            'success': True,
            'data': {
                'code': code,
                'in_watchlist': in_watchlist
            }
        }
    except Exception as e:
        return {
            'success': False,
            'error': str(e)
        }


# ==================== 涨幅榜接口 ====================

@router.get("/top-gainers")
async def get_top_gainers(
    period: str = Query('1w', description="涨幅周期: yesterday/today_estimate/1w/1m/3m/6m/1y"),
    limit: int = Query(20, ge=5, le=50, description="返回数量")
):
    """
    获取涨幅榜
    
    按指定周期的涨幅排序返回基金列表
    - yesterday: 昨日涨幅（实时联网获取最新净值涨跌幅）
    - today_estimate: 今日估算（基于指数基金跟踪指数实时行情）
    - 1w/1m/3m/6m/1y: 历史周期涨幅（从快照缓存获取）
    """
    try:
        db = get_db()
        
        # 昨日涨幅 - 全市场实时排行榜 (Existing code logic)
        if period == 'yesterday':
            from ..services.data_fetcher import get_data_fetcher
            fetcher = get_data_fetcher()
            
            # 使用全市场涨幅排行榜
            gains_data = fetcher.get_market_top_gainers(
                period='day',
                fund_type='全部',
                limit=limit
            )
            
            if not gains_data:
                return {
                    'success': False,
                    'error': '获取全市场涨幅榜失败，请稍后重试'
                }
            
            return {
                'success': True,
                'data': {
                    'period': 'yesterday',
                    'period_label': '昨日涨幅(全市场)',
                    'realtime': True,
                    'note': '数据来源：东方财富全市场基金排行',
                    'count': len(gains_data),
                    'funds': gains_data
                }
            }
        
        # 今日估算 - 使用全市场指数基金排行
        elif period == 'today_estimate':
            from ..services.data_fetcher import get_data_fetcher
            fetcher = get_data_fetcher()
            
            # 获取指数型基金的当日涨幅排行
            gains_data = fetcher.get_market_top_gainers(
                period='day',
                fund_type='指数型',
                limit=limit
            )
            
            # 同时获取主要指数实时行情作为参考
            index_quotes = {}
            main_indices = ['000300', '000905', '399006', '000016']
            for idx in main_indices:
                quote = fetcher.get_realtime_index_quote(idx)
                if quote:
                    index_quotes[idx] = quote
            
            if not gains_data:
                return {
                    'success': False,
                    'error': '获取指数基金涨幅榜失败，请稍后重试'
                }
            
            return {
                'success': True,
                'data': {
                    'period': 'today_estimate',
                    'period_label': '今日估算(指数基金)',
                    'realtime': True,
                    'note': '数据来源：东方财富指数型基金排行',
                    'index_quotes': [{'symbol': k, **v} for k, v in index_quotes.items()] if index_quotes else [],
                    'count': len(gains_data),
                    'funds': gains_data
                }
            }
        
        # 历史周期涨幅 - 全市场实时获取
        else:
            from ..services.data_fetcher import get_data_fetcher
            fetcher = get_data_fetcher()
            
            # 映射周期参数
            period_mapping = {
                '1w': ('week', '近1周'),
                '1m': ('month', '近1月'),
                '3m': ('3month', '近3月'),
                '6m': ('6month', '近6月'),
                '1y': ('1year', '近1年')
            }
            
            api_period, period_label = period_mapping.get(period, ('week', '近1周'))
            
            # 使用全市场涨幅排行榜
            gains_data = fetcher.get_market_top_gainers(
                period=api_period,
                fund_type='全部',
                limit=limit
            )
            
            if not gains_data:
                # 如果全市场API失败，回退到数据库
                snapshot = db.get_latest_snapshot()
                if snapshot:
                    db_funds = db.get_top_gainers(snapshot['id'], period=period, limit=limit)
                    period_field = {
                        '1w': 'return_1w', '1m': 'return_1m', '3m': 'return_3m',
                        '6m': 'return_6m', '1y': 'return_1y'
                    }.get(period, 'return_1w')
                    
                    return {
                        'success': True,
                        'data': {
                            'period': period,
                            'period_label': period_label + '(缓存)',
                            'snapshot_date': snapshot['snapshot_date'],
                            'count': len(db_funds),
                            'funds': [{
                                'code': f['code'],
                                'name': f.get('name', ''),
                                'gain': f.get(period_field, 0),
                                'score': f.get('score', 0),
                                'themes': f.get('themes', [])
                            } for f in db_funds]
                        }
                    }
                else:
                    return {
                        'success': False,
                        'error': '获取涨幅榜失败，请稍后重试'
                    }
            
            return {
                'success': True,
                'data': {
                    'period': period,
                    'period_label': period_label + '(全市场)',
                    'realtime': True,
                    'note': '数据来源：东方财富全市场基金排行',
                    'count': len(gains_data),
                    'funds': gains_data
                }
            }
    except Exception as e:
        logger.error(f"获取涨幅榜失败: {e}")
        return {
            'success': False,
            'error': str(e)
        }


# ==================== 持仓模拟接口 ====================

@router.get("/portfolio/performance")
@router.get("/portfolio")
async def get_portfolio():
    """
    获取持仓列表 (兼容 /portfolio 和 /portfolio/performance)
    """
    try:
        db = get_db()
        positions = db.get_portfolio(status='holding')
        summary = db.get_portfolio_summary()
        
        # 获取每个持仓的当前净值
        enriched_positions = []
        total_value = 0
        total_profit = 0
        
        for pos in positions:
            current_nav = None
            profit = 0
            profit_rate = 0
            
            # 尝试获取当前净值
            nav_history = db.get_nav_history(pos['fund_code'], days=1)
            if nav_history:
                current_nav = nav_history[0].get('nav')
            
            if current_nav and pos.get('cost_price'):
                value = pos['shares'] * current_nav
                cost = pos['shares'] * pos['cost_price']
                profit = value - cost
                profit_rate = (current_nav / pos['cost_price'] - 1) * 100
                total_value += value
                total_profit += profit
            
            enriched_positions.append({
                **pos,
                'current_nav': current_nav,
                'current_value': round(pos['shares'] * current_nav, 2) if current_nav else None,
                'profit': round(profit, 2),
                'profit_rate': round(profit_rate, 2)
            })
        
        return {
            'success': True,
            'items': enriched_positions, # 兼容前端 app.js:847 的 items 字段
            'data': enriched_positions,
            'summary': {
                'total_positions': summary['total_positions'],
                'total_cost': round(summary['total_cost'], 2),
                'total_value': round(total_value, 2),
                'total_profit': round(total_profit, 2),
                'total_profit_rate': round(total_profit / summary['total_cost'] * 100, 2) if summary['total_cost'] > 0 else 0
            }
        }
    except Exception as e:
        logger.error(f"获取持仓失败: {e}")
        return {
            'success': False,
            'error': str(e)
        }
@router.get("/fund/compare")
async def compare_funds(codes: str = Query(..., description="基金代码，多个用逗号分隔")):
    """
    基金PK对比 - 获取多个基金的详细指标对比 (带缓存)
    """
    try:
        code_list = [c.strip().zfill(6) for c in codes.split(',') if c.strip()]
        if not code_list:
            return {'success': False, 'error': '请提供有效的基金代码'}
        
        # 1. 检查缓存
        from .utils.cache import get_cache_manager
        cache = get_cache_manager()
        cache_key = f"compare:{','.join(sorted(code_list))}"
        cached = cache.get(cache_key)
        if cached:
            return cached

        snapshot_service = get_snapshot_service()
        results = []
        
        for code in code_list:
            analysis = snapshot_service.analyze_single_fund(code)
            if analysis.get('success'):
                # 提取核心数据
                metrics = analysis.get('metrics', {})
                results.append({
                    'code': code,
                    'name': metrics.get('name', '未知'),
                    'category': metrics.get('category', '混合型'),
                    'themes': metrics.get('themes', []),
                    'score': metrics.get('score', 0),
                    'alpha': metrics.get('alpha', 0),
                    'beta': metrics.get('beta', 0),
                    'sharpe': metrics.get('sharpe', 0),
                    'max_drawdown': metrics.get('max_drawdown', 0),
                    'annual_return': metrics.get('annual_return', 0),
                    'volatility': metrics.get('volatility', 0),
                    'return_1w': metrics.get('return_1w', 0),
                    'return_1m': metrics.get('return_1m', 0),
                    'return_1y': metrics.get('return_1y', 0),
                    'nav': metrics.get('nav', 0),
                    'nav_date': metrics.get('nav_date', ''),
                    'chart_data': analysis.get('chart_data', [])
                })
        
        return {
            'success': True,
            'data': results,
            'count': len(results)
        }
    except Exception as e:
        logger.error(f"基金对比失败: {e}")
        return {
            'success': False,
            'error': str(e)
        }


@router.get("/portfolio/diagnose")
async def diagnose_portfolio(user_id: str = 'default'):
    """
    持仓诊断 - AI分析风险与机会
    """
    try:
        db = get_db()
        portfolio = db.get_portfolio(user_id=user_id, status='holding')
        
        if not portfolio:
            return {
                'success': False,
                'error': '暂无持仓内容，请先买入一些基金再进行诊断。'
            }
        
        # 聚合数据
        stats = {
            'position_count': len(portfolio),
            'total_cost': sum(p.get('shares', 0) * p.get('cost_price', 0) for p in portfolio),
            'total_value': 0,
            'category_distribution': {},
            'theme_distribution': {}
        }
        
        snapshot_service = get_snapshot_service()
        
        # 获取全组合重仓股分布 (穿透分析)
        stock_exposure = {}
        fetcher = get_data_fetcher()
        
        total_value = 0
        enriched_portfolio = []
        for p in portfolio:
            code = p.get('fund_code')
            analysis = snapshot_service.analyze_single_fund(code)
            if analysis.get('success'):
                metrics = analysis.get('metrics', {})
                current_nav = metrics.get('nav', p.get('cost_price'))
                p_value = p.get('shares', 0) * current_nav
                total_value += p_value
                
                # 获取该基金的重仓股
                holdings = fetcher.get_fund_holdings(code)
                for h in holdings:
                    s_name = h.get('name')
                    s_ratio = h.get('ratio', 0)
                    # 计算该股票在全组合中的权重 = 该股在基金中的占比 * 该基金在全组合中的占比
                    # 简化计算：存储绝对权重，最后除以全组合市值
                    # 但其实直接按百分比加权更直观
                    if s_name:
                        # 权重增加：基金占比 * 股票在基金中的占比
                        weight_contribution = (p_value / total_value if total_value > 0 else 0) * s_ratio
                        stock_exposure[s_name] = stock_exposure.get(s_name, 0) + weight_contribution

                # 更新持仓信息用于 AI 诊断
                p['current_price'] = current_nav
                p['market_value'] = p_value
                p['profit'] = p_value - (p.get('shares', 0) * p.get('cost_price', 0))
                p['holdings'] = holdings # 加入重仓股明细
                
                # 分类分布
                cat = metrics.get('category', '其他')
                stats['category_distribution'][cat] = stats['category_distribution'].get(cat, 0) + p_value
                
                # 主题分布
                themes = metrics.get('themes', ['综合'])
                if isinstance(themes, list):
                    weight = p_value / len(themes)
                    for t in themes:
                        stats['theme_distribution'][t] = stats['theme_distribution'].get(t, 0) + weight
                else:
                    stats['theme_distribution'][themes] = stats['theme_distribution'].get(themes, 0) + p_value
            enriched_portfolio.append(p)

        stats['total_value'] = total_value
        stats['total_profit'] = total_value - stats['total_cost']
        stats['profit_pct'] = (stats['total_profit'] / stats['total_cost'] * 100) if stats['total_cost'] > 0 else 0
        
        # 转换为百分比并排序
        category_pct = {}
        if total_value > 0:
            for k, v in stats['category_distribution'].items():
                category_pct[k] = (v / total_value * 100)
            
            theme_pct = {}
            for k, v in stats['theme_distribution'].items():
                theme_pct[k] = (v / total_value * 100)
            
            # 重新计算股票暴露权重 (因为循环中 total_value 是动态增加的，这里做修正)
            # 正确修正逻辑：
            rebase_stock_exposure = {}
            for p in enriched_portfolio:
                p_weight = p.get('market_value', 0) / total_value if total_value > 0 else 0
                for h in p.get('holdings', []):
                    s_name = h.get('name')
                    s_ratio = h.get('ratio', 0)
                    rebase_stock_exposure[s_name] = rebase_stock_exposure.get(s_name, 0) + (p_weight * s_ratio)
            
            stats['category_distribution'] = category_pct
            stats['theme_distribution'] = dict(sorted(theme_pct.items(), key=lambda x: x[1], reverse=True)[:8])
            stats['stock_exposure'] = dict(sorted(rebase_stock_exposure.items(), key=lambda x: x[1], reverse=True)[:10])
        
        # 调用 AI 诊断
        ai_service = get_ai_service()
        diagnosis_content = 'AI服务未配置，仅提供量化数据。'
        if ai_service:
            diagnosis = await ai_service.generate_portfolio_diagnosis(enriched_portfolio, stats)
            if diagnosis.get('success'):
                diagnosis_content = diagnosis.get('content')
            else:
                diagnosis_content = diagnosis.get('error', 'AI诊断发生错误')
            
        return {
            'success': True,
            'data': {
                'stats': stats,
                'diagnosis': diagnosis_content,
                'updated_at': datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            }
        }
    except Exception as e:
        logger.error(f"持仓诊断失败: {e}")
        return {
            'success': False,
            'error': str(e)
        }



@router.post("/portfolio/buy")
async def buy_fund(
    code: str = Query(..., description="基金代码"),
    shares: float = Query(..., gt=0, description="买入份额"),
    notes: str = Query(None, description="备注")
):
    """
    模拟买入基金
    """
    try:
        db = get_db()
        service = get_snapshot_service()
        code = code.strip().zfill(6)
        
        # 获取当前净值作为成本价
        nav_history = db.get_nav_history(code, days=1)
        if nav_history:
            cost_price = nav_history[0].get('nav')
        else:
            # 尝试在线获取
            result = service.analyze_single_fund(code)
            if result.get('status') == 'success':
                cost_price = result['metrics'].get('latest_nav')
            else:
                return {
                    'success': False,
                    'error': f'无法获取基金 {code} 的当前净值'
                }
        
        if not cost_price:
            return {
                'success': False,
                'error': '无法获取当前净值'
            }
        
        # 获取基金名称
        fund_info = db.get_fund(code)
        fund_name = fund_info.get('name', '') if fund_info else f'基金{code}'
        
        buy_date = datetime.datetime.now().strftime('%Y-%m-%d')
        
        success = db.add_portfolio_position(
            fund_code=code,
            fund_name=fund_name,
            shares=shares,
            cost_price=cost_price,
            buy_date=buy_date,
            notes=notes
        )
        
        if success:
            return {
                'success': True,
                'data': {
                    'code': code,
                    'name': fund_name,
                    'shares': shares,
                    'cost_price': cost_price,
                    'buy_date': buy_date,
                    'total_cost': round(shares * cost_price, 2)
                }
            }
        else:
            return {
                'success': False,
                'error': '添加持仓失败'
            }
    except Exception as e:
        logger.error(f"买入失败: {e}")
        return {
            'success': False,
            'error': str(e)
        }


@router.post("/portfolio/sell")
async def sell_fund(
    position_id: int = Query(..., description="持仓ID"),
):
    """
    模拟卖出基金
    """
    try:
        db = get_db()
        
        sell_date = datetime.datetime.now().strftime('%Y-%m-%d')
        
        # 获取持仓信息以获取当前净值
        positions = db.get_portfolio()
        position = next((p for p in positions if p['id'] == position_id), None)
        
        if not position:
            return {
                'success': False,
                'error': '持仓不存在'
            }
        
        # 获取当前净值
        nav_history = db.get_nav_history(position['fund_code'], days=1)
        sell_price = nav_history[0].get('nav') if nav_history else position['cost_price']
        
        success = db.sell_portfolio_position(
            position_id=position_id,
            sell_price=sell_price,
            sell_date=sell_date
        )
        
        if success:
            profit = (sell_price - position['cost_price']) * position['shares']
            profit_rate = (sell_price / position['cost_price'] - 1) * 100
            
            return {
                'success': True,
                'data': {
                    'position_id': position_id,
                    'code': position['fund_code'],
                    'sell_price': sell_price,
                    'profit': round(profit, 2),
                    'profit_rate': round(profit_rate, 2)
                }
            }
        else:
            return {
                'success': False,
                'error': '卖出失败'
            }
    except Exception as e:
        logger.error(f"卖出失败: {e}")
        return {
            'success': False,
            'error': str(e)
        }


@router.get("/portfolio/performance")
async def get_portfolio_performance():
    """获取所有持仓的实时表现汇总"""
    try:
        db = get_db()
        positions = db.get_portfolio()
        if not positions:
            return {"success": True, "summary": {"total_value": 0, "total_profit": 0}, "items": []}
            
        # 兼容处理 database 返回的明细转换给 PortfolioService
        holdings = []
        for p in positions:
            holdings.append({
                "code": p['fund_code'],
                "name": p['fund_name'],
                "shares": p['shares'],
                "cost": p['cost_price']
            })
            
        from ..services.portfolio_service import get_portfolio_service
        service = get_portfolio_service()
        return await service.calculate_portfolio_performance(holdings)
    except Exception as e:
        logger.error(f"Portfolio performance failed: {e}")
        return {"success": False, "error": str(e)}


# ==================== 推荐历史回溯接口 ====================

@router.get("/recommendation-history")
async def get_recommendation_history(
    days: int = Query(30, ge=7, le=90, description="查询天数"),
):
    """
    获取历史推荐回溯 (Phase 7 统一结构)
    """
    try:
        from ..services.roi_review_service import get_roi_service
        service = get_roi_service()
        # 将天数近似转换为快照数量 (假设每日一快照)
        result = await service.get_historical_roi(limit=days)
        return result
    except Exception as e:
        logger.error(f"获取推荐历史失败: {e}")
        return {
            'success': False,
            'error': str(e)
        }


# ==================== 新闻与预测API ====================

@router.post("/v1/compare")
async def fund_comparison(request: CompareRequest):
    """
    多基金对比矩阵
    """
    try:
        ss = get_snapshot_service()
        result = ss.get_comparison_matrix(request.codes)
        return result
    except Exception as e:
        logger.error(f"基金对比失败: {e}")
        return {'status': 'error', 'message': str(e)}

@router.post("/v1/ai/chat/query")
async def ai_chat_selection(request: AIChatQueryRequest):
    """
    对话式选基核心接口 (Phase 4)
    """
    try:
        ai = get_ai_service()
        ss = get_snapshot_service()
        
        # 1. 语义解析
        extraction = await ai.translate_semantic_query(request.query)
        interpretation = extraction.get('interpretation', f"正在为您搜索 {request.query} 相关基金...")
        
        # 2. 执行高级筛选
        filters = {}
        if 'themes' in extraction: filters['themes'] = extraction['themes']
        if 'risk_level' in extraction: filters['risk_level'] = extraction['risk_level']
        
        # 指标匹配逻辑
        for key in ['return_1y', 'max_drawdown_1y', 'sharpe_1y']:
            if key in extraction:
                op_data = extraction[key]
                if isinstance(op_data, dict):
                    val = op_data.get('val')
                    db_key = key.replace('_1y', '')
                    if db_key == 'return': db_key = 'return_1y'
                    
                    if op_data.get('op') == '>':
                        filters[f'min_{db_key}'] = val
                    elif op_data.get('op') == '<':
                        filters[f'max_{db_key}'] = val
        
        # 3. 运行筛选
        results = ss.query_funds_advanced(filters, limit=6)
        
        return {
            'status': 'success',
            'interpretation': interpretation,
            'filters_extracted': filters,
            'funds': results.get('data', []),
            'count': results.get('count', 0)
        }
    except Exception as e:
        logger.error(f"AI Chat query failed: {e}")
        return {'status': 'error', 'message': str(e)}

@router.post("/v1/diagnose/pro")
async def portfolio_diagnose_pro(request: PortfolioDiagnoseRequest):
    """
    专业投资组合诊断
    - 资产配置分析 (权益/固收/现金)
    - 场景压力测试
    """
    try:
        portfolio = request.funds
        if not portfolio:
            return {'status': 'error', 'message': '组合为空'}
            
        db = get_db()
        allocation = {'equity': 0, 'bond': 0, 'cash': 0}
        total_weight = sum(p.get('weight', 0) for p in portfolio)
        
        # 1. 资产配置估算 (基于基金类型)
        for p in portfolio:
            fund = db.get_fund(p['code'])
            weight = p.get('weight', 0) / total_weight if total_weight > 0 else 0
            
            ftype = fund.get('fund_type', '') if fund else ''
            if '股票' in ftype or '混合' in ftype:
                allocation['equity'] += weight * 85  # 简化的平均仓位
                allocation['cash'] += weight * 15
            elif '债券' in ftype:
                allocation['bond'] += weight * 90
                allocation['cash'] += weight * 10
            else:
                allocation['cash'] += weight * 100
                
        # 2. 压力测试场景 (模拟)
        scenarios = [
            {'name': '2008年式金融危机 (-20%)', 'impact': allocation['equity'] * -0.2 + allocation['bond'] * 0.05},
            {'name': '流动性宽松牛市 (+15%)', 'impact': allocation['equity'] * 0.15 + allocation['bond'] * 0.02},
            {'name': '利率大幅上行 (-5%)', 'impact': allocation['equity'] * -0.05 + allocation['bond'] * -0.08},
        ]
        
        return {
            'status': 'success',
            'data': {
                'allocation': allocation,
                'scenarios': scenarios,
                'advice': "当前组合配置较为" + ("平衡" if allocation['equity'] < 60 else "激进")
            }
        }
    except Exception as e:
        logger.error(f"专业诊断失败: {e}")
        return {'status': 'error', 'message': str(e)}
@router.get("/news")
async def get_news(limit: int = 30):
    """获取财经新闻 (实时聚合)"""
    try:
        from ..services.news_service import get_news_service
        news_service = get_news_service()
        
        news = await news_service.get_market_news(limit=limit)
        
        return {
            'success': True,
            'data': {
                'count': len(news),
                'news': news
            }
        }
    except Exception as e:
        logger.error(f"获取新闻失败: {e}")
        return {
            'success': False,
            'error': str(e)
        }


@router.get("/news/sentiment")
async def get_news_sentiment():
    """获取实时新闻情绪分析"""
    try:
        from ..services.news_service import get_news_service
        news_service = get_news_service()
        
        summary = await news_service.analyze_market_sentiment()
        
        return {
            'success': True,
            'data': summary
        }
    except Exception as e:
        logger.error(f"获取情绪分析失败: {e}")
        return {
            'success': False,
            'error': str(e)
        }


@router.get("/prediction/fund/{code}")
async def predict_fund_trend(code: str):
    """预测基金趋势"""
    try:
        try:
            from ..services.prediction_service import get_trend_predictor
            from ..services.news_service import get_news_service
        except (ImportError, ValueError):
            from services.prediction_service import get_trend_predictor
            from services.news_service import get_news_service
        
        db = get_db()
        predictor = get_trend_predictor()
        news_service = get_news_service()
        
        # 获取历史净值数据
        nav_history = db.get_nav_history(code, days=90)
        
        # 如果数据不足（少于20个交易日），尝试在线获取
        if not nav_history or len(nav_history) < 20:
            logger.info(f"本地数据不足 ({len(nav_history)}), 尝试在线获取 {code}...")
            try:
                try:
                    from ..services.data_fetcher import get_data_fetcher
                except (ImportError, ValueError):
                    from services.data_fetcher import get_data_fetcher
                
                fetcher = get_data_fetcher()
                nav_df = fetcher.get_fund_nav(code)
                
                if nav_df is not None and not nav_df.empty:
                    # 保存到缓存
                    nav_data = []
                    for _, row in nav_df.iterrows():
                        nav_data.append({
                            'date': row['date'].strftime('%Y-%m-%d') if hasattr(row['date'], 'strftime') else str(row['date']),
                            'nav': float(row['nav']) if row['nav'] else None,
                            'acc_nav': float(row.get('acc_nav', row['nav'])) if row.get('acc_nav') else None
                        })
                    
                    db.save_nav_history(code, nav_data)
                    
                    # 重新获取
                    nav_history = db.get_nav_history(code, days=90)
            except Exception as e:
                logger.error(f"在线补充数据失败: {e}")

        if not nav_history:
            return {
                'success': False,
                'error': '无法获取历史净值数据(本地不足且在线获取失败)'
            }
        
        # 转换为DataFrame
        import pandas as pd
        df = pd.DataFrame(nav_history)
        df['nav'] = pd.to_numeric(df['nav'], errors='coerce')
        df = df.dropna(subset=['nav'])
        
        # 获取新闻情绪
        news_sentiment = news_service.get_market_sentiment_summary()
        
        # 预测
        prediction = predictor.predict_trend(df, news_sentiment)
        
        # 获取基金基本信息
        fund_info = db.get_fund(code)
        
        return {
            'success': True,
            'data': {
                'code': code,
                'name': fund_info.get('name', '') if fund_info else '',
                'prediction': prediction
            }
        }
    except Exception as e:
        logger.error(f"预测基金趋势失败: {e}")
        return {
            'success': False,
                'error': str(e)
            }


@router.get("/market/sector-flow")
async def get_sector_flow():
    """获取板块资金流向"""
    try:
        import akshare as ak
        
        # 获取板块资金流
        df = ak.stock_sector_fund_flow_rank(indicator="今日")
        
        if df is None or len(df) == 0:
            return {
                'success': False,
                'error': '无法获取板块资金流向数据'
            }
        
        sectors = []
        for _, row in df.head(20).iterrows():
            sectors.append({
                'name': str(row.get('名称', '')),
                'change_pct': float(row.get('涨跌幅', 0)) if row.get('涨跌幅') else 0,
                'main_net_inflow': float(row.get('主力净流入-净额', 0)) if row.get('主力净流入-净额') else 0,
                'main_net_inflow_pct': float(row.get('主力净流入-净占比', 0)) if row.get('主力净流入-净占比') else 0,
            })
        
        return {
            'success': True,
            'data': {
                'count': len(sectors),
                'sectors': sectors,
                'updated_at': datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            }
        }
    except Exception as e:
        logger.error(f"获取板块资金流向失败: {e}")
        return {
            'success': False,
            'error': str(e)
        }


@router.get("/market/overview")
async def get_market_overview():
    """获取市场概览（综合情绪+主要指数）"""
    try:
        try:
            from ..services.news_service import get_news_service
            from ..services.data_fetcher import get_data_fetcher
        except (ImportError, ValueError):
            from services.news_service import get_news_service
            from services.data_fetcher import get_data_fetcher
        
        news_service = get_news_service()
        fetcher = get_data_fetcher()
        
        # 获取情绪概览
        sentiment = await news_service.analyze_market_sentiment()
        
        # 获取主要指数
        indices = []
        main_indices = [
            ('000001', '上证指数'),
            ('399001', '深证成指'),
            ('399006', '创业板指'),
            ('000300', '沪深300'),
            ('000016', '上证50'),
        ]
        
        for symbol, name in main_indices:
            quote = fetcher.get_realtime_index_quote(symbol)
            if quote:
                indices.append({
                    'symbol': symbol,
                    'name': name,
                    **quote
                })
        
        # 获取全市场涨跌家数
        breadth = fetcher.get_market_breadth()
        
        # 为热门板块获取领涨基金
        enriched_hot_sectors = []
        if sentiment and 'hot_sectors' in sentiment:
            for sector_info in sentiment['hot_sectors']:
                sector_name = sector_info['name']
                # 获取该板块的推荐/领涨基金（取前1个）
                snapshot_service = get_snapshot_service()
                recommends = snapshot_service.get_recommendations(theme=sector_name)
                top_fund = None
                if recommends and recommends.get('success') and recommends.get('results'):
                    top_fund = recommends['results'][0]
                
                enriched_hot_sectors.append({
                    **sector_info,
                    'top_fund': top_fund
                })
            sentiment['hot_sectors'] = enriched_hot_sectors

        return {
            'success': True,
            'debug_version': 'v1.0.4_breadth_leaders',
            'data': {
                'sentiment': sentiment,
                'indices': indices,
                'breadth': breadth,
                'updated_at': datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            }
        }
    except Exception as e:
        logger.error(f"获取市场概览失败: {e}")
        return {
            'success': False,
            'error': str(e)
        }


@router.get("/ai/deep-analysis")
async def deep_analysis(query: str = Query(..., description="深度分析问题")):
    """
    研报级 RAG 深度分析
    """
    try:
        ai_service = get_ai_service()
        result = await ai_service.generate_deep_analysis(query)
        return result
    except Exception as e:
        return {'success': False, 'error': str(e)}


@router.post("/ai/kb-update")
async def update_kb(token: str = Query(..., description="管理员令牌"), keyword: str = "基金市场"):
    """
    更新研报知识库
    """
    try:
        from .admin import ADMIN_TOKEN
    except ImportError:
        try:
            from api.admin import ADMIN_TOKEN
        except ImportError:
            import os
            ADMIN_TOKEN = os.environ.get("ADMIN_TOKEN", "AstliRGitFrJtABmjCMmxBKVP5YA0XuZ2OBfP28XQqPM44ZWhKAQIdsVWzBd4peO")

    if token != ADMIN_TOKEN:
        return {'success': False, 'error': '鉴权非法'}
        
    try:
        vector_service = get_vector_service()
        new_count = await vector_service.update_knowledge_base(keyword)
        return {'success': True, 'new_count': new_count}
    except Exception as e:
        return {'success': False, 'error': str(e)}


# ==================== 业绩走势图接口 ====================

@router.get("/fund/{code}/performance-chart")
async def get_fund_performance_chart(
    code: str,
    period: str = Query('1y', description="周期: 1m/3m/6m/1y/3y"),
    benchmark: str = Query('000300', description="基准指数代码")
):
    """
    获取基金业绩走势图数据 (基金 vs 同类平均 vs 基准指数)
    
    参考天天基金APP的业绩走势图功能
    """
    try:
        db = get_db()
        fetcher = get_data_fetcher()
        
        # 解析周期
        period_days = {'1m': 30, '3m': 90, '6m': 180, '1y': 365, '3y': 1095}.get(period, 365)
        
        # 1. 获取基金净值历史
        fund = db.get_fund(code)
        if not fund:
            return {'success': False, 'error': f'未找到基金 {code}'}
        
        nav_history = db.get_nav_history(code, days=period_days)
        if not nav_history or len(nav_history) < 5:
            return {'success': False, 'error': '净值数据不足'}
        
        # 2. 获取基准指数数据
        import pandas as pd
        start_date = (datetime.datetime.now() - datetime.timedelta(days=period_days)).strftime('%Y%m%d')
        benchmark_df = fetcher.get_benchmark_data(benchmark, start_date)
        
        # 3. 计算累计收益率序列
        fund_dates = [h['date'] for h in nav_history]
        fund_navs = [h['nav'] for h in nav_history]
        first_nav = fund_navs[0]
        fund_returns = [(nav / first_nav - 1) * 100 for nav in fund_navs]
        
        # 基准收益率
        benchmark_returns = []
        if benchmark_df is not None and len(benchmark_df) > 0:
            first_close = benchmark_df['close'].iloc[0]
            for _, row in benchmark_df.iterrows():
                benchmark_returns.append({
                    'date': row['date'].strftime('%Y-%m-%d'),
                    'return': round((row['close'] / first_close - 1) * 100, 2)
                })
        
        # 4. 获取同类平均（简化实现：使用该基金主题下其他基金的平均值）
        # 这里返回空数组，后续可扩展
        category_avg = []
        
        return {
            'success': True,
            'data': {
                'fund_code': code,
                'fund_name': fund.get('name', code),
                'period': period,
                'benchmark': benchmark,
                'fund_returns': [
                    {'date': fund_dates[i], 'return': round(fund_returns[i], 2)}
                    for i in range(len(fund_dates))
                ],
                'benchmark_returns': benchmark_returns,
                'category_avg': category_avg,
                'summary': {
                    'fund_total_return': round(fund_returns[-1], 2) if fund_returns else 0,
                    'benchmark_total_return': benchmark_returns[-1]['return'] if benchmark_returns else 0,
                    'excess_return': round(fund_returns[-1] - (benchmark_returns[-1]['return'] if benchmark_returns else 0), 2) if fund_returns else 0
                }
            }
        }
    except Exception as e:
        logger.error(f"获取业绩走势图失败: {e}")
        return {'success': False, 'error': str(e)}


@router.get("/fund/{code}/period-returns")
async def get_fund_period_returns(code: str):
    """
    获取基金阶段收益率表格 (近1周/1月/3月/半年/1年 vs 同类平均)
    
    参考天天基金APP的业绩表现表格
    """
    try:
        db = get_db()
        fund = db.get_fund(code)
        if not fund:
            return {'success': False, 'error': f'未找到基金 {code}'}
        
        # 获取基金指标
        metrics = fund.get('latest_metrics', {})
        
        # 阶段收益率
        periods = [
            {'label': '近一周', 'key': 'return_1w', 'avg_key': 'avg_1w'},
            {'label': '近一月', 'key': 'return_1m', 'avg_key': 'avg_1m'},
            {'label': '近三月', 'key': 'return_3m', 'avg_key': 'avg_3m'},
            {'label': '近半年', 'key': 'return_6m', 'avg_key': 'avg_6m'},
            {'label': '近一年', 'key': 'return_1y', 'avg_key': 'avg_1y'},
        ]
        
        # 获取同类平均（简化实现：使用固定的参考数据）
        # TODO: 后续可从数据库计算真实同类平均
        category_averages = {
            'avg_1w': 0.5, 'avg_1m': 2.0, 'avg_3m': 5.0, 'avg_6m': 10.0, 'avg_1y': 15.0
        }
        
        result_periods = []
        for p in periods:
            fund_return = metrics.get(p['key'], 0) or 0
            avg_return = category_averages.get(p['avg_key'], 0)
            
            # 计算排名 (简化：根据与平均值的差异估算)
            diff = fund_return - avg_return
            if diff > 10:
                rank = 50
            elif diff > 5:
                rank = 150
            elif diff > 0:
                rank = 300
            else:
                rank = 600
            
            result_periods.append({
                'label': p['label'],
                'fund_return': round(fund_return, 2),
                'category_avg': round(avg_return, 2),
                'rank': rank,
                'total_funds': 1089,  # 假设同类基金总数
                'rank_level': '优秀' if rank < 200 else '良好' if rank < 500 else '一般'
            })
        
        return {
            'success': True,
            'data': {
                'fund_code': code,
                'fund_name': fund.get('name', code),
                'periods': result_periods
            }
        }
    except Exception as e:
        logger.error(f"获取阶段收益率失败: {e}")
        return {'success': False, 'error': str(e)}


@router.get("/fund/{code}/manager")
async def get_fund_manager_info(code: str):
    """
    获取基金经理信息
    
    参考天天基金APP的基金经理展示
    """
    try:
        db = get_db()
        fund = db.get_fund(code)
        if not fund:
            return {'success': False, 'error': f'未找到基金 {code}'}
        
        # 尝试获取基金经理信息（从akshare或缓存）
        # 目前返回基础模拟数据，后续可接入真实接口
        manager_info = {
            'name': fund.get('manager', '未知'),
            'avatar': None,  # 头像URL
            'experience_years': 5.4,  # 从业年限
            'managed_scale': 60.0,  # 管理规模(亿)
            'career_return': 12.64,  # 生涯年化
            'current_fund_start': fund.get('latest_metrics', {}).get('nav_date', '2025-01-16'),
            'current_fund_return': fund.get('latest_metrics', {}).get('return_1y', 0),
            'current_fund_annual_return': fund.get('latest_metrics', {}).get('annual_return', 0),
        }
        
        return {
            'success': True,
            'data': manager_info
        }
    except Exception as e:
        logger.error(f"获取基金经理信息失败: {e}")
        return {'success': False, 'error': str(e)}


# ==================== 早报晚报接口 ====================

@router.get("/daily-report")
async def get_daily_report(
    report_type: str = Query('morning', description="报告类型: morning(早报) / evening(晚报)")
):
    """
    获取每日市场报告 (早报/晚报)
    
    - 早报: 昨日复盘 + 今日看点
    - 晚报: 今日复盘 + 明日展望
    """
    try:
        ai_service = get_ai_service()
        fetcher = get_data_fetcher()
        
        # 获取市场数据
        breadth = fetcher.get_market_breadth()
        
        # 获取主要指数
        indices_data = []
        for symbol, name in [('000001', '上证'), ('399001', '深证'), ('399006', '创业板')]:
            quote = fetcher.get_realtime_index_quote(symbol)
            if quote:
                indices_data.append(f"{name}: {quote.get('change_pct', 0):+.2f}%")
        
        # 获取涨幅榜
        top_gainers = fetcher.get_market_top_gainers(period='day', limit=5)
        gainers_text = ', '.join([f"{g['name']}({g['gain']:+.2f}%)" for g in top_gainers[:3]]) if top_gainers else '暂无数据'
        
        # 构建AI prompt
        if report_type == 'morning':
            prompt = f"""请生成一份简洁的股市早报（150字左右）：

今日指数: {', '.join(indices_data) if indices_data else '暂无数据'}
涨跌家数: 上涨{breadth.get('up', 0)}家, 下跌{breadth.get('down', 0)}家
领涨基金: {gainers_text}

要求格式：
1. 昨日复盘（2-3句）
2. 今日看点（2-3句）
3. 投资建议（1句）"""
        else:
            prompt = f"""请生成一份简洁的股市晚报（150字左右）：

今日指数: {', '.join(indices_data) if indices_data else '暂无数据'}
涨跌家数: 上涨{breadth.get('up', 0)}家, 下跌{breadth.get('down', 0)}家
领涨基金: {gainers_text}

要求格式：
1. 今日复盘（2-3句）
2. 明日展望（2-3句）
3. 操作建议（1句）"""
        
        # 调用AI生成
        if ai_service:
            result = await ai_service.ask_ai(prompt, system_prompt="你是一位专业的证券分析师，擅长撰写简洁有力的市场日报。")
            content = result.get('content', '') if result.get('success') else None
        else:
            content = None
        
        # 如果AI不可用，返回基础数据
        if not content:
            content = f"""## {'📰 早报' if report_type == 'morning' else '📰 晚报'}

### 市场概况
- 指数: {', '.join(indices_data) if indices_data else '暂无数据'}
- 涨跌比: {breadth.get('up', 0)}/{breadth.get('down', 0)}

### 领涨基金
{gainers_text}

*更多分析请配置AI服务*"""
        
        return {
            'success': True,
            'data': {
                'type': report_type,
                'title': '每日早报' if report_type == 'morning' else '每日晚报',
                'content': content,
                'market_data': {
                    'indices': indices_data,
                    'breadth': breadth,
                    'top_gainers': top_gainers[:5] if top_gainers else []
                },
                'generated_at': datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            }
        }
    except Exception as e:
        logger.error(f"生成每日报告失败: {e}")
        return {'success': False, 'error': str(e)}


# ==================== 实时热点接口 ====================

@router.get("/hotspots")
async def get_realtime_hotspots():
    """
    获取实时市场热点板块
    """
    try:
        try:
            from ..services.news_service import get_news_service
        except (ImportError, ValueError):
            from services.news_service import get_news_service
        
        news_service = get_news_service()
        sentiment = await news_service.analyze_market_sentiment()
        
        hot_sectors = sentiment.get('hot_sectors', []) if sentiment else []
        
        # 为每个热点板块获取领涨基金
        snapshot_service = get_snapshot_service()
        enriched_sectors = []
        
        for sector in hot_sectors[:8]:  # 限制8个
            sector_name = sector.get('name', '')
            recommends = snapshot_service.get_recommendations(theme=sector_name)
            top_funds = []
            if recommends and recommends.get('success') and recommends.get('results'):
                top_funds = recommends['results'][:3]
            
            enriched_sectors.append({
                'name': sector_name,
                'sentiment': sector.get('sentiment', 'neutral'),
                'heat': sector.get('heat', 50),
                'top_funds': [{'code': f['code'], 'name': f['name'], 'score': f.get('score')} for f in top_funds]
            })
        
        return {
            'success': True,
            'data': {
                'hotspots': enriched_sectors,
                'updated_at': datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            }
        }
    except Exception as e:
        logger.error(f"获取实时热点失败: {e}")
        return {'success': False, 'error': str(e)}


# ==================== V1 兼容接口 ====================

@router.get("/v1/recommendations")
async def get_recommendations_v1(
    theme: Optional[str] = Query(None, description="主题筛选"),
    limit: int = Query(10, description="返回数量")
):
    """v1 推荐列表接口"""
    try:
        service = get_snapshot_service()
        return service.get_recommendations(theme=theme, limit=limit)
    except Exception as e:
        logger.error(f"获取推荐列表失败: {e}")
        return {"status": "error", "message": str(e)}

@router.get("/v1/rankings")
async def get_rankings_v1(
    sort_by: str = Query("score", description="排序字段: score/return_1y /sharpe/alpha/max_drawdown"),
    theme: Optional[str] = Query(None, description="主题筛选"),
    limit: int = Query(20, description="返回数量")
):
    """v1 多维排行接口"""
    try:
        service = get_snapshot_service()
        return service.get_ranking_list(sort_by=sort_by, limit=limit, theme=theme)
    except Exception as e:
        logger.error(f"获取排行榜失败: {e}")
        return {"status": "error", "message": str(e)}

@router.get("/v1/sectors/hot")
async def get_hot_sectors_v1():
    """获取热门板块排行"""
    try:
        service = get_sector_service()
        sectors = service.get_available_sectors()
        
        results = []
        # 取前8个板块进行指标聚合
        for sector_info in sectors[:8]:
            sector_name = sector_info.get('name')
            if not sector_name: continue
            
            res = service.get_sector_metrics(sector_name)
            if res.get('success'):
                m = res.get('metrics', {})
                results.append({
                    'sector': sector_name,
                    'avg_return': m.get('avg_return_1y', 0),
                    'fund_count': res.get('fund_count', 0),
                    'best_fund': m.get('best_fund_name', '')
                })
        
        # 按收益率排序
        results.sort(key=lambda x: x.get('avg_return', 0), reverse=True)
        
        return {"status": "success", "data": results}
    except Exception as e:
        logger.error(f"获取热门板块失败: {e}")
        return {"status": "error", "message": str(e)}

@router.get("/v1/market/hotspots")
async def get_market_hotspots_v1():
    """获取 AI 市场热点摘要 (结构化版) - 带缓存 & 并发优化"""
    try:
        # 1. Check Cache (1 Hour TTL)
        now = datetime.datetime.now()
        if _hotspots_cache['data'] and _hotspots_cache['updated_at']:
            elapsed = (now - _hotspots_cache['updated_at']).seconds
            if elapsed < 3600:
                return _hotspots_cache['data']

        news_service = get_news_service()
        ai_service = get_ai_service()
        
        # 2. Parallel Fetching
        import asyncio
        
        # 定义并发任务
        async def fetch_news_task():
            return await news_service.get_market_news(limit=12)
            
        async def fetch_sentiment_task():
            # analyze_market_sentiment 内部也会 fetch news，为避免重复工作，
            # 理想状况下 news_service 内部有缓存，所以这里直接调用是安全的
            return await news_service.analyze_market_sentiment()

        news, sentiment = await asyncio.gather(fetch_news_task(), fetch_sentiment_task())
        
        news_text = "\n".join([f"- {n['title']}" for n in news])
        prompt = f"""基于以下近期财经新闻，提取最核心的 3-5 条市场热点。
请严格按以下 JSON 格式返回列表：
[
  {{
    "title": "热点标题",
    "what_happened": "发生了什么的具体描述",
    "sectors": ["涉及板块1", "涉及板块2"],
    "comment": "简短且专业的 AI 点评"
  }}
]

要求：
1. 语言简练专业。
2. 涉及板块需具体。
3. 必须返回合法的 JSON 数组，不要包含任何其他文字。

待分析新闻：
{news_text}"""
        
        # 调用 AI
        res = await ai_service.ask_ai(prompt, system_prompt="你是一个专业的金融数据处理助手，只输出 JSON 格式。")
        
        hotspots_list = []
        if res.get('success'):
            content = res.get('content', '[]')
            # 使用更鲁棒的正则提取 JSON 数组
            try:
                import re
                import ast
                match = re.search(r'\[.*\]', content, re.DOTALL)
                if match:
                    json_str = match.group(0)
                    try:
                        hotspots_list = json.loads(json_str)
                    except json.JSONDecodeError:
                        # 尝试 Python 字面量解析 (处理单引号等)
                        hotspots_list = ast.literal_eval(json_str)
                else:
                    # 尝试直接解析
                    hotspots_list = json.loads(content)
            except Exception as parse_error:
                logger.error(f"解析热点 JSON 失败: {parse_error}\nContent: {content}")
                # Fallback: 显示原始返回内容以便调试
                hotspots_list = [{
                    "title": "AI解析异常 (调试模式)",
                    "what_happened": f"解析错误: {str(parse_error)}",
                    "sectors": ["DEBUG"],
                    "comment": f"原始返回: {content[:200]}..." # 截取前200字符
                }]
        
        result_data = {
            "status": "success", 
            "hotspots": hotspots_list,
            "sentiment": sentiment,
            "news_count": len(news),
            "updated_at": now.strftime('%Y-%m-%d %H:%M:%S'),
            "cached": False
        }
        
        # 3. Save to Cache
        _hotspots_cache['data'] = {**result_data, 'cached': True} # Next time it will return cached=True
        _hotspots_cache['updated_at'] = now
        
        return result_data

    except Exception as e:
        logger.error(f"获取市场热点失败: {e}")
        return {"status": "error", "message": str(e)}

@router.get("/v1/sectors/{sector}/analyze")
async def analyze_sector_v1(sector: str, period: str = 'tomorrow'):
    """获取板块深度分析与预测"""
    try:
        service = get_sector_service()
        # 同时获取基础指标、情绪和预测
        metrics = service.get_sector_metrics(sector)
        sentiment = await service.get_sector_sentiment(sector)
        prediction = await service.predict_sector(sector, period=period)
        
        return {
            "status": "success",
            "data": {
                "sector": sector,
                "metrics": metrics,
                "sentiment": sentiment,
                "prediction": prediction
            }
        }
    except Exception as e:
        logger.error(f"分析板块 {sector} 失败: {e}")
        return {"status": "error", "message": str(e)}

@router.get("/fund/diagnose/{code}")
async def diagnose_fund_api(code: str):
    """
    获取基金健康度诊断报告
    """
    try:
        db = get_db()
        # 获取最新快照中的指标
        snapshot = db.get_latest_snapshot()
        if not snapshot:
            return error_response(error="暂无快照数据，请先执行全量更新")
            
        metrics = db.get_fund_metrics(snapshot['id'], code)
        if not metrics:
            return error_response(error=f"未找到基金 {code} 的指标数据")
            
        service = get_health_service()
        result = service.diagnose_fund(code, metrics.get('name', ''), metrics)
        return success_response(data=result)
    except Exception as e:
        logger.error(f"Fund diagnosis failed for {code}: {e}")
        return error_response(error=str(e))

@router.get("/fund/style/{code}")
async def analyze_fund_style_api(code: str):
    """
    获取基金风格分析报告
    """
    try:
        fetcher = get_data_fetcher()
        # 获取历史净值用于分析
        nav_df = fetcher.get_fund_nav(code)
        
        if nav_df is None or nav_df.empty:
            return error_response(error=f"无法获取基金 {code} 的净值数据")
            
        service = get_style_service()
        result = service.analyze_style(code, nav_df)
        return success_response(data=result)
    except Exception as e:
        logger.error(f"Style analysis failed for {code}: {e}")
        return error_response(error=str(e))

@router.get("/investment/dca/{code}")
async def get_smart_dca_advice(code: str, amount: float = Query(1000, description="定投基础额度")):
    """
    获取基于均线偏离度的智能定投建议
    """
    try:
        fetcher = get_data_fetcher()
        nav_df = fetcher.get_fund_nav(code)
        
        if nav_df is None or nav_df.empty:
            return error_response(error=f"无法获取基金 {code} 的净值数据")
            
        service = get_investment_service()
        result = service.calculate_smart_dca(nav_df, base_amount=amount)
        return success_response(data=result)
    except Exception as e:
        logger.error(f"Smart DCA advice failed for {code}: {e}")
        return error_response(error=str(e))

@router.get("/market/calendar")
async def get_investment_calendar_api(date: Optional[str] = Query(None, description="开始日期 YYYYMMDD"), 
                                     days: int = Query(7, ge=1, le=30)):
    """
    获取投资日历 (宏观经济事件)
    """
    try:
        service = get_calendar_service()
        result = service.get_investment_calendar(start_date=date, days=days)
        return success_response(data=result)
    except Exception as e:
        logger.error(f"Failed to get investment calendar: {e}")
        return error_response(error=str(e))

@router.get("/market/money_flow")
async def get_big_money_flow_api(limit: int = Query(20, ge=5, le=100)):
    """
    获取大额资金流入流出监测 (基于基金份额变动)
    """
    try:
        service = get_money_flow_service()
        result = service.get_big_money_flows(top_n=limit)
        return success_response(data=result)
    except Exception as e:
        logger.error(f"Failed to get money flow data: {e}")
        return error_response(error=str(e))


# ==================== 专业量化接口 ====================

@router.post("/portfolio/backtest")
async def run_portfolio_backtest(portfolio: List[Dict[str, Any]]):
    """
    运行投资组合回测
    """
    try:
        service = get_backtest_service()
        result = await service.run_backtest(portfolio)
        return success_response(data=result)
    except Exception as e:
        logger.error(f"Backtest failed: {e}")
        return error_response(error=str(e))

@router.post("/compare/fees")
async def compare_funds_fees(req: CompareRequest):
    """
    对比多只基金的费率结构
    """
    try:
        service = get_fee_service()
        result = service.compare_fees(req.codes)
        return success_response(data=result)
    except Exception as e:
        logger.error(f"Fee comparison failed: {e}")
        return error_response(error=str(e))

@router.get("/macro/dashboard")
async def get_macro_dashboard():
    """
    获取宏观看板数据
    """
    try:
        service = get_macro_service()
        result = await service.get_macro_dashboard()
        return success_response(data=result)
    except Exception as e:
        logger.error(f"Macro dashboard failed: {e}")
        return error_response(error=str(e))

@router.get("/fee/calculate")
async def calculate_fee_api(amount: float, years: int, rate: float):
    """
    计算基金费用损失
    """
    try:
        # A = P * (1 - (1-r)^n)
        loss = amount * (1 - (1 - rate/100)**years)
        return success_response(data={
            "original_amount": amount,
            "years": years,
            "fee_rate": rate,
            "fee_loss": round(loss, 2),
            "remaining": round(amount - loss, 2)
        })
    except Exception as e:
        return error_response(error=str(e))

# ==================== 自选列表接口 ====================

@router.get("/watchlist/realtime")
async def get_watchlist_realtime():
    """
    获取自选列表及实时估值数据
    """
    try:
        db = get_db()
        items = db.get_watchlist()
        if not items:
            return success_response(data=[])
            
        fetcher = get_data_fetcher()
        codes = [item['fund_code'] for item in items]
        
        # 批量获取估值
        valuations = fetcher.get_realtime_valuation_batch(codes)
        
        results = []
        for item in items:
            code = item['fund_code']
            val = valuations.get(code, {})
            
            # 分时走势已删除（因其使用随机模拟数据）
            
            results.append({
                'code': code,
                'name': item['fund_name'],
                'estimation_nav': val.get('estimation_nav', 0),
                'estimation_growth': val.get('estimation_growth', 0),
                'nav': val.get('nav', 0),
                'nav_date': val.get('nav_date', ''),
                'update_time': val.get('time', ''),
                'notes': item.get('notes', '')
            })
            
        return success_response(data=results)
    except Exception as e:
        logger.error(f"Get realtime watchlist failed: {e}")
        return error_response(error=str(e))

@router.post("/watchlist/add")
async def add_to_watchlist(req: WatchlistAddRequest):
    """添加自选"""
    try:
        db = get_db()
        db.add_to_watchlist(req.code, req.name)
        return success_response(message='已加入自选')
    except Exception as e:
        logger.error(f"Add watchlist failed: {e}")
        return error_response(error=str(e))

@router.post("/watchlist/remove")
async def remove_from_watchlist(req: WatchlistRemoveRequest):
    """移除自选"""
    try:
        db = get_db()
        db.remove_from_watchlist(req.code)
        return success_response(message='已移除')
    except Exception as e:
        logger.error(f"Remove watchlist failed: {e}")
        return error_response(error=str(e))


# ==================== Phase 7: 用户中心高级工具 ====================

@router.get("/daily-actions")
async def get_daily_actions(limit: int = 10):
    """获取每日操作建议清单"""
    try:
        from .services.action_service import get_action_service
        service = get_action_service()
        return await service.get_daily_actions(limit=limit)
    except Exception as e:
        logger.error(f"获取每日操作建议失败: {e}")
        return {"status": "error", "message": str(e)}

@router.get("/portfolio-builder")
async def build_portfolio(amount: float = Query(..., gt=0), risk_level: str = 'moderate'):
    """一键生成建仓方案"""
    try:
        from .services.portfolio_builder import get_portfolio_builder
        service = get_portfolio_builder()
        return service.build_portfolio(amount, risk_level)
    except Exception as e:
        logger.error(f"生成建仓方案失败: {e}")
        return {"success": False, "error": str(e)}

@router.get("/user/profile")
async def get_user_profile():
    """获取用户风险偏好与预算"""
    try:
        db = get_db()
        return {"success": True, "data": db.get_user_profile()}
    except Exception as e:
        return {"success": False, "error": str(e)}

@router.post("/user/profile")
async def save_user_profile(profile: Dict[str, Any]):
    """更新用户风险偏好与预算"""
    try:
        db = get_db()
        db.save_user_profile(
            risk_level=profile.get('risk_level', 'moderate'),
            budget=profile.get('budget', 10000)
        )
        return {"success": True, "message": "设置已保存"}
    except Exception as e:
        return {"success": False, "error": str(e)}

@router.get("/dca/plans")
async def get_dca_plans():
    """获取定投计划列表"""
    try:
        db = get_db()
        return {"success": True, "data": db.get_dca_plans()}
    except Exception as e:
        return {"success": False, "error": str(e)}

@router.post("/dca/plans")
async def add_dca_plan(plan: Dict[str, Any]):
    """添加或修改定投计划"""
    try:
        db = get_db()
        success = db.add_dca_plan(
            fund_code=plan['fund_code'],
            fund_name=plan.get('fund_name'),
            base_amount=plan['base_amount'],
            frequency=plan.get('frequency', 'weekly'),
            day_of_week=plan.get('day_of_week'),
            day_of_month=plan.get('day_of_month')
        )
        return {"success": success}
    except Exception as e:
        return {"success": False, "error": str(e)}

@router.post("/dca/plans/{plan_id}/status")
async def update_dca_status(plan_id: int, is_active: bool):
    """更新定投计划状态 (暂停/启动)"""
    try:
        db = get_db()
        success = db.update_dca_status(plan_id, 1 if is_active else 0)
        return {"success": success}
    except Exception as e:
        return {"success": False, "error": str(e)}

@router.get("/notifications")
async def get_notifications():
    """获取未读通知"""
    try:
        db = get_db()
        return {"success": True, "data": db.get_unread_notifications()}
    except Exception as e:
        return {"success": False, "error": str(e)}

@router.post("/notifications/{notif_id}/read")
async def mark_notification_read(notif_id: int):
    """标记通知为已读"""
    try:
        db = get_db()
        db.mark_notification_read(notif_id)
        return {"success": True}
    except Exception as e:
        return {"success": False, "error": str(e)}
