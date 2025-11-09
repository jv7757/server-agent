"""
服务器管理API测试
"""

import pytest
from httpx import AsyncClient

from app.models.server import Server
from app.models.user import User


@pytest.mark.server
@pytest.mark.integration
class TestServerAPI:
    """服务器管理API测试类"""

    async def test_create_server_success(self, client: AsyncClient, auth_headers: dict):
        """测试创建服务器成功"""
        response = await client.post(
            "/api/v1/servers",
            headers=auth_headers,
            json={
                "name": "my-server",
                "host": "192.168.1.100",
                "port": 22,
                "ssh_username": "root",
                "ssh_password": "password123",
                "description": "My test server",
                "tags": ["production", "web"],
            },
        )
        assert response.status_code == 201
        data = response.json()
        assert data["name"] == "my-server"
        assert data["host"] == "192.168.1.100"
        assert data["port"] == 22
        assert "ssh_password" not in data  # 密码不应返回
        assert data["tags"] == ["production", "web"]

    async def test_create_server_with_ssh_key(self, client: AsyncClient, auth_headers: dict):
        """测试使用SSH密钥创建服务器"""
        response = await client.post(
            "/api/v1/servers",
            headers=auth_headers,
            json={
                "name": "key-server",
                "host": "192.168.1.101",
                "port": 22,
                "ssh_username": "ubuntu",
                "ssh_key": "-----BEGIN RSA PRIVATE KEY-----\nMIIEpAIBAAKCAQEA...\n-----END RSA PRIVATE KEY-----",
                "description": "Server with SSH key",
            },
        )
        assert response.status_code == 201
        data = response.json()
        assert "ssh_key" not in data  # 密钥不应返回

    async def test_create_server_unauthorized(self, client: AsyncClient):
        """测试未授权创建服务器"""
        response = await client.post(
            "/api/v1/servers",
            json={
                "name": "my-server",
                "host": "192.168.1.100",
                "port": 22,
                "ssh_username": "root",
                "ssh_password": "password123",
            },
        )
        assert response.status_code == 403

    async def test_create_server_missing_credentials(self, client: AsyncClient, auth_headers: dict):
        """测试创建服务器缺少凭证"""
        response = await client.post(
            "/api/v1/servers",
            headers=auth_headers,
            json={
                "name": "my-server",
                "host": "192.168.1.100",
                "port": 22,
                "ssh_username": "root",
                # 缺少ssh_password或ssh_key
            },
        )
        assert response.status_code == 400

    async def test_get_servers(
        self, client: AsyncClient, auth_headers: dict, multiple_servers: list[Server]
    ):
        """测试获取服务器列表"""
        response = await client.get("/api/v1/servers", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 5
        assert len(data["items"]) == 5
        assert data["page"] == 1
        assert data["size"] == 20

    async def test_get_servers_pagination(
        self, client: AsyncClient, auth_headers: dict, multiple_servers: list[Server]
    ):
        """测试服务器列表分页"""
        response = await client.get("/api/v1/servers?page=1&size=2", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 5
        assert len(data["items"]) == 2
        assert data["page"] == 1
        assert data["size"] == 2

    async def test_get_servers_filter_by_status(
        self, client: AsyncClient, auth_headers: dict, multiple_servers: list[Server]
    ):
        """测试按状态筛选服务器"""
        response = await client.get("/api/v1/servers?status=online", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 3  # 有3个online服务器
        for item in data["items"]:
            assert item["status"] == "online"

    async def test_get_servers_filter_by_tags(
        self, client: AsyncClient, auth_headers: dict, multiple_servers: list[Server]
    ):
        """测试按标签筛选服务器"""
        response = await client.get("/api/v1/servers?tags=production", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 2  # 有2个production服务器
        for item in data["items"]:
            assert "production" in item["tags"]

    async def test_get_servers_search(
        self, client: AsyncClient, auth_headers: dict, multiple_servers: list[Server]
    ):
        """测试搜索服务器"""
        response = await client.get("/api/v1/servers?search=server-1", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 1
        assert data["items"][0]["name"] == "server-1"

    async def test_get_server_detail(
        self, client: AsyncClient, auth_headers: dict, test_server: Server
    ):
        """测试获取服务器详情"""
        response = await client.get(f"/api/v1/servers/{test_server.id}", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == str(test_server.id)
        assert data["name"] == test_server.name
        assert data["host"] == test_server.host

    async def test_get_server_not_found(self, client: AsyncClient, auth_headers: dict):
        """测试获取不存在的服务器"""
        from uuid import uuid4

        response = await client.get(f"/api/v1/servers/{uuid4()}", headers=auth_headers)
        assert response.status_code == 404

    async def test_update_server(
        self, client: AsyncClient, auth_headers: dict, test_server: Server
    ):
        """测试更新服务器"""
        response = await client.put(
            f"/api/v1/servers/{test_server.id}",
            headers=auth_headers,
            json={
                "name": "updated-server",
                "description": "Updated description",
                "tags": ["updated"],
            },
        )
        assert response.status_code == 200
        data = response.json()
        assert data["name"] == "updated-server"
        assert data["description"] == "Updated description"
        assert data["tags"] == ["updated"]

    async def test_update_server_not_owner(
        self, client: AsyncClient, viewer_headers: dict, test_server: Server
    ):
        """测试非所有者更新服务器"""
        response = await client.put(
            f"/api/v1/servers/{test_server.id}",
            headers=viewer_headers,
            json={"name": "hacked-server"},
        )
        assert response.status_code == 404  # 找不到服务器（因为不是所有者）

    async def test_delete_server(
        self, client: AsyncClient, auth_headers: dict, test_server: Server
    ):
        """测试删除服务器"""
        response = await client.delete(f"/api/v1/servers/{test_server.id}", headers=auth_headers)
        assert response.status_code == 204

        # 验证服务器已删除
        get_response = await client.get(f"/api/v1/servers/{test_server.id}", headers=auth_headers)
        assert get_response.status_code == 404

    async def test_delete_server_not_owner(
        self, client: AsyncClient, viewer_headers: dict, test_server: Server
    ):
        """测试非所有者删除服务器"""
        response = await client.delete(f"/api/v1/servers/{test_server.id}", headers=viewer_headers)
        assert response.status_code == 404

    async def test_admin_can_access_all_servers(
        self, client: AsyncClient, admin_headers: dict, test_server: Server
    ):
        """测试管理员可以访问所有服务器"""
        response = await client.get(f"/api/v1/servers/{test_server.id}", headers=admin_headers)
        assert response.status_code == 200
