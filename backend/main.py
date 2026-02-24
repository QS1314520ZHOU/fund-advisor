# backend/main.py
"""
基金AI智能推荐系统 v3.0
FastAPI 应用入口
"""

import logging
import webbrowser
import threading
import warnings
# 忽略 pkg_resources 导致的弃用警告 (通常由 py_mini_racer 触发)
warnings.filterwarnings("ignore", category=UserWarning, module="pkg_resources")
from pathlib import Path
from contextlib import asynccontextmanager
from fastapi import FastAPI, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, HTMLResponse

import sys
# 确保项目根目录在 sys.path 中，以支持绝对导入和直接运行
current_file = Path(__file__).resolve()
backend_dir = current_file.parent
project_root = backend_dir.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))
if str(backend_dir) not in sys.path:
    sys.path.insert(0, str(backend_dir))

try:
    from backend.config import get_settings, ensure_data_dir
    from backend.database import get_db
    from backend.scheduler import init_scheduler
except ImportError:
    from config import get_settings, ensure_data_dir
    from database import get_db
    from scheduler import init_scheduler

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('fund_advisor.log', encoding='utf-8')
    ]
)
logger = logging.getLogger(__name__)

# 项目根目录
BASE_DIR = Path(__file__).resolve().parent.parent


@asynccontextmanager
async def lifespan(app: FastAPI):
    """应用生命周期管理"""
    # ========== 启动阶段 ==========
    logger.info("=" * 60)
    logger.info("🚀 基金AI智能推荐系统 v3.0 启动中...")
    
    # 确保数据目录存在
    ensure_data_dir()
    
    # 初始化数据库
    db = get_db()
    
    # 初始化调度器
    init_scheduler()
    
    # 获取配置
    settings = get_settings()
    
    # 显示配置信息
    logger.info(f"🤖 AI模型: {settings.AI_MODEL}")
    logger.info(f"🔗 AI Base URL: {settings.AI_BASE_URL}")
    logger.info(f"🔄 回退模型: {settings.AI_FALLBACK_MODELS}")
    logger.info(f"📊 默认基准: {settings.DEFAULT_BENCHMARK}")
    logger.info(f"🔐 管理Token: {'已配置' if settings.ADMIN_TOKEN else '⚠️ 未配置'}")
    logger.info(f"🔑 AI Key: {'已配置' if settings.AI_API_KEY else '⚠️ 未配置'}")
    
    # 尝试获取可用模型列表
    if settings.AI_API_KEY:
        try:
            try:
                from backend.services.ai_service import get_ai_service
            except ImportError:
                from services.ai_service import get_ai_service
            ai_service = get_ai_service()
            if ai_service:
                models = await ai_service.fetch_available_models()
                if models:
                    logger.info(f"🎯 可用模型数: {len(models)}")
                    logger.info(f"📋 推荐模型: {models[:5]}")
        except Exception as e:
            logger.warning(f"⚠️ 获取AI模型列表失败: {e}")
    
    # 读取数据库状态
    try:
        snapshot = db.get_latest_snapshot()
        fund_count = db.get_fund_count()
        
        if snapshot:
            logger.info(f"📅 最新快照: {snapshot.get('snapshot_date')}")
            logger.info(f"✅ 入选基金: {snapshot.get('qualified_funds', 0)} 只")
        else:
            logger.info("📅 最新快照: 暂无")
        
        logger.info(f"📊 基金总数: {fund_count} 只")
        
        # ========== 检查数据新鲜度 ==========
        from datetime import datetime, time as dt_time
        now = datetime.now()
        today_str = now.strftime('%Y-%m-%d')
        current_time = now.time()
        
        need_update = False
        update_reason = ""
        
        if not snapshot:
            need_update = True
            update_reason = "暂无快照数据"
        elif snapshot.get('snapshot_date') != today_str:
            # 只有在14:30之后才自动更新（给净值数据足够时间更新）
            if current_time >= dt_time(14, 30):
                need_update = True
                update_reason = f"快照日期为 {snapshot.get('snapshot_date')}，需要更新到今日"
        
        if need_update:
            logger.info(f"🔄 检测到数据需要更新: {update_reason}")
            # 尝试异步触发更新
            tasks = BackgroundTasks()
            await check_and_trigger_update(tasks)
        else:
            logger.info("✅ 数据已是最新")
            
    except Exception as e:
        logger.warning(f"⚠️ 读取数据库状态失败: {e}")
    
    logger.info("=" * 60)
    logger.info("✅ 系统启动完成!")
    logger.info("=" * 60)
    
    # 自动打开浏览器
    def open_browser():
        import time
        time.sleep(1)  # 等待服务器完全启动
        webbrowser.open('http://127.0.0.1:8000/app')
        logger.info("🌐 已自动打开浏览器")
    
    threading.Thread(target=open_browser, daemon=True).start()
    
    yield
    
    # ========== 关闭阶段 ==========
    logger.info("系统关闭中...")


