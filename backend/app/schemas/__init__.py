"""
Pydantic模式模块
"""
from app.schemas.auth import (
    LoginRequest,
    LoginResponse,
    RefreshTokenRequest,
    RefreshTokenResponse,
    TokenPayload,
    TokenResponse,
)
from app.schemas.server import (
    ConnectionTestResponse,
    ServerCreate,
    ServerDetailResponse,
    ServerListResponse,
    ServerQueryParams,
    ServerResponse,
    ServerUpdate,
    SystemInfoResponse,
)
from app.schemas.user import (
    PasswordChange,
    PasswordReset,
    UserCreate,
    UserDetailResponse,
    UserListResponse,
    UserResponse,
    UserUpdate,
    UserUpdateRole,
    UserUpdateStatus,
)

__all__ = [
    # Auth
    "LoginRequest",
    "LoginResponse",
    "RefreshTokenRequest",
    "RefreshTokenResponse",
    "TokenResponse",
    "TokenPayload",
    # User
    "UserCreate",
    "UserUpdate",
    "UserUpdateRole",
    "UserUpdateStatus",
    "UserResponse",
    "UserDetailResponse",
    "UserListResponse",
    "PasswordChange",
    "PasswordReset",
    # Server
    "ServerCreate",
    "ServerUpdate",
    "ServerResponse",
    "ServerDetailResponse",
    "ServerListResponse",
    "ServerQueryParams",
    "ConnectionTestResponse",
    "SystemInfoResponse",
]
