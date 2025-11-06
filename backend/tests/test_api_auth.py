"""
认证API测试
"""
import pytest
from httpx import AsyncClient

from app.models.user import User


@pytest.mark.auth
@pytest.mark.integration
class TestAuthAPI:
    """认证API测试类"""

    async def test_register_success(self, client: AsyncClient):
        """测试用户注册成功"""
        response = await client.post(
            "/api/v1/auth/register",
            json={
                "username": "newuser",
                "email": "newuser@example.com",
                "password": "Password123!",
            },
        )
        assert response.status_code == 201
        data = response.json()
        assert data["username"] == "newuser"
        assert data["email"] == "newuser@example.com"
        assert "id" in data
        assert "password" not in data

    async def test_register_duplicate_username(
        self, client: AsyncClient, test_user: User
    ):
        """测试注册重复用户名"""
        response = await client.post(
            "/api/v1/auth/register",
            json={
                "username": "testuser",  # 已存在
                "email": "another@example.com",
                "password": "Password123!",
            },
        )
        assert response.status_code == 400
        assert "already registered" in response.json()["detail"].lower()

    async def test_register_duplicate_email(
        self, client: AsyncClient, test_user: User
    ):
        """测试注册重复邮箱"""
        response = await client.post(
            "/api/v1/auth/register",
            json={
                "username": "anotheruser",
                "email": "testuser@example.com",  # 已存在
                "password": "Password123!",
            },
        )
        assert response.status_code == 400
        assert "already registered" in response.json()["detail"].lower()

    async def test_register_weak_password(self, client: AsyncClient):
        """测试弱密码注册"""
        response = await client.post(
            "/api/v1/auth/register",
            json={
                "username": "newuser",
                "email": "newuser@example.com",
                "password": "123",  # 太短
            },
        )
        assert response.status_code == 422  # Validation error

    async def test_login_success(self, client: AsyncClient, test_user: User):
        """测试登录成功"""
        response = await client.post(
            "/api/v1/auth/login",
            json={"username": "testuser", "password": "testpass123"},
        )
        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        assert "refresh_token" in data
        assert data["token_type"] == "bearer"
        assert "user" in data
        assert data["user"]["username"] == "testuser"

    async def test_login_wrong_password(self, client: AsyncClient, test_user: User):
        """测试错误密码登录"""
        response = await client.post(
            "/api/v1/auth/login",
            json={"username": "testuser", "password": "wrongpassword"},
        )
        assert response.status_code == 401
        assert "incorrect" in response.json()["detail"].lower()

    async def test_login_nonexistent_user(self, client: AsyncClient):
        """测试不存在的用户登录"""
        response = await client.post(
            "/api/v1/auth/login",
            json={"username": "nonexistent", "password": "password123"},
        )
        assert response.status_code == 401

    async def test_get_current_user(self, client: AsyncClient, auth_headers: dict):
        """测试获取当前用户信息"""
        response = await client.get("/api/v1/auth/me", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert data["username"] == "testuser"
        assert data["email"] == "testuser@example.com"

    async def test_get_current_user_unauthorized(self, client: AsyncClient):
        """测试未授权访问当前用户"""
        response = await client.get("/api/v1/auth/me")
        assert response.status_code == 403  # No auth header

    async def test_get_current_user_invalid_token(self, client: AsyncClient):
        """测试无效token访问"""
        response = await client.get(
            "/api/v1/auth/me", headers={"Authorization": "Bearer invalidtoken"}
        )
        assert response.status_code == 401

    async def test_refresh_token(self, client: AsyncClient, test_user: User):
        """测试刷新token"""
        # 先登录获取refresh_token
        login_response = await client.post(
            "/api/v1/auth/login",
            json={"username": "testuser", "password": "testpass123"},
        )
        refresh_token = login_response.json()["refresh_token"]

        # 使用refresh_token获取新的access_token
        response = await client.post(
            "/api/v1/auth/refresh", json={"refresh_token": refresh_token}
        )
        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        assert data["token_type"] == "bearer"

    async def test_refresh_token_invalid(self, client: AsyncClient):
        """测试无效refresh_token"""
        response = await client.post(
            "/api/v1/auth/refresh", json={"refresh_token": "invalidtoken"}
        )
        assert response.status_code == 401

    async def test_update_profile(self, client: AsyncClient, auth_headers: dict):
        """测试更新用户资料"""
        response = await client.put(
            "/api/v1/auth/me",
            headers=auth_headers,
            json={"email": "newemail@example.com"},
        )
        assert response.status_code == 200
        data = response.json()
        assert data["email"] == "newemail@example.com"

    async def test_change_password(self, client: AsyncClient, auth_headers: dict):
        """测试修改密码"""
        response = await client.post(
            "/api/v1/auth/change-password",
            headers=auth_headers,
            json={
                "old_password": "testpass123",
                "new_password": "NewPassword123!",
            },
        )
        assert response.status_code == 200

        # 验证新密码可以登录
        login_response = await client.post(
            "/api/v1/auth/login",
            json={"username": "testuser", "password": "NewPassword123!"},
        )
        assert login_response.status_code == 200

    async def test_change_password_wrong_old_password(
        self, client: AsyncClient, auth_headers: dict
    ):
        """测试使用错误的旧密码修改密码"""
        response = await client.post(
            "/api/v1/auth/change-password",
            headers=auth_headers,
            json={
                "old_password": "wrongpassword",
                "new_password": "NewPassword123!",
            },
        )
        assert response.status_code == 400
