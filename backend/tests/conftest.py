"""
Pytest配置和共享fixtures
"""

import asyncio
from typing import AsyncGenerator, Generator
from uuid import uuid4

import pytest
from faker import Faker
from httpx import AsyncClient
from sqlalchemy import create_engine
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import NullPool

from app.config import settings
from app.core.security import get_password_hash
from app.database import Base, get_db
from app.main import app
from app.models.server import Server
from app.models.user import User

# 创建Faker实例
fake = Faker()

# 测试数据库URL（使用内存SQLite）
TEST_DATABASE_URL = "sqlite+aiosqlite:///:memory:"


@pytest.fixture(scope="session")
def event_loop() -> Generator:
    """创建事件循环"""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture(scope="function")
async def test_db() -> AsyncGenerator[AsyncSession, None]:
    """
    创建测试数据库会话

    每个测试函数使用独立的数据库会话
    """
    # 创建异步引擎
    engine = create_async_engine(
        TEST_DATABASE_URL,
        echo=False,
        poolclass=NullPool,
    )

    # 创建所有表
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    # 创建会话
    async_session = sessionmaker(
        engine,
        class_=AsyncSession,
        expire_on_commit=False,
    )

    async with async_session() as session:
        yield session

    # 清理：删除所有表
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)

    await engine.dispose()


@pytest.fixture
async def client(test_db: AsyncSession) -> AsyncGenerator[AsyncClient, None]:
    """
    创建测试HTTP客户端

    覆盖应用的数据库依赖为测试数据库
    """

    async def override_get_db():
        yield test_db

    app.dependency_overrides[get_db] = override_get_db

    async with AsyncClient(app=app, base_url="http://test") as ac:
        yield ac

    app.dependency_overrides.clear()


# ========== 测试数据Fixtures ==========


@pytest.fixture
async def test_user(test_db: AsyncSession) -> User:
    """创建测试用户"""
    user = User(
        username="testuser",
        email="testuser@example.com",
        hashed_password=get_password_hash("testpass123"),
        role="user",
        is_active=True,
    )
    test_db.add(user)
    await test_db.commit()
    await test_db.refresh(user)
    return user


@pytest.fixture
async def test_admin(test_db: AsyncSession) -> User:
    """创建测试管理员"""
    admin = User(
        username="admin",
        email="admin@example.com",
        hashed_password=get_password_hash("adminpass123"),
        role="admin",
        is_active=True,
    )
    test_db.add(admin)
    await test_db.commit()
    await test_db.refresh(admin)
    return admin


@pytest.fixture
async def test_viewer(test_db: AsyncSession) -> User:
    """创建测试查看者"""
    viewer = User(
        username="viewer",
        email="viewer@example.com",
        hashed_password=get_password_hash("viewerpass123"),
        role="viewer",
        is_active=True,
    )
    test_db.add(viewer)
    await test_db.commit()
    await test_db.refresh(viewer)
    return viewer


@pytest.fixture
async def test_server(test_db: AsyncSession, test_user: User) -> Server:
    """创建测试服务器"""
    from app.core.security import encrypt_ssh_credential

    server = Server(
        name="test-server",
        host="192.168.1.100",
        port=22,
        ssh_username="root",
        ssh_password=encrypt_ssh_credential("password123"),
        owner_id=test_user.id,
        description="Test server",
        tags=["test", "development"],
        status="unknown",
    )
    test_db.add(server)
    await test_db.commit()
    await test_db.refresh(server)
    return server


@pytest.fixture
async def multiple_servers(test_db: AsyncSession, test_user: User) -> list[Server]:
    """创建多个测试服务器"""
    from app.core.security import encrypt_ssh_credential

    servers = []
    for i in range(5):
        server = Server(
            name=f"server-{i}",
            host=f"192.168.1.{100 + i}",
            port=22,
            ssh_username="root",
            ssh_password=encrypt_ssh_credential(f"password{i}"),
            owner_id=test_user.id,
            description=f"Test server {i}",
            tags=["test"] if i % 2 == 0 else ["production"],
            status="online" if i % 2 == 0 else "offline",
        )
        test_db.add(server)
        servers.append(server)

    await test_db.commit()

    for server in servers:
        await test_db.refresh(server)

    return servers


# ========== 认证Fixtures ==========


@pytest.fixture
async def user_token(client: AsyncClient, test_user: User) -> str:
    """获取用户访问令牌"""
    response = await client.post(
        "/api/v1/auth/login",
        json={"username": "testuser", "password": "testpass123"},
    )
    assert response.status_code == 200
    data = response.json()
    return data["access_token"]


@pytest.fixture
async def admin_token(client: AsyncClient, test_admin: User) -> str:
    """获取管理员访问令牌"""
    response = await client.post(
        "/api/v1/auth/login",
        json={"username": "admin", "password": "adminpass123"},
    )
    assert response.status_code == 200
    data = response.json()
    return data["access_token"]


@pytest.fixture
async def viewer_token(client: AsyncClient, test_viewer: User) -> str:
    """获取查看者访问令牌"""
    response = await client.post(
        "/api/v1/auth/login",
        json={"username": "viewer", "password": "viewerpass123"},
    )
    assert response.status_code == 200
    data = response.json()
    return data["access_token"]


@pytest.fixture
def auth_headers(user_token: str) -> dict:
    """用户认证请求头"""
    return {"Authorization": f"Bearer {user_token}"}


@pytest.fixture
def admin_headers(admin_token: str) -> dict:
    """管理员认证请求头"""
    return {"Authorization": f"Bearer {admin_token}"}


@pytest.fixture
def viewer_headers(viewer_token: str) -> dict:
    """查看者认证请求头"""
    return {"Authorization": f"Bearer {viewer_token}"}


# ========== 工具Fixtures ==========


@pytest.fixture
def faker_instance() -> Faker:
    """Faker实例"""
    return fake


@pytest.fixture
def random_email() -> str:
    """生成随机邮箱"""
    return fake.email()


@pytest.fixture
def random_username() -> str:
    """生成随机用户名"""
    return fake.user_name()


@pytest.fixture
def random_password() -> str:
    """生成随机密码"""
    return fake.password(length=12)
