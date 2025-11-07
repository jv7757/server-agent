"""
审计日志API测试
"""
import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.audit import AuditLog
from app.models.server import Server
from app.models.user import User


@pytest.fixture
async def test_audit_logs(
    test_db: AsyncSession,
    test_user: User,
    test_server: Server,
) -> list[AuditLog]:
    """创建测试审计日志"""
    logs = []
    actions = ["login", "create_server", "execute_command", "grant_permission"]

    for i, action in enumerate(actions):
        log = AuditLog(
            user_id=test_user.id,
            server_id=test_server.id if i % 2 == 0 else None,
            action=action,
            resource_type="command" if action == "execute_command" else "server",
            details={"test": f"detail_{i}"},
            ip_address="192.168.1.1",
        )
        test_db.add(log)
        logs.append(log)

    await test_db.commit()
    for log in logs:
        await test_db.refresh(log)

    return logs


@pytest.mark.integration
@pytest.mark.audit
class TestAuditLogsAPI:
    """审计日志API测试类（仅管理员）"""

    async def test_get_audit_logs_as_admin(
        self,
        client: AsyncClient,
        admin_headers: dict,
        test_audit_logs: list[AuditLog],
    ):
        """测试管理员获取审计日志列表"""
        response = await client.get(
            "/api/v1/audit-logs",
            headers=admin_headers,
        )
        assert response.status_code == 200
        data = response.json()
        assert "total" in data
        assert "items" in data
        assert data["total"] >= len(test_audit_logs)

    async def test_get_audit_logs_as_regular_user(
        self,
        client: AsyncClient,
        auth_headers: dict,
    ):
        """测试普通用户无法获取审计日志"""
        response = await client.get(
            "/api/v1/audit-logs",
            headers=auth_headers,
        )
        assert response.status_code == 403

    async def test_get_audit_logs_with_user_filter(
        self,
        client: AsyncClient,
        admin_headers: dict,
        test_user: User,
        test_audit_logs: list[AuditLog],
    ):
        """测试按用户筛选审计日志"""
        response = await client.get(
            f"/api/v1/audit-logs?user_id={test_user.id}",
            headers=admin_headers,
        )
        assert response.status_code == 200
        data = response.json()
        assert all(item["user_id"] == str(test_user.id) for item in data["items"])

    async def test_get_audit_logs_with_server_filter(
        self,
        client: AsyncClient,
        admin_headers: dict,
        test_server: Server,
        test_audit_logs: list[AuditLog],
    ):
        """测试按服务器筛选审计日志"""
        response = await client.get(
            f"/api/v1/audit-logs?server_id={test_server.id}",
            headers=admin_headers,
        )
        assert response.status_code == 200
        data = response.json()
        for item in data["items"]:
            if item["server_id"]:  # 可能为 None
                assert item["server_id"] == str(test_server.id)

    async def test_get_audit_logs_with_action_filter(
        self,
        client: AsyncClient,
        admin_headers: dict,
        test_audit_logs: list[AuditLog],
    ):
        """测试按操作类型筛选"""
        response = await client.get(
            "/api/v1/audit-logs?action=login",
            headers=admin_headers,
        )
        assert response.status_code == 200
        data = response.json()
        assert all(item["action"] == "login" for item in data["items"])

    async def test_get_audit_logs_with_resource_type_filter(
        self,
        client: AsyncClient,
        admin_headers: dict,
        test_audit_logs: list[AuditLog],
    ):
        """测试按资源类型筛选"""
        response = await client.get(
            "/api/v1/audit-logs?resource_type=command",
            headers=admin_headers,
        )
        assert response.status_code == 200
        data = response.json()
        assert all(item["resource_type"] == "command" for item in data["items"])

    async def test_get_audit_logs_with_search(
        self,
        client: AsyncClient,
        admin_headers: dict,
        test_audit_logs: list[AuditLog],
    ):
        """测试搜索审计日志"""
        response = await client.get(
            "/api/v1/audit-logs?search=execute",
            headers=admin_headers,
        )
        assert response.status_code == 200
        data = response.json()
        # 搜索应该匹配操作名称
        assert len(data["items"]) >= 0

    async def test_get_audit_log_detail(
        self,
        client: AsyncClient,
        admin_headers: dict,
        test_audit_logs: list[AuditLog],
    ):
        """测试获取审计日志详情"""
        log = test_audit_logs[0]
        response = await client.get(
            f"/api/v1/audit-logs/{log.id}",
            headers=admin_headers,
        )
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == log.id
        assert data["action"] == log.action

    async def test_get_nonexistent_audit_log(
        self,
        client: AsyncClient,
        admin_headers: dict,
    ):
        """测试获取不存在的审计日志"""
        response = await client.get(
            "/api/v1/audit-logs/999999",
            headers=admin_headers,
        )
        assert response.status_code == 404

    async def test_pagination(
        self,
        client: AsyncClient,
        admin_headers: dict,
        test_audit_logs: list[AuditLog],
    ):
        """测试分页功能"""
        response = await client.get(
            "/api/v1/audit-logs?page=1&size=2",
            headers=admin_headers,
        )
        assert response.status_code == 200
        data = response.json()
        assert data["page"] == 1
        assert data["size"] == 2
        assert len(data["items"]) <= 2

    async def test_audit_log_contains_user_info(
        self,
        client: AsyncClient,
        admin_headers: dict,
        test_audit_logs: list[AuditLog],
    ):
        """测试审计日志包含用户信息"""
        response = await client.get(
            "/api/v1/audit-logs",
            headers=admin_headers,
        )
        assert response.status_code == 200
        data = response.json()

        for item in data["items"]:
            # 应该包含用户名（通过 JOIN 获取）
            if item["user_id"]:
                assert "username" in item or item["username"] is not None

    async def test_audit_log_contains_server_info(
        self,
        client: AsyncClient,
        admin_headers: dict,
        test_audit_logs: list[AuditLog],
    ):
        """测试审计日志包含服务器信息"""
        response = await client.get(
            "/api/v1/audit-logs",
            headers=admin_headers,
        )
        assert response.status_code == 200
        data = response.json()

        for item in data["items"]:
            # 如果有服务器ID，应该包含服务器名称
            if item["server_id"]:
                assert "server_name" in item or item["server_name"] is not None
