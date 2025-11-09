"""
认证相关的Pydantic模式
"""

from pydantic import BaseModel, Field

from app.schemas.user import UserResponse

# ========== 登录 ==========


class LoginRequest(BaseModel):
    """登录请求模式"""

    username: str = Field(..., description="用户名或邮箱")
    password: str = Field(..., description="密码")


class TokenResponse(BaseModel):
    """Token响应模式"""

    access_token: str = Field(..., description="访问令牌")
    refresh_token: str = Field(..., description="刷新令牌")
    token_type: str = Field(default="bearer", description="令牌类型")
    expires_in: int = Field(..., description="过期时间（秒）")


class LoginResponse(BaseModel):
    """登录响应模式"""

    user: UserResponse = Field(..., description="用户信息")
    tokens: TokenResponse = Field(..., description="令牌信息")


# ========== Token刷新 ==========


class RefreshTokenRequest(BaseModel):
    """刷新Token请求模式"""

    refresh_token: str = Field(..., description="刷新令牌")


class RefreshTokenResponse(BaseModel):
    """刷新Token响应模式"""

    access_token: str = Field(..., description="新的访问令牌")
    token_type: str = Field(default="bearer", description="令牌类型")
    expires_in: int = Field(..., description="过期时间（秒）")


# ========== Token负载 ==========


class TokenPayload(BaseModel):
    """Token负载模式"""

    sub: str = Field(..., description="用户ID")
    type: str = Field(..., description="令牌类型: access 或 refresh")
    exp: int = Field(..., description="过期时间戳")
