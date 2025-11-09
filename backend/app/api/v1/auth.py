"""
认证API路由
"""

from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status

from app.dependencies import CurrentUser, get_auth_service
from app.schemas.auth import (
    LoginRequest,
    LoginResponse,
    RefreshTokenRequest,
    RefreshTokenResponse,
)
from app.schemas.user import PasswordChange, UserCreate, UserResponse
from app.services.auth_service import AuthService

router = APIRouter()


@router.post("/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def register(
    user_data: UserCreate,
    auth_service: Annotated[AuthService, Depends(get_auth_service)],
):
    """
    用户注册

    - **username**: 用户名（3-50字符）
    - **email**: 邮箱地址
    - **password**: 密码（至少8字符，包含大小写字母和数字）
    - **full_name**: 全名（可选）
    """
    try:
        user = await auth_service.register(user_data)
        return user
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )


@router.post("/login", response_model=LoginResponse)
async def login(
    login_data: LoginRequest,
    auth_service: Annotated[AuthService, Depends(get_auth_service)],
):
    """
    用户登录

    - **username**: 用户名或邮箱
    - **password**: 密码

    返回用户信息和访问令牌、刷新令牌
    """
    try:
        result = await auth_service.login(login_data.username, login_data.password)
        return result
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=str(e),
            headers={"WWW-Authenticate": "Bearer"},
        )


@router.post("/refresh", response_model=RefreshTokenResponse)
async def refresh_token(
    refresh_data: RefreshTokenRequest,
    auth_service: Annotated[AuthService, Depends(get_auth_service)],
):
    """
    刷新访问令牌

    - **refresh_token**: 刷新令牌

    返回新的访问令牌
    """
    try:
        tokens = await auth_service.refresh_access_token(refresh_data.refresh_token)
        return RefreshTokenResponse(
            access_token=tokens.access_token,
            token_type=tokens.token_type,
            expires_in=tokens.expires_in,
        )
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=str(e),
            headers={"WWW-Authenticate": "Bearer"},
        )


@router.get("/me", response_model=UserResponse)
async def get_current_user_info(
    current_user: CurrentUser,
):
    """
    获取当前登录用户信息

    需要Bearer Token认证
    """
    return UserResponse.model_validate(current_user)


@router.post("/change-password", status_code=status.HTTP_200_OK)
async def change_password(
    password_data: PasswordChange,
    current_user: CurrentUser,
    auth_service: Annotated[AuthService, Depends(get_auth_service)],
):
    """
    修改密码

    - **old_password**: 旧密码
    - **new_password**: 新密码（至少8字符，包含大小写字母和数字）

    需要Bearer Token认证
    """
    try:
        await auth_service.change_password(
            current_user.id, password_data.old_password, password_data.new_password
        )
        return {"message": "Password changed successfully"}
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )


@router.post("/logout", status_code=status.HTTP_200_OK)
async def logout(
    current_user: CurrentUser,
):
    """
    用户登出

    注意：由于使用JWT，服务端无法主动失效令牌。
    客户端应该删除本地存储的令牌。
    如需实现真正的登出，需要维护令牌黑名单（可使用Redis）。

    需要Bearer Token认证
    """
    # TODO: 如需实现令牌黑名单，在此添加逻辑
    return {"message": "Logged out successfully"}
