"""
监控指标相关的Pydantic模式
"""
from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, Field


# ========== 指标响应模式 ==========


class MetricResponse(BaseModel):
    """监控指标响应模式"""

    id: int
    server_id: UUID
    cpu_usage_percent: float | None
    cpu_cores: int | None
    memory_total_mb: int | None
    memory_used_mb: int | None
    memory_usage_percent: float | None
    disk_total_gb: int | None
    disk_used_gb: int | None
    disk_usage_percent: float | None
    network_bytes_sent: int | None
    network_bytes_recv: int | None
    uptime_seconds: int | None
    load_average: dict | None
    collected_at: datetime

    class Config:
        from_attributes = True


class CurrentMetricsResponse(BaseModel):
    """当前指标响应模式"""

    server_id: UUID
    server_name: str
    cpu_usage_percent: float | None
    cpu_cores: int | None
    memory_total_mb: int | None
    memory_used_mb: int | None
    memory_free_mb: int | None
    memory_usage_percent: float | None
    disk_total_gb: int | None
    disk_used_gb: int | None
    disk_free_gb: int | None
    disk_usage_percent: float | None
    network_bytes_sent: int | None
    network_bytes_recv: int | None
    uptime_seconds: int | None
    uptime_human: str | None
    load_average: dict | None
    collected_at: datetime


class MetricsHistoryResponse(BaseModel):
    """历史指标响应模式"""

    total: int = Field(..., description="总数")
    items: list[MetricResponse] = Field(..., description="指标列表")


class MetricsSummaryResponse(BaseModel):
    """指标摘要统计响应模式"""

    cpu: dict = Field(..., description="CPU统计")
    memory: dict = Field(..., description="内存统计")
    disk: dict = Field(..., description="磁盘统计")
    data_points: int = Field(..., description="数据点数量")
    time_range_hours: int = Field(..., description="统计时间范围（小时）")


# ========== 指标查询参数 ==========


class MetricsQueryParams(BaseModel):
    """指标查询参数"""

    start_time: datetime | None = Field(None, description="开始时间")
    end_time: datetime | None = Field(None, description="结束时间")
    limit: int = Field(default=100, ge=1, le=1000, description="返回数量限制")


class MetricsSummaryParams(BaseModel):
    """指标摘要查询参数"""

    hours: int = Field(default=24, ge=1, le=168, description="统计时间范围（小时，最多7天）")
