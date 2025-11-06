"""
命令执行相关的Pydantic模式
"""
from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, Field


# ========== 命令执行请求 ==========


class CommandExecuteRequest(BaseModel):
    """命令执行请求模式"""

    command: str = Field(..., min_length=1, description="要执行的命令")
    timeout: int = Field(default=30, ge=1, le=300, description="超时时间（秒）")
    allow_dangerous: bool = Field(default=False, description="是否允许危险命令")
    skip_confirmation: bool = Field(default=False, description="是否跳过确认提示")


class CommandValidateRequest(BaseModel):
    """命令验证请求模式"""

    command: str = Field(..., min_length=1, description="要验证的命令")


# ========== 命令执行响应 ==========


class CommandExecuteResponse(BaseModel):
    """命令执行响应模式"""

    command: str = Field(..., description="执行的命令")
    exit_code: int = Field(..., description="退出码")
    stdout: str = Field(..., description="标准输出")
    stderr: str = Field(..., description="标准错误")
    execution_time_ms: int = Field(..., description="执行时间（毫秒）")
    executed_at: datetime = Field(..., description="执行时间")


class CommandValidateResponse(BaseModel):
    """命令验证响应模式"""

    command: str = Field(..., description="命令")
    is_valid: bool = Field(..., description="是否有效")
    risk_level: str = Field(..., description="风险级别: safe, warning, dangerous")
    message: str | None = Field(None, description="验证消息")
    requires_confirmation: bool = Field(default=False, description="是否需要确认")


# ========== 命令历史 ==========


class CommandHistoryResponse(BaseModel):
    """命令历史响应模式"""

    id: int
    server_id: UUID
    server_name: str
    command: str
    exit_code: int | None
    execution_time_ms: int | None
    executed_at: datetime
    user_id: UUID
    username: str

    class Config:
        from_attributes = True


class CommandHistoryListResponse(BaseModel):
    """命令历史列表响应模式"""

    total: int = Field(..., description="总数")
    page: int = Field(..., description="当前页")
    size: int = Field(..., description="每页数量")
    items: list[CommandHistoryResponse] = Field(..., description="命令历史列表")


# ========== 批量执行 ==========


class BatchCommandRequest(BaseModel):
    """批量命令执行请求"""

    server_ids: list[UUID] = Field(..., min_items=1, description="服务器ID列表")
    command: str = Field(..., min_length=1, description="要执行的命令")
    timeout: int = Field(default=30, ge=1, le=300, description="超时时间（秒）")
    allow_dangerous: bool = Field(default=False, description="是否允许危险命令")


class BatchCommandResult(BaseModel):
    """单个服务器的批量执行结果"""

    server_id: UUID
    server_name: str
    success: bool
    exit_code: int | None = None
    stdout: str | None = None
    stderr: str | None = None
    error: str | None = None
    execution_time_ms: int | None = None


class BatchCommandResponse(BaseModel):
    """批量命令执行响应"""

    total: int = Field(..., description="总服务器数")
    success: int = Field(..., description="成功数量")
    failed: int = Field(..., description="失败数量")
    results: list[BatchCommandResult] = Field(..., description="执行结果列表")
