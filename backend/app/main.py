"""
FastAPI应用主入口
"""
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.config import settings
from app.database import close_db, init_db


@asynccontextmanager
async def lifespan(app: FastAPI):
    """应用生命周期管理"""
    # 启动时执行
    if settings.is_development:
        await init_db()  # 开发环境自动创建表
    yield
    # 关闭时执行
    await close_db()


# 创建FastAPI应用
app = FastAPI(
    title=settings.app_name,
    version=settings.app_version,
    description="现代化服务器管理系统 API",
    docs_url="/docs" if settings.debug else None,
    redoc_url="/redoc" if settings.debug else None,
    lifespan=lifespan,
)

# 配置CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.allowed_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# 健康检查端点
@app.get("/", tags=["Health"])
async def root():
    """根路径 - 健康检查"""
    return {
        "app": settings.app_name,
        "version": settings.app_version,
        "status": "running",
        "environment": settings.env,
    }


@app.get("/health", tags=["Health"])
async def health_check():
    """健康检查"""
    return {"status": "healthy"}


# 异常处理器
@app.exception_handler(Exception)
async def global_exception_handler(request, exc):
    """全局异常处理"""
    return JSONResponse(
        status_code=500,
        content={
            "detail": "Internal server error",
            "message": str(exc) if settings.debug else "An error occurred",
        },
    )


# 导入并注册路由
from app.api.v1 import audit_logs, auth, chat, execute, metrics, permissions, servers, users, websocket

app.include_router(auth.router, prefix="/api/v1/auth", tags=["Authentication"])
app.include_router(users.router, prefix="/api/v1", tags=["User Management"])
app.include_router(servers.router, prefix="/api/v1/servers", tags=["Servers"])
app.include_router(metrics.router, prefix="/api/v1/metrics", tags=["Metrics"])
app.include_router(execute.router, prefix="/api/v1/execute", tags=["Command Execution"])
app.include_router(chat.router, prefix="/api/v1/chat", tags=["AI Chat"])
app.include_router(permissions.router, prefix="/api/v1/permissions", tags=["Permissions"])
app.include_router(audit_logs.router, prefix="/api/v1", tags=["Audit Logs"])
app.include_router(websocket.router, prefix="/api/v1/ws", tags=["WebSocket"])


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=settings.debug,
        log_level=settings.log_level.lower(),
    )
