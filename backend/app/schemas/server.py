"""
服务器相关的Pydantic模式
"""

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, Field, field_validator


# ========== 服务器基础模式 ==========


class ServerBase(BaseModel):
    """服务器基础模式"""

    name: str = Field(..., min_length=1, max_length=100, description="服务器名称")
    host: str = Field(..., description="主机地址（IP或域名）")
    port: int = Field(default=22, ge=1, le=65535, description="SSH端口")
    description: str | None = Field(None, description="服务器描述")
    tags: list[str] = Field(default_factory=list, description="服务器标签")


class ServerCreate(ServerBase):
    """服务器创建模式"""

    ssh_username: str = Field(..., min_length=1, max_length=100, description="SSH用户名")
    ssh_password: str | None = Field(None, description="SSH密码（与ssh_key二选一）")
    ssh_key: str | None = Field(None, description="SSH私钥（与ssh_password二选一）")

    @field_validator("ssh_password", "ssh_key")
    @classmethod
    def validate_credentials(cls, v, info):
        """验证至少提供一种认证方式"""
        # 这个验证会在model_validate时进行更复杂的检查
        return v


class ServerUpdate(BaseModel):
    """服务器更新模式"""

    name: str | None = Field(None, min_length=1, max_length=100)
    host: str | None = None
    port: int | None = Field(None, ge=1, le=65535)
    description: str | None = None
    tags: list[str] | None = None
    ssh_username: str | None = Field(None, min_length=1, max_length=100)
    ssh_password: str | None = None
    ssh_key: str | None = None


# ========== 服务器响应模式 ==========


class ServerOwner(BaseModel):
    """服务器所有者信息"""

    id: UUID
    username: str

    class Config:
        from_attributes = True


class ServerResponse(ServerBase):
    """服务器响应模式"""

    id: UUID
    owner_id: UUID
    owner: ServerOwner
    ssh_username: str | None
    status: str
    last_checked_at: datetime | None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class ServerDetailResponse(ServerResponse):
    """服务器详细响应模式（包含更多信息）"""

    # 可以添加额外的详细信息
    pass


class ServerListResponse(BaseModel):
    """服务器列表响应模式"""

    total: int = Field(..., description="总数")
    page: int = Field(..., description="当前页")
    size: int = Field(..., description="每页数量")
    items: list[ServerResponse] = Field(..., description="服务器列表")


# ========== 连接测试 ==========


class ConnectionTestResponse(BaseModel):
    """连接测试响应模式"""

    status: str = Field(..., description="状态: success 或 error")
    message: str = Field(..., description="消息")
    latency_ms: int = Field(..., description="延迟（毫秒）")


class SystemInfoResponse(BaseModel):
    """系统信息响应模式"""

    os_info: str = Field(..., description="操作系统信息")
    hostname: str = Field(..., description="主机名")
    kernel: str = Field(..., description="内核版本")


# ========== 服务器查询参数 ==========


class ServerQueryParams(BaseModel):
    """服务器查询参数"""

    page: int = Field(default=1, ge=1, description="页码")
    size: int = Field(default=20, ge=1, le=100, description="每页数量")
    status: str | None = Field(
        None, pattern="^(online|offline|error|unknown)$", description="状态筛选"
    )
    tags: str | None = Field(None, description="标签筛选（逗号分隔）")
    search: str | None = Field(None, description="搜索关键词（名称或主机）")
