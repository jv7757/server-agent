"""
用户相关的Pydantic模式
"""

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, EmailStr, Field


# ========== 用户基础模式 ==========


class UserBase(BaseModel):
    """用户基础模式"""

    username: str = Field(..., min_length=3, max_length=50, description="用户名")
    email: EmailStr = Field(..., description="邮箱地址")
    full_name: str | None = Field(None, max_length=100, description="全名")


class UserCreate(UserBase):
    """用户创建模式"""

    password: str = Field(..., min_length=8, description="密码")


class UserUpdate(BaseModel):
    """用户更新模式"""

    email: EmailStr | None = None
    full_name: str | None = Field(None, max_length=100)
    password: str | None = Field(None, min_length=8)


class UserUpdateRole(BaseModel):
    """用户角色更新模式（仅管理员）"""

    role: str = Field(..., pattern="^(admin|user|viewer)$", description="用户角色")


class UserUpdateStatus(BaseModel):
    """用户状态更新模式（仅管理员）"""

    is_active: bool = Field(..., description="是否激活")


# ========== 用户响应模式 ==========


class UserResponse(UserBase):
    """用户响应模式（公开信息）"""

    id: UUID
    role: str
    is_active: bool
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class UserDetailResponse(UserResponse):
    """用户详细响应模式（包含敏感信息，仅本人或管理员可见）"""

    pass


class UserListResponse(BaseModel):
    """用户列表响应模式"""

    total: int = Field(..., description="总数")
    page: int = Field(..., description="当前页")
    size: int = Field(..., description="每页数量")
    items: list[UserResponse] = Field(..., description="用户列表")


# ========== 密码相关 ==========


class PasswordChange(BaseModel):
    """密码修改模式"""

    old_password: str = Field(..., description="旧密码")
    new_password: str = Field(..., min_length=8, description="新密码")


class PasswordReset(BaseModel):
    """密码重置模式"""

    token: str = Field(..., description="重置令牌")
    new_password: str = Field(..., min_length=8, description="新密码")
