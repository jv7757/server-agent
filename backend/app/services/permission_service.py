"""
权限管理服务
"""
from typing import List
from uuid import UUID

from sqlalchemy import and_, delete, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.permission import UserServerPermission
from app.models.server import Server
from app.models.user import User
from app.utils.logger import logger


class PermissionService:
    """权限管理服务类"""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def grant_permission(
        self,
        server_id: UUID,
        target_user_id: UUID,
        grantor_id: UUID,
        permissions: List[str],
    ) -> UserServerPermission:
        """
        授予权限

        Args:
            server_id: 服务器ID
            target_user_id: 目标用户ID
            grantor_id: 授权者ID
            permissions: 权限列表 ['read', 'write', 'execute', 'admin']

        Returns:
            UserServerPermission: 权限对象

        Raises:
            ValueError: 权限验证失败
        """
        # 验证授权者是否有权限
        if not await self.can_manage_permissions(server_id, grantor_id):
            raise ValueError("您没有权限管理该服务器的权限")

        # 验证目标用户存在
        user_result = await self.db.execute(
            select(User).where(User.id == target_user_id)
        )
        if not user_result.scalar_one_or_none():
            raise ValueError("目标用户不存在")

        # 验证服务器存在
        server_result = await self.db.execute(
            select(Server).where(Server.id == server_id)
        )
        if not server_result.scalar_one_or_none():
            raise ValueError("服务器不存在")

        # 检查权限是否已存在
        existing = await self.db.execute(
            select(UserServerPermission).where(
                and_(
                    UserServerPermission.user_id == target_user_id,
                    UserServerPermission.server_id == server_id,
                )
            )
        )
        permission = existing.scalar_one_or_none()

        if permission:
            # 更新现有权限
            permission.can_read = "read" in permissions
            permission.can_write = "write" in permissions
            permission.can_execute = "execute" in permissions
            permission.can_admin = "admin" in permissions
        else:
            # 创建新权限
            permission = UserServerPermission(
                user_id=target_user_id,
                server_id=server_id,
                can_read="read" in permissions,
                can_write="write" in permissions,
                can_execute="execute" in permissions,
                can_admin="admin" in permissions,
            )
            self.db.add(permission)

        await self.db.commit()
        await self.db.refresh(permission)

        logger.info(
            f"User {grantor_id} granted permissions {permissions} "
            f"to user {target_user_id} on server {server_id}"
        )

        return permission

    async def revoke_permission(
        self,
        server_id: UUID,
        target_user_id: UUID,
        revoker_id: UUID,
    ) -> bool:
        """
        撤销权限

        Args:
            server_id: 服务器ID
            target_user_id: 目标用户ID
            revoker_id: 撤销者ID

        Returns:
            bool: 是否成功撤销

        Raises:
            ValueError: 权限验证失败
        """
        # 验证撤销者是否有权限
        if not await self.can_manage_permissions(server_id, revoker_id):
            raise ValueError("您没有权限管理该服务器的权限")

        # 删除权限记录
        result = await self.db.execute(
            delete(UserServerPermission).where(
                and_(
                    UserServerPermission.user_id == target_user_id,
                    UserServerPermission.server_id == server_id,
                )
            )
        )

        await self.db.commit()

        deleted = result.rowcount > 0

        if deleted:
            logger.info(
                f"User {revoker_id} revoked permissions "
                f"from user {target_user_id} on server {server_id}"
            )

        return deleted

    async def get_user_permissions(
        self,
        user_id: UUID,
        page: int = 1,
        size: int = 20,
    ) -> dict:
        """
        获取用户的所有权限

        Args:
            user_id: 用户ID
            page: 页码
            size: 每页数量

        Returns:
            dict: 权限列表和分页信息
        """
        from sqlalchemy import func

        # 查询总数
        count_result = await self.db.execute(
            select(func.count())
            .select_from(UserServerPermission)
            .where(UserServerPermission.user_id == user_id)
        )
        total = count_result.scalar_one()

        # 查询权限（包含服务器信息）
        offset = (page - 1) * size
        query = (
            select(UserServerPermission, Server)
            .join(Server, UserServerPermission.server_id == Server.id)
            .where(UserServerPermission.user_id == user_id)
            .offset(offset)
            .limit(size)
        )

        result = await self.db.execute(query)
        items = []

        for permission, server in result.all():
            items.append({
                "permission_id": permission.id,
                "server_id": str(server.id),
                "server_name": server.name,
                "server_host": server.host,
                "permissions": self._format_permissions(permission),
                "created_at": permission.created_at,
            })

        return {
            "total": total,
            "page": page,
            "size": size,
            "items": items,
        }

    async def get_server_permissions(
        self,
        server_id: UUID,
        requester_id: UUID,
        page: int = 1,
        size: int = 20,
    ) -> dict:
        """
        获取服务器的所有权限

        Args:
            server_id: 服务器ID
            requester_id: 请求者ID
            page: 页码
            size: 每页数量

        Returns:
            dict: 权限列表和分页信息

        Raises:
            ValueError: 权限验证失败
        """
        # 验证请求者是否有权限查看
        if not await self.can_manage_permissions(server_id, requester_id):
            raise ValueError("您没有权限查看该服务器的权限列表")

        from sqlalchemy import func

        # 查询总数
        count_result = await self.db.execute(
            select(func.count())
            .select_from(UserServerPermission)
            .where(UserServerPermission.server_id == server_id)
        )
        total = count_result.scalar_one()

        # 查询权限（包含用户信息）
        offset = (page - 1) * size
        query = (
            select(UserServerPermission, User)
            .join(User, UserServerPermission.user_id == User.id)
            .where(UserServerPermission.server_id == server_id)
            .offset(offset)
            .limit(size)
        )

        result = await self.db.execute(query)
        items = []

        for permission, user in result.all():
            items.append({
                "permission_id": permission.id,
                "user_id": str(user.id),
                "username": user.username,
                "email": user.email,
                "permissions": self._format_permissions(permission),
                "created_at": permission.created_at,
            })

        return {
            "total": total,
            "page": page,
            "size": size,
            "items": items,
        }

    async def check_permission(
        self,
        server_id: UUID,
        user_id: UUID,
        required_permission: str,
    ) -> bool:
        """
        检查用户是否有指定权限

        Args:
            server_id: 服务器ID
            user_id: 用户ID
            required_permission: 所需权限 ('read', 'write', 'execute', 'admin')

        Returns:
            bool: 是否有权限
        """
        # 检查用户是否是管理员
        user_result = await self.db.execute(
            select(User).where(User.id == user_id)
        )
        user = user_result.scalar_one_or_none()

        if not user:
            return False

        # 管理员有所有权限
        if user.role == "admin":
            return True

        # 检查用户是否是服务器所有者
        server_result = await self.db.execute(
            select(Server).where(Server.id == server_id)
        )
        server = server_result.scalar_one_or_none()

        if not server:
            return False

        # 服务器所有者有所有权限
        if server.owner_id == user_id:
            return True

        # 检查权限表
        permission_result = await self.db.execute(
            select(UserServerPermission).where(
                and_(
                    UserServerPermission.user_id == user_id,
                    UserServerPermission.server_id == server_id,
                )
            )
        )
        permission = permission_result.scalar_one_or_none()

        if not permission:
            return False

        # 根据所需权限检查
        permission_map = {
            "read": permission.can_read,
            "write": permission.can_write,
            "execute": permission.can_execute,
            "admin": permission.can_admin,
        }

        return permission_map.get(required_permission, False)

    async def can_manage_permissions(
        self,
        server_id: UUID,
        user_id: UUID,
    ) -> bool:
        """
        检查用户是否可以管理服务器权限

        只有服务器所有者、管理员、或拥有 admin 权限的用户可以管理权限

        Args:
            server_id: 服务器ID
            user_id: 用户ID

        Returns:
            bool: 是否可以管理权限
        """
        # 检查是否是系统管理员
        user_result = await self.db.execute(
            select(User).where(User.id == user_id)
        )
        user = user_result.scalar_one_or_none()

        if not user:
            return False

        if user.role == "admin":
            return True

        # 检查是否是服务器所有者
        server_result = await self.db.execute(
            select(Server).where(Server.id == server_id)
        )
        server = server_result.scalar_one_or_none()

        if not server:
            return False

        if server.owner_id == user_id:
            return True

        # 检查是否有 admin 权限
        return await self.check_permission(server_id, user_id, "admin")

    async def get_accessible_servers(
        self,
        user_id: UUID,
        min_permission: str = "read",
    ) -> List[UUID]:
        """
        获取用户可访问的服务器ID列表

        Args:
            user_id: 用户ID
            min_permission: 最小权限要求 ('read', 'write', 'execute', 'admin')

        Returns:
            List[UUID]: 服务器ID列表
        """
        # 检查用户角色
        user_result = await self.db.execute(
            select(User).where(User.id == user_id)
        )
        user = user_result.scalar_one_or_none()

        if not user:
            return []

        # 管理员可以访问所有服务器
        if user.role == "admin":
            result = await self.db.execute(select(Server.id))
            return [row[0] for row in result.all()]

        # 获取用户拥有的服务器
        owned_servers = await self.db.execute(
            select(Server.id).where(Server.owner_id == user_id)
        )
        server_ids = [row[0] for row in owned_servers.all()]

        # 根据权限级别构建查询条件
        permission_conditions = []

        if min_permission == "read":
            permission_conditions = [
                UserServerPermission.can_read == True,
                UserServerPermission.can_write == True,
                UserServerPermission.can_execute == True,
                UserServerPermission.can_admin == True,
            ]
        elif min_permission == "write":
            permission_conditions = [
                UserServerPermission.can_write == True,
                UserServerPermission.can_execute == True,
                UserServerPermission.can_admin == True,
            ]
        elif min_permission == "execute":
            permission_conditions = [
                UserServerPermission.can_execute == True,
                UserServerPermission.can_admin == True,
            ]
        elif min_permission == "admin":
            permission_conditions = [UserServerPermission.can_admin == True]

        # 获取有权限的服务器
        if permission_conditions:
            permitted_servers = await self.db.execute(
                select(UserServerPermission.server_id)
                .where(
                    and_(
                        UserServerPermission.user_id == user_id,
                        or_(*permission_conditions),
                    )
                )
            )
            server_ids.extend([row[0] for row in permitted_servers.all()])

        # 去重
        return list(set(server_ids))

    @staticmethod
    def _format_permissions(permission: UserServerPermission) -> List[str]:
        """格式化权限对象为字符串列表"""
        perms = []
        if permission.can_read:
            perms.append("read")
        if permission.can_write:
            perms.append("write")
        if permission.can_execute:
            perms.append("execute")
        if permission.can_admin:
            perms.append("admin")
        return perms
