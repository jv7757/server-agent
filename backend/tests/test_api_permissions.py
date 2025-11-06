"""
权限管理API测试
"""
import pytest
from httpx import AsyncClient

from app.models.server import Server
from app.models.user import User


@pytest.mark.permission
@pytest.mark.integration
class TestPermissionAPI:
    """权限管理API测试类"""

    async def test_grant_permission_success(
        self,
        client: AsyncClient,
        auth_headers: dict,
        test_server: Server,
        test_viewer: User,
    ):
        """测试授予权限成功"""
        response = await client.post(
            "/api/v1/permissions/grant",
            headers=auth_headers,
            json={
                "server_id": str(test_server.id),
                "target_user_id": str(test_viewer.id),
                "permissions": ["read", "execute"],
            },
        )
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert "read" in data["permission"]["permissions"]
        assert "execute" in data["permission"]["permissions"]
        assert "write" not in data["permission"]["permissions"]

    async def test_grant_permission_invalid_permission(
        self,
        client: AsyncClient,
        auth_headers: dict,
        test_server: Server,
        test_viewer: User,
    ):
        """测试授予无效权限"""
        response = await client.post(
            "/api/v1/permissions/grant",
            headers=auth_headers,
            json={
                "server_id": str(test_server.id),
                "target_user_id": str(test_viewer.id),
                "permissions": ["invalid_permission"],
            },
        )
        assert response.status_code == 422  # Validation error

    async def test_grant_permission_not_owner(
        self,
        client: AsyncClient,
        viewer_headers: dict,
        test_server: Server,
        test_admin: User,
    ):
        """测试非所有者授予权限"""
        response = await client.post(
            "/api/v1/permissions/grant",
            headers=viewer_headers,
            json={
                "server_id": str(test_server.id),
                "target_user_id": str(test_admin.id),
                "permissions": ["read"],
            },
        )
        assert response.status_code == 403

    async def test_update_existing_permission(
        self,
        client: AsyncClient,
        auth_headers: dict,
        test_server: Server,
        test_viewer: User,
    ):
        """测试更新已存在的权限"""
        # 先授予read权限
        await client.post(
            "/api/v1/permissions/grant",
            headers=auth_headers,
            json={
                "server_id": str(test_server.id),
                "target_user_id": str(test_viewer.id),
                "permissions": ["read"],
            },
        )

        # 更新为read + write权限
        response = await client.post(
            "/api/v1/permissions/grant",
            headers=auth_headers,
            json={
                "server_id": str(test_server.id),
                "target_user_id": str(test_viewer.id),
                "permissions": ["read", "write"],
            },
        )
        assert response.status_code == 200
        data = response.json()
        assert "read" in data["permission"]["permissions"]
        assert "write" in data["permission"]["permissions"]

    async def test_revoke_permission_success(
        self,
        client: AsyncClient,
        auth_headers: dict,
        test_server: Server,
        test_viewer: User,
    ):
        """测试撤销权限成功"""
        # 先授予权限
        await client.post(
            "/api/v1/permissions/grant",
            headers=auth_headers,
            json={
                "server_id": str(test_server.id),
                "target_user_id": str(test_viewer.id),
                "permissions": ["read"],
            },
        )

        # 撤销权限
        response = await client.post(
            "/api/v1/permissions/revoke",
            headers=auth_headers,
            json={
                "server_id": str(test_server.id),
                "target_user_id": str(test_viewer.id),
            },
        )
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True

    async def test_revoke_nonexistent_permission(
        self,
        client: AsyncClient,
        auth_headers: dict,
        test_server: Server,
        test_viewer: User,
    ):
        """测试撤销不存在的权限"""
        response = await client.post(
            "/api/v1/permissions/revoke",
            headers=auth_headers,
            json={
                "server_id": str(test_server.id),
                "target_user_id": str(test_viewer.id),
            },
        )
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is False

    async def test_check_permission(
        self,
        client: AsyncClient,
        auth_headers: dict,
        test_server: Server,
    ):
        """测试检查权限"""
        # 服务器所有者应该有所有权限
        response = await client.post(
            "/api/v1/permissions/check",
            headers=auth_headers,
            json={
                "server_id": str(test_server.id),
                "required_permission": "admin",
            },
        )
        assert response.status_code == 200
        data = response.json()
        assert data["has_permission"] is True

    async def test_check_permission_no_access(
        self,
        client: AsyncClient,
        viewer_headers: dict,
        test_server: Server,
    ):
        """测试检查无权限"""
        response = await client.post(
            "/api/v1/permissions/check",
            headers=viewer_headers,
            json={
                "server_id": str(test_server.id),
                "required_permission": "read",
            },
        )
        assert response.status_code == 200
        data = response.json()
        assert data["has_permission"] is False

    async def test_get_user_permissions(
        self,
        client: AsyncClient,
        viewer_headers: dict,
        test_server: Server,
        test_user: User,
        test_viewer: User,
    ):
        """测试获取用户权限列表"""
        # 先给viewer授予一些权限
        from httpx import AsyncClient as AC

        # 使用服务器所有者的token授予权限
        login_response = await client.post(
            "/api/v1/auth/login",
            json={"username": "testuser", "password": "testpass123"},
        )
        owner_token = login_response.json()["access_token"]
        owner_headers = {"Authorization": f"Bearer {owner_token}"}

        await client.post(
            "/api/v1/permissions/grant",
            headers=owner_headers,
            json={
                "server_id": str(test_server.id),
                "target_user_id": str(test_viewer.id),
                "permissions": ["read"],
            },
        )

        # 获取viewer的权限列表
        response = await client.get(
            "/api/v1/permissions/user/permissions", headers=viewer_headers
        )
        assert response.status_code == 200
        data = response.json()
        assert data["total"] >= 1
        assert len(data["items"]) >= 1

    async def test_get_server_permissions(
        self,
        client: AsyncClient,
        auth_headers: dict,
        test_server: Server,
        test_viewer: User,
    ):
        """测试获取服务器权限列表"""
        # 先授予权限
        await client.post(
            "/api/v1/permissions/grant",
            headers=auth_headers,
            json={
                "server_id": str(test_server.id),
                "target_user_id": str(test_viewer.id),
                "permissions": ["read", "write"],
            },
        )

        # 获取服务器的权限列表
        response = await client.get(
            f"/api/v1/permissions/server/{test_server.id}", headers=auth_headers
        )
        assert response.status_code == 200
        data = response.json()
        assert data["total"] >= 1

    async def test_get_server_permissions_not_authorized(
        self,
        client: AsyncClient,
        viewer_headers: dict,
        test_server: Server,
    ):
        """测试未授权获取服务器权限列表"""
        response = await client.get(
            f"/api/v1/permissions/server/{test_server.id}", headers=viewer_headers
        )
        assert response.status_code == 403

    async def test_get_accessible_servers(
        self,
        client: AsyncClient,
        auth_headers: dict,
        test_server: Server,
    ):
        """测试获取可访问服务器列表"""
        response = await client.get(
            "/api/v1/permissions/user/accessible-servers", headers=auth_headers
        )
        assert response.status_code == 200
        data = response.json()
        assert data["count"] >= 1
        assert str(test_server.id) in data["server_ids"]

    async def test_get_accessible_servers_with_min_permission(
        self,
        client: AsyncClient,
        viewer_headers: dict,
        test_server: Server,
        test_viewer: User,
        auth_headers: dict,
    ):
        """测试按最小权限获取可访问服务器"""
        # 授予execute权限
        await client.post(
            "/api/v1/permissions/grant",
            headers=auth_headers,
            json={
                "server_id": str(test_server.id),
                "target_user_id": str(test_viewer.id),
                "permissions": ["read", "execute"],
            },
        )

        # 查询需要execute权限的服务器
        response = await client.get(
            "/api/v1/permissions/user/accessible-servers?min_permission=execute",
            headers=viewer_headers,
        )
        assert response.status_code == 200
        data = response.json()
        assert str(test_server.id) in data["server_ids"]

        # 查询需要admin权限的服务器（viewer没有）
        response = await client.get(
            "/api/v1/permissions/user/accessible-servers?min_permission=admin",
            headers=viewer_headers,
        )
        assert response.status_code == 200
        data = response.json()
        assert str(test_server.id) not in data["server_ids"]

    async def test_admin_has_all_permissions(
        self,
        client: AsyncClient,
        admin_headers: dict,
        test_server: Server,
    ):
        """测试管理员拥有所有权限"""
        response = await client.post(
            "/api/v1/permissions/check",
            headers=admin_headers,
            json={
                "server_id": str(test_server.id),
                "required_permission": "admin",
            },
        )
        assert response.status_code == 200
        data = response.json()
        assert data["has_permission"] is True
