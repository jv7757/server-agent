"""
FastAPI依赖注入
"""
from typing import Annotated

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models.user import User
from app.services.auth_service import AuthService

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
