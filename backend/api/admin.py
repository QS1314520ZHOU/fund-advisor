# backend/api/admin.py
"""
管理接口 - 需要鉴权
"""

import asyncio
from fastapi import APIRouter, Header, HTTPException, BackgroundTasks, Query
from typing import Optional

try:
    from config import get_settings
    from services.snapshot import get_snapshot_service
    from services.ai_service import get_ai_service
    from database import get_db
    from api.responses import ApiResponse, success_response, error_response
except (ImportError, ValueError):
    from backend.config import get_settings
    from backend.services.snapshot import get_snapshot_service
    from backend.services.ai_service import get_ai_service
    from backend.database import get_db
    from backend.api.responses import ApiResponse, success_response, error_response

router = APIRouter(prefix="/admin")


def verify_admin_token(x_admin_token: Optional[str] = Header(None)):
    """验证管理员Token"""
    settings = get_settings()
    
    if not settings.ADMIN_TOKEN:
        raise HTTPException(
            status_code=500, 
            detail="服务器未配置管理员Token，请在 .env 文件中设置 ADMIN_TOKEN"
        )
    
    if not x_admin_token:
        raise HTTPException(
            status_code=401, 
            detail="缺少管理员Token，请在请求头中添加 X-Admin-Token"
        )
    
    if x_admin_token != settings.ADMIN_TOKEN:
        raise HTTPException(
            status_code=401, 
            detail="管理员Token无效"
        )
    
    return True


@router.post("/update/snapshot")
async def trigger_snapshot_update(
    background_tasks: BackgroundTasks,
    x_admin_token: Optional[str] = Header(None),
    async_mode: bool = Query(True, description="是否异步执行（推荐True）"),
    max_qualified: int = Query(230, ge=50, le=500, description="最大入选数量")
):
    """
    触发完整快照更新
    
    - async_mode=True: 后台异步执行，立即返回，通过 /update-status 查看进度
    - async_mode=False: 同步执行，等待完成后返回（可能需要较长时间）
    """
    verify_admin_token(x_admin_token)
    
    service = get_snapshot_service()
    
    # 检查是否正在更新
    if service.is_updating():
        return error_response(
            error='更新任务正在进行中，请等待完成',
            message=f"当前进度: {service.get_progress()}%"
        )
    
    if async_mode:
        # 异步执行
        background_tasks.add_task(service.create_full_snapshot, max_qualified)
        return success_response(
            message='更新任务已启动',
            data={'async': True, 'tip': '请通过 GET /api/v1/admin/update-status 查看进度'}
        )
    else:
        # 同步执行（阻塞）
        result = service.create_full_snapshot(max_qualified=max_qualified)
        return ApiResponse(**result) if isinstance(result, dict) else success_response(data=result)


@router.post("/update/fund-list")
async def update_fund_list(
    x_admin_token: Optional[str] = Header(None)
):
    """
    仅更新基金列表（快速，不重算指标）
    
    用于刷新候选池，不创建新快照
    """
    verify_admin_token(x_admin_token)
    
    try:
        from ..services.data_fetcher import get_data_fetcher
        fetcher = get_data_fetcher()
        
        # 强制刷新
        fetcher._fund_list_cache = None
        fetcher._fund_list_cache_time = None
        
        candidates = fetcher.filter_candidate_funds()
        
        # 统计主题分布
        theme_stats = {}
        for c in candidates:
            for t in c.get('themes', ['综合']):
                theme_stats[t] = theme_stats.get(t, 0) + 1
        
        return {
            'success': True,
            'message': '基金列表更新完成',
            'candidate_count': len(candidates),
            'theme_distribution': theme_stats
        }
    except Exception as e:
        return {
            'success': False,
            'error': str(e)
        }


@router.get("/status")
async def get_admin_status(
    x_admin_token: Optional[str] = Header(None)
):
    """
    获取系统详细状态
    """
    verify_admin_token(x_admin_token)
    
    service = get_snapshot_service()
    db = get_db()
    settings = get_settings()
    
    # AI服务状态
    ai_status = None
    try:
        ai_service = get_ai_service()
        if ai_service:
            ai_status = ai_service.get_model_info()
    except Exception as e:
        ai_status = {'error': str(e)}
    
    return {
        'is_updating': service.is_updating(),
        'progress': service.get_progress(),
        'latest_snapshot': db.get_latest_snapshot(),
        'fund_count': db.get_fund_count(),
        'recent_logs': db.get_recent_logs(limit=5),
        'config': {
            'default_benchmark': settings.DEFAULT_BENCHMARK,
            'auto_update_enabled': settings.AUTO_UPDATE_ENABLED,
            'auto_update_time': f"{settings.AUTO_UPDATE_HOUR:02d}:{settings.AUTO_UPDATE_MINUTE:02d}"
        },
        'ai_service': ai_status
    }


@router.get("/logs")
async def get_logs(
    x_admin_token: Optional[str] = Header(None),
    limit: int = Query(20, ge=1, le=100, description="返回数量")
):
    """
    获取更新日志
    """
    verify_admin_token(x_admin_token)
    
    db = get_db()
    logs = db.get_recent_logs(limit=limit)
    
    return {
        'success': True,
        'count': len(logs),
        'data': logs
    }


