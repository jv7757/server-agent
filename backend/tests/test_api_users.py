"""
用户管理API测试
"""
import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.user import User


@pytest.mark.integration
@pytest.mark.users
class TestUserManagementAPI:
    """用户管理API测试类（仅管理员）"""

    async def test_get_users_list_as_admin(
        self,
        client: AsyncClient,
        admin_headers: dict,
        test_user: User,
        test_admin: User,
    ):
        """测试管理员获取用户列表"""
        response = await client.get(
            "/api/v1/users",
            headers=admin_headers,
        )
        assert response.status_code == 200
        data = response.json()
        assert "total" in data
        assert "items" in data
        assert data["total"] >= 2  # 至少有 test_user 和 test_admin

    async def test_get_users_list_as_regular_user(
        self,
        client: AsyncClient,
        auth_headers: dict,
    ):
        """测试普通用户无法获取用户列表"""
        response = await client.get(
            "/api/v1/users",
            headers=auth_headers,
        )
        assert response.status_code == 403

    async def test_get_users_list_with_filters(
        self,
        client: AsyncClient,
        admin_headers: dict,
        test_user: User,
        test_admin: User,
    ):
        """测试带过滤条件获取用户列表"""
        response = await client.get(
            "/api/v1/users?role=admin",
            headers=admin_headers,
        )
        assert response.status_code == 200
        data = response.json()
        assert all(item["role"] == "admin" for item in data["items"])

    async def test_get_users_list_with_search(
        self,
        client: AsyncClient,
        admin_headers: dict,
        test_user: User,
    ):
        """测试搜索用户"""
        response = await client.get(
            "/api/v1/users?search=testuser",
            headers=admin_headers,
        )
        assert response.status_code == 200
        data = response.json()
        assert len(data["items"]) >= 1
        assert any("testuser" in item["username"].lower() for item in data["items"])

    async def test_get_user_detail_as_admin(
        self,
        client: AsyncClient,
        admin_headers: dict,
        test_user: User,
    ):
        """测试管理员获取用户详情"""
        response = await client.get(
            f"/api/v1/users/{test_user.id}",
            headers=admin_headers,
        )
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == str(test_user.id)
        assert data["username"] == test_user.username

    async def test_get_nonexistent_user(
        self,
        client: AsyncClient,
        admin_headers: dict,
    ):
        """测试获取不存在的用户"""
        response = await client.get(
            "/api/v1/users/00000000-0000-0000-0000-000000000000",
            headers=admin_headers,
        )
        assert response.status_code == 404

    async def test_create_user_as_admin(
        self,
        client: AsyncClient,
        admin_headers: dict,
        random_email: str,
        random_username: str,
    ):
        """测试管理员创建用户"""
        response = await client.post(
            "/api/v1/users",
            headers=admin_headers,
            json={
                "username": random_username,
                "email": random_email,
                "password": "NewPassword123",
                "full_name": "New User",
            },
        )
        assert response.status_code == 201
        data = response.json()
        assert data["username"] == random_username
        assert data["email"] == random_email
        assert data["role"] == "user"  # 默认角色
        assert data["is_active"] is True

    async def test_create_user_duplicate_username(
        self,
        client: AsyncClient,
        admin_headers: dict,
        test_user: User,
    ):
        """测试创建重复用户名的用户"""
        response = await client.post(
            "/api/v1/users",
            headers=admin_headers,
            json={
                "username": test_user.username,  # 重复用户名
                "email": "new@example.com",
                "password": "Password123",
            },
        )
        assert response.status_code == 400

    async def test_update_user_as_admin(
        self,
        client: AsyncClient,
        admin_headers: dict,
        test_user: User,
    ):
        """测试管理员更新用户"""
        new_email = "updated@example.com"
        response = await client.put(
            f"/api/v1/users/{test_user.id}",
            headers=admin_headers,
            json={
                "email": new_email,
                "full_name": "Updated Name",
            },
        )
        assert response.status_code == 200
        data = response.json()
        assert data["email"] == new_email
        assert data["full_name"] == "Updated Name"

    async def test_update_user_password(
        self,
        client: AsyncClient,
        admin_headers: dict,
        test_user: User,
    ):
        """测试更新用户密码"""
        response = await client.put(
            f"/api/v1/users/{test_user.id}",
            headers=admin_headers,
            json={
                "password": "NewPassword456",
            },
        )
        assert response.status_code == 200

        # 验证新密码可以登录
        login_response = await client.post(
            "/api/v1/auth/login",
            json={"username": test_user.username, "password": "NewPassword456"},
        )
        assert login_response.status_code == 200

    async def test_change_user_role(
        self,
        client: AsyncClient,
        admin_headers: dict,
        test_user: User,
    ):
        """测试修改用户角色"""
        response = await client.put(
            f"/api/v1/users/{test_user.id}/role",
            headers=admin_headers,
            json={"role": "admin"},
        )
        assert response.status_code == 200
        data = response.json()
        assert data["role"] == "admin"

    async def test_admin_cannot_change_own_role(
        self,
        client: AsyncClient,
        admin_headers: dict,
        test_admin: User,
    ):
        """测试管理员无法修改自己的角色"""
        response = await client.put(
            f"/api/v1/users/{test_admin.id}/role",
            headers=admin_headers,
            json={"role": "user"},
        )
        assert response.status_code == 400

    async def test_change_user_status(
        self,
        client: AsyncClient,
        admin_headers: dict,
        test_user: User,
    ):
        """测试启用/禁用用户"""
        # 禁用用户
        response = await client.put(
            f"/api/v1/users/{test_user.id}/status",
            headers=admin_headers,
            json={"is_active": False},
        )
        assert response.status_code == 200
        data = response.json()
        assert data["is_active"] is False

        # 重新启用
        response = await client.put(
            f"/api/v1/users/{test_user.id}/status",
            headers=admin_headers,
            json={"is_active": True},
        )
        assert response.status_code == 200
        data = response.json()
        assert data["is_active"] is True

    async def test_admin_cannot_disable_self(
        self,
        client: AsyncClient,
        admin_headers: dict,
        test_admin: User,
    ):
        """测试管理员无法禁用自己"""
        response = await client.put(
            f"/api/v1/users/{test_admin.id}/status",
            headers=admin_headers,
            json={"is_active": False},
        )
        assert response.status_code == 400

    async def test_delete_user_as_admin(
        self,
        client: AsyncClient,
        admin_headers: dict,
        test_user: User,
    ):
        """测试管理员删除用户"""
        response = await client.delete(
            f"/api/v1/users/{test_user.id}",
            headers=admin_headers,
        )
        assert response.status_code == 200

        # 验证用户已删除
        get_response = await client.get(
            f"/api/v1/users/{test_user.id}",
            headers=admin_headers,
        )
        assert get_response.status_code == 404

    async def test_admin_cannot_delete_self(
        self,
        client: AsyncClient,
        admin_headers: dict,
        test_admin: User,
    ):
        """测试管理员无法删除自己"""
        response = await client.delete(
            f"/api/v1/users/{test_admin.id}",
            headers=admin_headers,
        )
        assert response.status_code == 400

    async def test_pagination(
        self,
        client: AsyncClient,
        admin_headers: dict,
    ):
        """测试分页功能"""
        response = await client.get(
            "/api/v1/users?page=1&size=10",
            headers=admin_headers,
        )
        assert response.status_code == 200
        data = response.json()
        assert "page" in data
        assert "size" in data
        assert "total" in data
        assert data["page"] == 1
        assert data["size"] == 10
