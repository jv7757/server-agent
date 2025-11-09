"""
服务器管理服务
"""
from uuid import UUID

from sqlalchemy import func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload

from app.core.security import encrypt_ssh_credential
from app.models.server import Server
from app.schemas.server import (
    ConnectionTestResponse,
    ServerCreate,
    ServerListResponse,
    ServerResponse,
    ServerUpdate,
)
from app.services.ssh_service import SSHService
from app.utils.logger import logger


class ServerService:
    """服务器管理服务类"""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def create_server(self, server_data: ServerCreate, owner_id: UUID) -> ServerResponse:
        """
        创建服务器

        Args:
            server_data: 服务器数据
            owner_id: 所有者ID

        Returns:
            ServerResponse: 创建的服务器信息

        Raises:
            ValueError: 验证失败
        """
        # 验证至少提供一种认证方式
        if not server_data.ssh_password and not server_data.ssh_key:
            raise ValueError("Either ssh_password or ssh_key must be provided")

        # 检查服务器名称是否重复（同一用户下）
        existing = await self.db.execute(
            select(Server).where(
                Server.owner_id == owner_id,
                Server.name == server_data.name,
            )
        )
        if existing.scalar_one_or_none():
            raise ValueError("Server name already exists")

        # 加密SSH凭证
        encrypted_password = None
        encrypted_key = None

        if server_data.ssh_password:
            encrypted_password = encrypt_ssh_credential(server_data.ssh_password)

        if server_data.ssh_key:
            encrypted_key = encrypt_ssh_credential(server_data.ssh_key)

        # 创建服务器记录
        new_server = Server(
            name=server_data.name,
            host=server_data.host,
            port=server_data.port,
            description=server_data.description,
            owner_id=owner_id,
            ssh_username=server_data.ssh_username,
            ssh_password_encrypted=encrypted_password,
            ssh_key_encrypted=encrypted_key,
            tags=server_data.tags,
            status="unknown",
        )

        self.db.add(new_server)
        await self.db.commit()
        await self.db.refresh(new_server, ["owner"])

        logger.info(f"Server created: {new_server.name} ({new_server.id})")

        return ServerResponse.model_validate(new_server)

    async def get_server_by_id(self, server_id: UUID, user_id: UUID) -> Server | None:
        """
        根据ID获取服务器

        Args:
            server_id: 服务器ID
            user_id: 用户ID（用于权限检查）

        Returns:
            Server: 服务器对象
        """
        result = await self.db.execute(
            select(Server)
            .options(joinedload(Server.owner))
            .where(
                Server.id == server_id,
                Server.owner_id == user_id,  # 只能访问自己的服务器
            )
        )
        return result.scalar_one_or_none()

    async def get_servers(
        self,
        user_id: UUID,
        page: int = 1,
        size: int = 20,
        status: str | None = None,
        tags: list[str] | None = None,
        search: str | None = None,
    ) -> ServerListResponse:
        """
        获取服务器列表

        Args:
            user_id: 用户ID
            page: 页码
            size: 每页数量
            status: 状态筛选
            tags: 标签筛选
            search: 搜索关键词

        Returns:
            ServerListResponse: 服务器列表
        """
        # 构建查询条件
        conditions = [Server.owner_id == user_id]

        if status:
            conditions.append(Server.status == status)

        if tags:
            # 使用JSONB包含查询
            for tag in tags:
                conditions.append(Server.tags.contains([tag]))

        if search:
            conditions.append(
                or_(
                    Server.name.ilike(f"%{search}%"),
                    Server.host.ilike(f"%{search}%"),
                )
            )

        # 查询总数
        count_query = select(func.count()).select_from(Server).where(*conditions)
        total_result = await self.db.execute(count_query)
        total = total_result.scalar_one()

        # 查询数据
        offset = (page - 1) * size
        query = (
            select(Server)
            .options(joinedload(Server.owner))
            .where(*conditions)
            .order_by(Server.created_at.desc())
            .offset(offset)
            .limit(size)
        )

        result = await self.db.execute(query)
        servers = result.scalars().all()

        return ServerListResponse(
            total=total,
            page=page,
            size=size,
            items=[ServerResponse.model_validate(s) for s in servers],
        )

    async def update_server(
        self, server_id: UUID, user_id: UUID, server_data: ServerUpdate
    ) -> ServerResponse:
        """
        更新服务器

        Args:
            server_id: 服务器ID
            user_id: 用户ID
            server_data: 更新数据

        Returns:
            ServerResponse: 更新后的服务器信息

        Raises:
            ValueError: 服务器不存在
        """
        server = await self.get_server_by_id(server_id, user_id)
        if not server:
            raise ValueError("Server not found")

        # 更新字段
        update_data = server_data.model_dump(exclude_unset=True)

        for field, value in update_data.items():
            if field == "ssh_password" and value:
                server.ssh_password_encrypted = encrypt_ssh_credential(value)
            elif field == "ssh_key" and value:
                server.ssh_key_encrypted = encrypt_ssh_credential(value)
            elif field not in ("ssh_password", "ssh_key"):
                setattr(server, field, value)

        await self.db.commit()
        await self.db.refresh(server, ["owner"])

        logger.info(f"Server updated: {server.name} ({server.id})")

        return ServerResponse.model_validate(server)

    async def delete_server(self, server_id: UUID, user_id: UUID) -> bool:
        """
        删除服务器

        Args:
            server_id: 服务器ID
            user_id: 用户ID

        Returns:
            bool: 是否成功删除

        Raises:
            ValueError: 服务器不存在
        """
        server = await self.get_server_by_id(server_id, user_id)
        if not server:
            raise ValueError("Server not found")

        await self.db.delete(server)
        await self.db.commit()

        logger.info(f"Server deleted: {server.name} ({server.id})")

        return True

    async def test_connection(self, server_id: UUID, user_id: UUID) -> ConnectionTestResponse:
        """
        测试服务器连接

        Args:
            server_id: 服务器ID
            user_id: 用户ID

        Returns:
            ConnectionTestResponse: 测试结果

        Raises:
            ValueError: 服务器不存在
        """
        server = await self.get_server_by_id(server_id, user_id)
        if not server:
            raise ValueError("Server not found")

        # 创建SSH服务并测试连接
        ssh_service = await SSHService.create_from_encrypted(
            host=server.host,
            port=server.port,
            username=server.ssh_username or "",
            encrypted_password=server.ssh_password_encrypted,
            encrypted_key=server.ssh_key_encrypted,
        )

        result = await ssh_service.test_connection()

        # 更新服务器状态
        from datetime import datetime

        server.status = "online" if result["status"] == "success" else "offline"
        server.last_checked_at = datetime.utcnow()
        await self.db.commit()

        return ConnectionTestResponse(**result)

    async def update_server_status(self, server_id: UUID, status: str) -> None:
        """
        更新服务器状态

        Args:
            server_id: 服务器ID
            status: 新状态
        """
        from datetime import datetime

        result = await self.db.execute(select(Server).where(Server.id == server_id))
        server = result.scalar_one_or_none()

        if server:
            server.status = status
            server.last_checked_at = datetime.utcnow()
            await self.db.commit()

    async def get_ssh_service(self, server_id: UUID, user_id: UUID) -> SSHService:
        """
        获取服务器的SSH服务实例

        Args:
            server_id: 服务器ID
            user_id: 用户ID

        Returns:
            SSHService: SSH服务实例

        Raises:
            ValueError: 服务器不存在
        """
        server = await self.get_server_by_id(server_id, user_id)
        if not server:
            raise ValueError("Server not found")

        ssh_service = await SSHService.create_from_encrypted(
            host=server.host,
            port=server.port,
            username=server.ssh_username or "",
            encrypted_password=server.ssh_password_encrypted,
            encrypted_key=server.ssh_key_encrypted,
        )

        return ssh_service
