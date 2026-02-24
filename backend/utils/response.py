# backend/utils/response.py
"""
统一 API 响应格式
"""

import datetime
from typing import Any, Optional, List, Dict
from pydantic import BaseModel, Field


class APIResponse(BaseModel):
    """标准化 API 响应"""
    success: bool = True
    code: int = 200
    message: str = "OK"
    data: Optional[Any] = None
    error: Optional[str] = None
    timestamp: str = Field(default_factory=lambda: datetime.datetime.now().isoformat())
    
    class Config:
        json_encoders = {
            datetime.datetime: lambda v: v.isoformat()
        }


def success_response(
    data: Any = None, 
    message: str = "OK",
    code: int = 200
) -> dict:
    """成功响应"""
    return {
        'success': True,
        'code': code,
        'message': message,
        'data': data,
        'timestamp': datetime.datetime.now().isoformat()
    }


def error_response(
    error: str,
    message: str = "请求失败",
    code: int = 500,
    data: Any = None
) -> dict:
    """错误响应"""
    return {
        'success': False,
        'code': code,
        'message': message,
        'error': error,
        'data': data,
        'timestamp': datetime.datetime.now().isoformat()
    }


def paginated_response(
    items: List[Any],
    total: int,
    page: int = 1,
    page_size: int = 20,
    message: str = "OK"
) -> dict:
    """分页响应"""
    return {
        'success': True,
        'code': 200,
        'message': message,
        'data': {
            'items': items,
            'total': total,
            'page': page,
            'page_size': page_size,
            'total_pages': (total + page_size - 1) // page_size
        },
        'timestamp': datetime.datetime.now().isoformat()
    }
