"""
FastAPI依赖注入
"""
from typing import Annotated
from uuid import UUID

from fastapi import Depends, HTTPException, WebSocket, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models.user import User
from app.services.auth_service import AuthService
from app.services.permission_service import PermissionService

# HTTP Bearer认证方案
security = HTTPBearer()


async def get_auth_service(
    db: Annotated[AsyncSession, Depends(get_db)]
) -> AuthService:
    """获取认证服务依赖"""
    return AuthService(db)


async def get_current_user(
    credentials: Annotated[HTTPAuthorizationCredentials, Depends(security)],
    auth_service: Annotated[AuthService, Depends(get_auth_service)],
) -> User:
    """
    获取当前登录用户

    Args:
        credentials: HTTP Bearer凭证
        auth_service: 认证服务

    Returns:
        User: 当前用户

    Raises:
        HTTPException: 401 未授权
    """
    try:
        token = credentials.credentials
        user = await auth_service.get_current_user(token)
        return user
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=str(e),
            headers={"WWW-Authenticate": "Bearer"},
        )


async def get_current_user_ws(
    websocket: WebSocket,
    token: str,
    db: Annotated[AsyncSession, Depends(get_db)],
) -> User:
    """
    获取当前登录用户 (WebSocket)

    从query参数中获取token: ?token=xxx

    Args:
        websocket: WebSocket连接
        token: JWT token (从query参数获取)
        db: 数据库会话

    Returns:
        User: 当前用户

    Raises:
        WebSocketException: 401 未授权
    """
    try:
        auth_service = AuthService(db)
        user = await auth_service.get_current_user(token)

        if not user.is_active:
            await websocket.close(code=status.WS_1008_POLICY_VIOLATION, reason="Inactive user")
            raise ValueError("Inactive user")

        return user
    except ValueError as e:
        await websocket.close(code=status.WS_1008_POLICY_VIOLATION, reason=str(e))
        raise
    except Exception as e:
        await websocket.close(code=status.WS_1011_INTERNAL_ERROR, reason="Authentication failed")
        raise


async def get_current_active_user(
    current_user: Annotated[User, Depends(get_current_user)]
) -> User:
    """
    获取当前激活用户

    Args:
        current_user: 当前用户

    Returns:
        User: 当前激活用户

    Raises:
        HTTPException: 403 账户未激活
    """
    if not current_user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Inactive user"
        )
    return current_user


async def get_current_admin_user(
    current_user: Annotated[User, Depends(get_current_active_user)]
) -> User:
    """
    获取当前管理员用户

    Args:
        current_user: 当前用户

    Returns:
        User: 当前管理员用户

    Raises:
        HTTPException: 403 权限不足
    """
    if not current_user.is_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions"
        )
    return current_user


# 类型别名（方便使用）
CurrentUser = Annotated[User, Depends(get_current_active_user)]
CurrentAdmin = Annotated[User, Depends(get_current_admin_user)]


# ========== 权限检查 ==========


async def get_permission_service(
    db: Annotated[AsyncSession, Depends(get_db)]
) -> PermissionService:
    """获取权限服务依赖"""
    return PermissionService(db)


class PermissionChecker:
    """
    权限检查器

    使用示例:
        @router.get("/servers/{server_id}")
        async def get_server(
            server_id: UUID,
            current_user: CurrentUser,
            _: Annotated[None, Depends(PermissionChecker("read"))],
        ):
            # 此处代码只在用户有 read 权限时执行
            pass
    """

    def __init__(self, required_permission: str):
        """
        初始化权限检查器

        Args:
            required_permission: 所需权限 ('read', 'write', 'execute', 'admin')
        """
        self.required_permission = required_permission

    async def __call__(
        self,
        server_id: UUID,
        current_user: Annotated[User, Depends(get_current_active_user)],
        permission_service: Annotated[PermissionService, Depends(get_permission_service)],
    ) -> None:
        """
        检查权限

        Args:
            server_id: 服务器ID（从路径参数自动注入）
            current_user: 当前用户
            permission_service: 权限服务

        Raises:
            HTTPException: 403 权限不足
        """
        has_permission = await permission_service.check_permission(
            server_id=server_id,
            user_id=current_user.id,
            required_permission=self.required_permission,
        )

        if not has_permission:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"You don't have '{self.required_permission}' permission for this server",
            )


def require_server_permission(permission: str):
    """
    便捷的权限检查装饰器工厂

    使用示例:
        @router.get("/servers/{server_id}")
        async def get_server(
            server_id: UUID,
            current_user: CurrentUser,
            _: Annotated[None, Depends(require_server_permission("read"))],
        ):
            pass
    """
    return PermissionChecker(permission)
