"""
审计日志相关的Pydantic模式
"""

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, Field, field_validator


class AuditLogResponse(BaseModel):
    """审计日志响应模式"""

    id: int
    user_id: str | None
    username: str | None
    server_id: str | None
    server_name: str | None
    action: str
    resource_type: str | None
    details: dict | None
    ip_address: str | None
    created_at: datetime

    @field_validator("user_id", "server_id", mode="before")
    @classmethod
    def convert_uuid_to_str(cls, v):
        """将 UUID 转换为字符串"""
        if isinstance(v, UUID):
            return str(v)
        return v

    class Config:
        from_attributes = True


class AuditLogListResponse(BaseModel):
    """审计日志列表响应"""

    total: int = Field(..., description="总数")
    page: int = Field(..., description="当前页")
    size: int = Field(..., description="每页数量")
    items: list[AuditLogResponse] = Field(..., description="日志列表")
