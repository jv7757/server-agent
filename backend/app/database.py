"""
数据库连接和会话管理
"""

from typing import AsyncGenerator

from sqlalchemy import create_engine
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import NullPool

from app.config import settings

# 创建异步数据库引擎
# 注意：使用 NullPool 以避免 Celery worker 进程间的连接池问题
engine = create_async_engine(
    settings.database_url,
    echo=settings.debug,
    pool_pre_ping=True,
    poolclass=NullPool,  # 使用 NullPool 避免 fork 问题
)

# 创建异步会话工厂
AsyncSessionLocal = sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autocommit=False,
    autoflush=False,
)

# 创建同步引擎（用于Alembic迁移）
sync_database_url = settings.database_url.replace("+asyncpg", "").replace("+aiomysql", "+pymysql")
sync_engine = create_engine(sync_database_url, echo=settings.debug)

# 创建基础模型类
Base = declarative_base()


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """
    获取数据库会话依赖

    Yields:
        AsyncSession: 数据库会话
    """
    async with AsyncSessionLocal() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()


async def init_db() -> None:
    """初始化数据库（创建所有表）"""
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)


async def close_db() -> None:
    """关闭数据库连接"""
    await engine.dispose()


def get_celery_async_session():
    """
    为 Celery 任务创建独立的异步数据库会话

    使用 NullPool 确保每次都创建新连接，避免事件循环冲突
    """
    celery_engine = create_async_engine(
        settings.database_url,
        echo=settings.debug,
        pool_pre_ping=True,
        poolclass=NullPool,  # 关键：不使用连接池
    )

    return sessionmaker(
        celery_engine,
        class_=AsyncSession,
        expire_on_commit=False,
        autocommit=False,
        autoflush=False,
    )