async def check_and_trigger_update(background_tasks: BackgroundTasks):
    """启动时检查是否需要更新数据"""
    try:
        db = get_db()
        # 获取最后一条快照记录
        last_snap = db.get_latest_snapshot()
        
        from datetime import datetime
        now = datetime.now()
        # 如果没有快照，或者快照不是今天的且现在已经过了14:30
        should_update = False
        if not last_snap:
            should_update = True
        else:
            snap_time = datetime.strptime(last_snap['snapshot_date'], '%Y-%m-%d')
            if snap_time.date() < now.date() and now.hour >= 14 and now.minute >= 30:
                should_update = True
        
        if should_update:
            logger.info("检测到数据陈旧，触发背景自动更新...")
            try:
                from backend.services.snapshot import get_snapshot_service
            except ImportError:
                from services.snapshot import get_snapshot_service
            snapshot_service = get_snapshot_service()
            background_tasks.add_task(snapshot_service.create_full_snapshot)
        else:
            logger.info("异步检查：数据已是最新，无需更新")
            
    except Exception as e:
        logger.error(f"启动自动更新检查失败: {e}")


# 创建应用
settings = get_settings()
app = FastAPI(
    title="基金AI智能推荐系统",
    description="基于量化指标和AI分析的基金智能推荐平台",
    version="3.0.0",
    lifespan=lifespan
)

