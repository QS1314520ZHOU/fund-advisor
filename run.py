#!/usr/bin/env python3
"""启动脚本"""
import uvicorn
from backend.config import get_settings

if __name__ == "__main__":
    settings = get_settings()
    
    print("\n" + "="*60)
    print("🚀 基金AI智能推荐系统 v3.0")
    print("="*60)
    print(f"🌐 访问: http://localhost:8000")
    print(f"📚 文档: http://localhost:8000/docs")
    print("="*60 + "\n")
    
    uvicorn.run(
        "backend.main:app",
        host="0.0.0.0",
        port=8000,
        reload=settings.DEBUG
    )
