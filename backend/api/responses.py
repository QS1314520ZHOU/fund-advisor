# backend/api/responses.py
from typing import Any, Optional, Generic, TypeVar, List, Dict
from pydantic import BaseModel

DataT = TypeVar("DataT")

class ApiResponse(BaseModel, Generic[DataT]):
    """
    统一 API 响应格式
    """
    success: bool = True
    data: Optional[DataT] = None
    error: Optional[str] = None
    message: Optional[str] = None
    meta: Optional[Dict[str, Any]] = None # 分页等元数据

    class Config:
        arbitrary_types_allowed = True

def success_response(data: Any = None, message: str = None, meta: Dict[str, Any] = None) -> ApiResponse:
    return ApiResponse(success=True, data=data, message=message, meta=meta)

def error_response(error: str, message: str = None) -> ApiResponse:
    return ApiResponse(success=False, error=error, message=message)