# CORS 配置
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS if settings.CORS_ORIGINS else ["http://localhost:8000", "http://127.0.0.1:8000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 注册路由
try:
    from backend.api import query, admin
except ImportError:
    from api import query, admin

from fastapi.staticfiles import StaticFiles

app.include_router(query.router)
app.include_router(admin.router)

# 静态数据存储挂载
storage_path = BASE_DIR / "backend" / "data" / "storage"
storage_path.mkdir(parents=True, exist_ok=True)
app.mount("/static/storage", StaticFiles(directory=str(storage_path)), name="storage")


@app.get("/app", response_class=HTMLResponse)
async def serve_frontend():
    """提供前端页面"""
    frontend_path = BASE_DIR / "frontend" / "index.html"
    
    if frontend_path.exists():
        return FileResponse(frontend_path)
    
    return HTMLResponse(
        content=f"""
        <!DOCTYPE html>
        <html>
        <head><title>404 - 前端文件未找到</title></head>
        <body>
            <h1>前端文件未找到</h1>
            <p>请确保 frontend/index.html 文件存在</p>
            <p>期望路径: {frontend_path}</p>
            <p><a href="/docs">访问 API 文档</a></p>
        </body>
        </html>
        """,
        status_code=404
    )


@app.get("/", response_class=HTMLResponse)
async def root():
    """首页 - 显示系统状态"""
    try:
        db = get_db()
        snapshot = db.get_latest_snapshot()
        fund_count = db.get_fund_count()
        settings = get_settings()
        
        snapshot_info = "暂无快照"
        qualified_info = "0"
        if snapshot:
            snapshot_info = snapshot.get('snapshot_date', '未知')
            qualified_info = snapshot.get('qualified_funds', 0)
        
        ai_status = "已配置" if settings.AI_API_KEY else "未配置"
        ai_model = settings.AI_MODEL or "未设置"
        
    except Exception as e:
        snapshot_info = f"错误: {e}"
        qualified_info = "N/A"
        fund_count = "N/A"
        ai_status = "未知"
        ai_model = "未知"
    
    return HTMLResponse(content=f"""
    <!DOCTYPE html>
    <html lang="zh-CN">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>基金AI智能推荐系统</title>
        <style>
            * {{ margin: 0; padding: 0; box-sizing: border-box; }}
            body {{ 
                font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                min-height: 100vh;
                display: flex;
                align-items: center;
                justify-content: center;
                padding: 20px;
            }}
            .container {{
                background: white;
                border-radius: 20px;
                padding: 40px;
                max-width: 600px;
                width: 100%;
                box-shadow: 0 20px 60px rgba(0,0,0,0.3);
            }}
            h1 {{
                color: #333;
                margin-bottom: 10px;
                font-size: 28px;
            }}
            .subtitle {{
                color: #666;
                margin-bottom: 30px;
            }}
            .status-grid {{
                display: grid;
                grid-template-columns: repeat(2, 1fr);
                gap: 15px;
                margin-bottom: 30px;
            }}
            .status-card {{
                background: #f8f9fa;
                padding: 20px;
                border-radius: 12px;
                text-align: center;
            }}
            .status-card .label {{
                color: #666;
                font-size: 14px;
                margin-bottom: 5px;
            }}
            .status-card .value {{
                color: #333;
                font-size: 20px;
                font-weight: bold;
            }}
            .status-card .value.success {{ color: #28a745; }}
            .status-card .value.warning {{ color: #ffc107; }}
            .links {{
                display: flex;
                gap: 10px;
                flex-wrap: wrap;
            }}
            .links a {{
                flex: 1;
                min-width: 120px;
                padding: 12px 20px;
                background: #667eea;
                color: white;
                text-decoration: none;
                border-radius: 8px;
                text-align: center;
                font-weight: 500;
                transition: background 0.3s;
            }}
            .links a:hover {{
                background: #5a6fd6;
            }}
            .links a.secondary {{
                background: #6c757d;
            }}
            .links a.secondary:hover {{
                background: #5a6268;
            }}
        </style>
    </head>
    <body>
        <div class="container">
            <h1>🤖 基金AI智能推荐系统</h1>
            <p class="subtitle">基于量化指标和AI分析的智能推荐平台 v3.0</p>
            
            <div class="status-grid">
                <div class="status-card">
                    <div class="label">最新快照</div>
                    <div class="value">{snapshot_info}</div>
                </div>
                <div class="status-card">
                    <div class="label">入选基金</div>
                    <div class="value success">{qualified_info} 只</div>
                </div>
                <div class="status-card">
                    <div class="label">基金总数</div>
                    <div class="value">{fund_count} 只</div>
                </div>
                <div class="status-card">
                    <div class="label">AI服务</div>
                    <div class="value {'success' if ai_status == '已配置' else 'warning'}">{ai_status}</div>
                </div>
            </div>
            
            <div class="links">
                <a href="/app">📱 进入应用</a>
                <a href="/docs" class="secondary">📚 API文档</a>
                <a href="/health" class="secondary">💚 健康检查</a>
            </div>
        </div>
    </body>
    </html>
    """)


if __name__ == "__main__":
    import uvicorn
    # 动态判断运行路径
    module_path = "backend.main:app"
    if not (Path.cwd() / "backend").exists() and (Path.cwd() / "main.py").exists():
        module_path = "main:app"
        
    uvicorn.run(
        module_path,
        host="0.0.0.0",
        port=8000,
        reload=settings.DEBUG
    )