@router.get("/snapshots")
async def list_snapshots(
    x_admin_token: Optional[str] = Header(None),
    limit: int = Query(10, ge=1, le=50)
):
    """
    列出历史快照
    """
    verify_admin_token(x_admin_token)
    
    try:
        db = get_db()
        
        # 查询历史快照
        with db.get_cursor() as cursor:
            cursor.execute("""
                SELECT id, snapshot_date, total_funds, qualified_funds, 
                       benchmark, status, created_at, completed_at
                FROM snapshots
                ORDER BY created_at DESC
                LIMIT ?
            """, (limit,))
            
            rows = cursor.fetchall()
            snapshots = []
            for row in rows:
                snapshots.append({
                    'id': row[0],
                    'snapshot_date': row[1],
                    'total_funds': row[2],
                    'qualified_funds': row[3],
                    'benchmark': row[4],
                    'status': row[5],
                    'created_at': row[6],
                    'completed_at': row[7]
                })
        
        return {
            'success': True,
            'count': len(snapshots),
            'data': snapshots
        }
    except Exception as e:
        return {
            'success': False,
            'error': str(e)
        }


@router.post("/ai/switch-model")
async def switch_ai_model(
    model: str = Query(..., description="目标模型名称"),
    x_admin_token: Optional[str] = Header(None)
):
    """
    切换AI模型
    """
    verify_admin_token(x_admin_token)
    
    try:
        ai_service = get_ai_service()
        if not ai_service:
            return {
                'success': False, 
                'error': 'AI服务未配置，请检查 .env 中的 AI_API_KEY'
            }
        
        # 获取可用模型列表
        available = await ai_service.fetch_available_models()
        
        if model not in available:
            return {
                'success': False,
                'error': f'模型 {model} 不可用',
                'available_models': available[:30],
                'tip': '请从 available_models 中选择一个模型'
            }
        
        # 切换模型
        old_model = ai_service.current_model
        ai_service.current_model = model
        
        return {
            'success': True,
            'message': f'已从 {old_model} 切换到 {model}',
            'old_model': old_model,
            'current_model': model
        }
    except Exception as e:
        return {
            'success': False,
            'error': str(e)
        }


@router.get("/ai/models")
async def list_ai_models(
    x_admin_token: Optional[str] = Header(None),
    refresh: bool = Query(False, description="是否强制刷新")
):
    """
    列出可用AI模型
    """
    verify_admin_token(x_admin_token)
    
    try:
        ai_service = get_ai_service()
        if not ai_service:
            return {
                'success': False,
                'error': 'AI服务未配置'
            }
        
        models = await ai_service.fetch_available_models(force_refresh=refresh)
        recommended = ai_service.get_recommended_models()
        
        return {
            'success': True,
            'current_model': ai_service.current_model,
            'total_count': len(models),
            'recommended': recommended,
            'all_models': models
        }
    except Exception as e:
        return {
            'success': False,
            'error': str(e)
        }


@router.post("/cache/clear")
async def clear_cache(
    x_admin_token: Optional[str] = Header(None),
    cache_type: str = Query("expired", description="缓存类型: expired/ai/all")
):
    """
    清理缓存
    
    - expired: 仅清理过期缓存
    - ai: 清理所有AI缓存
    - all: 清理所有缓存
    """
    verify_admin_token(x_admin_token)
    
    try:
        db = get_db()
        cleared_count = 0
        
        if cache_type == 'expired':
            cleared_count = db.clear_expired_cache()
        elif cache_type == 'ai':
            with db.get_cursor() as cursor:
                cursor.execute("DELETE FROM ai_cache")
                cleared_count = cursor.rowcount
        elif cache_type == 'all':
            with db.get_cursor() as cursor:
                cursor.execute("DELETE FROM ai_cache")
                cleared_count = cursor.rowcount
            # 清理数据获取器缓存
            from ..services.data_fetcher import get_data_fetcher
            fetcher = get_data_fetcher()
            fetcher._fund_list_cache = None
            fetcher._fund_list_cache_time = None
        
        return {
            'success': True,
            'message': f'已清理 {cache_type} 缓存',
            'cleared_count': cleared_count
        }
    except Exception as e:
        return {
            'success': False,
            'error': str(e)
        }


@router.delete("/snapshot/{snapshot_id}")
async def delete_snapshot(
    snapshot_id: int,
    x_admin_token: Optional[str] = Header(None)
):
    """
    删除指定快照（谨慎使用）
    """
    verify_admin_token(x_admin_token)
    
    try:
        db = get_db()
        
        # 检查是否是最新快照
        latest = db.get_latest_snapshot()
        if latest and latest['id'] == snapshot_id:
            return {
                'success': False,
                'error': '不能删除最新快照'
            }
        
        with db.get_cursor() as cursor:
            # 删除关联的指标
            cursor.execute("DELETE FROM fund_metrics WHERE snapshot_id = ?", (snapshot_id,))
            metrics_deleted = cursor.rowcount
            
            # 删除快照
            cursor.execute("DELETE FROM snapshots WHERE id = ?", (snapshot_id,))
            
            if cursor.rowcount == 0:
                return {
                    'success': False,
                    'error': f'快照 {snapshot_id} 不存在'
                }
        
        return {
            'success': True,
            'message': f'已删除快照 {snapshot_id}',
            'metrics_deleted': metrics_deleted
        }
    except Exception as e:
        return {
            'success': False,
            'error': str(e)
        }


@router.post("/test/ai")
async def test_ai_connection(
    x_admin_token: Optional[str] = Header(None)
):
    """
    测试AI服务连接
    """
    verify_admin_token(x_admin_token)
    
    try:
        ai_service = get_ai_service()
        if not ai_service:
            return {
                'success': False,
                'error': 'AI服务未配置'
            }
        
        # 简单测试
        test_prompt = "请用一句话介绍自己"
        result = await ai_service._call_ai(
            system_prompt="你是一个AI助手",
            user_prompt=test_prompt,
            max_tokens=100
        )
        
        return {
            'success': True,
            'model_used': ai_service.current_model,
            'response': result[:200] if result else None
        }
    except Exception as e:
        return {
            'success': False,
            'error': str(e)
        }

