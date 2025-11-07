"""
权限相关的Pydantic模式
"""
from datetime import datetime
from typing import List
from uuid import UUID

from pydantic import BaseModel, Field, field_validator


# ========== 权限请求 ==========


class PermissionGrant(BaseModel):
    """授予权限请求模式"""

    server_id: UUID = Field(..., description="服务器ID")
    target_user_id: UUID = Field(..., description="目标用户ID")
    permissions: List[str] = Field(..., description="权限列表")

    @field_validator("permissions")
    @classmethod
    def validate_permissions(cls, v: List[str]) -> List[str]:
        """验证权限列表"""
        valid_permissions = {"read", "write", "execute", "admin"}
        for perm in v:
            if perm not in valid_permissions:
                raise ValueError(
                    f"Invalid permission: {perm}. "
                    f"Valid permissions: {', '.join(valid_permissions)}"
                )
        if not v:
            raise ValueError("At least one permission is required")
        return v


class PermissionRevoke(BaseModel):
    """撤销权限请求模式"""

    server_id: UUID = Field(..., description="服务器ID")
    target_user_id: UUID = Field(..., description="目标用户ID")


class PermissionCheck(BaseModel):
    """权限检查请求模式"""

    server_id: UUID = Field(..., description="服务器ID")
    required_permission: str = Field(..., description="所需权限")

    @field_validator("required_permission")
    @classmethod
    def validate_permission(cls, v: str) -> str:
        """验证权限"""
        valid_permissions = {"read", "write", "execute", "admin"}
        if v not in valid_permissions:
            raise ValueError(
                f"Invalid permission: {v}. "
                f"Valid permissions: {', '.join(valid_permissions)}"
            )
        return v


# ========== 权限响应 ==========


class PermissionResponse(BaseModel):
    """权限响应模式"""

    permission_id: str
    server_id: str | UUID
    user_id: str | UUID
    permissions: List[str] = Field(..., description="权限列表")
    created_at: datetime

    @field_validator('permission_id', 'server_id', 'user_id', mode='before')
    @classmethod
    def convert_uuid_to_str(cls, v):
        """将 UUID 转换为字符串"""
        if isinstance(v, UUID):
            return str(v)
        return v

    class Config:
        from_attributes = True


class UserPermissionItem(BaseModel):
    """用户权限列表项"""

    permission_id: str
    server_id: str
    server_name: str
    server_host: str
    permissions: List[str]
    created_at: datetime

    @field_validator('permission_id', 'server_id', mode='before')
    @classmethod
    def convert_uuid_to_str(cls, v):
        """将 UUID 转换为字符串"""
        if isinstance(v, UUID):
            return str(v)
        return v


class UserPermissionListResponse(BaseModel):
    """用户权限列表响应"""

    total: int = Field(..., description="总数")
    page: int = Field(..., description="当前页")
    size: int = Field(..., description="每页数量")
    items: List[UserPermissionItem] = Field(..., description="权限列表")


class ServerPermissionItem(BaseModel):
    """服务器权限列表项"""

    permission_id: str
    user_id: str
    username: str
    email: str
    permissions: List[str]
    created_at: datetime

    @field_validator('permission_id', 'user_id', mode='before')
    @classmethod
    def convert_uuid_to_str(cls, v):
        """将 UUID 转换为字符串"""
        if isinstance(v, UUID):
            return str(v)
        return v


class ServerPermissionListResponse(BaseModel):
    """服务器权限列表响应"""

    total: int = Field(..., description="总数")
    page: int = Field(..., description="当前页")
    size: int = Field(..., description="每页数量")
    items: List[ServerPermissionItem] = Field(..., description="权限列表")


class PermissionGrantResponse(BaseModel):
    """授予权限响应"""

    success: bool = Field(..., description="是否成功")
    message: str = Field(..., description="提示消息")
    permission: PermissionResponse | None = Field(None, description="权限详情")


class PermissionRevokeResponse(BaseModel):
    """撤销权限响应"""

    success: bool = Field(..., description="是否成功")
    message: str = Field(..., description="提示消息")


class PermissionCheckResponse(BaseModel):
    """权限检查响应"""

    has_permission: bool = Field(..., description="是否有权限")
    server_id: str
    required_permission: str


class AccessibleServersResponse(BaseModel):
    """可访问服务器列表响应"""

    server_ids: List[str] = Field(..., description="服务器ID列表")
    count: int = Field(..., description="服务器数量")
