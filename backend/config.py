# backend/config.py
"""
配置管理模块 - 所有配置从环境变量读取
"""
import os
from pathlib import Path
from typing import List, Optional
from pydantic_settings import BaseSettings
from functools import lru_cache


class Settings(BaseSettings):
    """应用配置"""
    
    # === 基础配置 ===
    APP_NAME: str = "基金AI智能推荐系统"
    APP_VERSION: str = "3.0.0"
    DEBUG: bool = False
    
    # === 数据库 ===
    DATABASE_PATH: str = "data/fund_advisor.db"
    
    # === AI 服务 ===
    AI_API_KEY: Optional[str] = None
    AI_BASE_URL: str = "https://api.openai.com/v1"
    AI_MODEL: str = "gpt-4o-mini"
    AI_FALLBACK_MODELS: List[str] = ["gpt-3.5-turbo"]
    AI_TIMEOUT: int = 30
    AI_MAX_RETRIES: int = 2
    
    # === 安全 ===
    ADMIN_TOKEN: Optional[str] = None
    CORS_ORIGINS: List[str] = ["http://localhost:3000", "http://127.0.0.1:3000"]
    
    # === 调度 ===
    AUTO_UPDATE_ENABLED: bool = True
    AUTO_UPDATE_HOUR: int = 2  # 凌晨2点
    AUTO_UPDATE_MINUTE: int = 0
    
    # === 数据获取 ===
    AKSHARE_TIMEOUT: int = 30
    AKSHARE_MAX_RETRIES: int = 3
    AKSHARE_RETRY_DELAY: int = 5
    AKSHARE_RATE_LIMIT: float = 0.5  # 每次请求间隔秒数
    
    # === 计算参数 ===
    DEFAULT_BENCHMARK: str = "000300"  # 沪深300
    MIN_DATA_DAYS: int = 60  # 最少数据天数
    RISK_FREE_RATE: float = 0.025  # 无风险利率
    
    # === 缓存 ===
    AI_CACHE_HOURS: int = 24
    QUERY_CACHE_SECONDS: int = 300
    
    # === 性能优化 ===
    ENABLE_CONCURRENT_FETCH: bool = True
    MAX_CONCURRENT_WORKERS: int = 8
    
    class Config:
        env_file = os.path.join(os.path.dirname(os.path.dirname(__file__)), ".env")
        env_file_encoding = "utf-8"
        extra = "ignore"


@lru_cache()
def get_settings() -> Settings:
    """获取配置单例"""
    return Settings()


def ensure_data_dir():
    """确保数据目录存在"""
    settings = get_settings()
    data_dir = Path(settings.DATABASE_PATH).parent
    data_dir.mkdir(parents=True, exist_ok=True)
