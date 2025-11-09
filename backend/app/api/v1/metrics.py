"""
服务器监控指标API路由
"""

from datetime import datetime
from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.dependencies import CurrentUser
from app.schemas.metric import (
    CurrentMetricsResponse,
    MetricResponse,
    MetricsHistoryResponse,
    MetricsSummaryResponse,
)
from app.services.metrics_service import MetricsService
from app.services.server_service import ServerService

router = APIRouter()


async def get_metrics_service(db: Annotated[AsyncSession, Depends(get_db)]) -> MetricsService:
    """获取监控服务依赖"""
    return MetricsService(db)


async def get_server_service(db: Annotated[AsyncSession, Depends(get_db)]) -> ServerService:
    """获取服务器服务依赖"""
    return ServerService(db)


@router.post(
    "/servers/{server_id}/collect",
    response_model=MetricResponse,
    status_code=status.HTTP_201_CREATED,
)
async def collect_server_metrics(
    server_id: UUID,
    current_user: CurrentUser,
    metrics_service: Annotated[MetricsService, Depends(get_metrics_service)],
    server_service: Annotated[ServerService, Depends(get_server_service)],
):
    """
    立即采集服务器指标

    通过SSH连接服务器并采集当前的性能指标

    需要Bearer Token认证
    """
    # 验证服务器所有权
    server = await server_service.get_server_by_id(server_id, current_user.id)
    if not server:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Server not found",
        )

    try:
        # 获取SSH服务
        ssh_service = await server_service.get_ssh_service(server_id, current_user.id)

        # 采集指标
        metric = await metrics_service.collect_metrics(server_id, ssh_service)

        # 更新服务器状态
        await server_service.update_server_status(server_id, "online")

        return MetricResponse.model_validate(metric)

    except Exception as e:
        # 更新服务器状态为离线
        await server_service.update_server_status(server_id, "error")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to collect metrics: {str(e)}",
        )


@router.get("/servers/{server_id}/current", response_model=CurrentMetricsResponse)
async def get_current_metrics(
    server_id: UUID,
    current_user: CurrentUser,
    metrics_service: Annotated[MetricsService, Depends(get_metrics_service)],
    server_service: Annotated[ServerService, Depends(get_server_service)],
):
    """
    获取服务器当前指标

    返回最近一次采集的指标数据

    需要Bearer Token认证
    """
    # 验证服务器所有权
    server = await server_service.get_server_by_id(server_id, current_user.id)
    if not server:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Server not found",
        )

    # 获取最新指标
    metric = await metrics_service.get_current_metrics(server_id)

    if not metric:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No metrics data available. Try collecting metrics first.",
        )

    # 计算人类可读的运行时间
    uptime_human = None
    if metric.uptime_seconds:
        days = metric.uptime_seconds // 86400
        hours = (metric.uptime_seconds % 86400) // 3600
        minutes = (metric.uptime_seconds % 3600) // 60
        uptime_human = f"{days}d {hours}h {minutes}m"

    return CurrentMetricsResponse(
        server_id=server_id,
        server_name=server.name,
        cpu_usage_percent=metric.cpu_usage_percent,
        cpu_cores=metric.cpu_cores,
        memory_total_mb=metric.memory_total_mb,
        memory_used_mb=metric.memory_used_mb,
        memory_free_mb=metric.memory_free_mb,
        memory_usage_percent=metric.memory_usage_percent,
        disk_total_gb=metric.disk_total_gb,
        disk_used_gb=metric.disk_used_gb,
        disk_free_gb=metric.disk_free_gb,
        disk_usage_percent=metric.disk_usage_percent,
        network_bytes_sent=metric.network_bytes_sent,
        network_bytes_recv=metric.network_bytes_recv,
        uptime_seconds=metric.uptime_seconds,
        uptime_human=uptime_human,
        load_average=metric.load_average,
        collected_at=metric.collected_at,
    )


@router.get("/servers/{server_id}/history", response_model=MetricsHistoryResponse)
async def get_metrics_history(
    server_id: UUID,
    current_user: CurrentUser,
    metrics_service: Annotated[MetricsService, Depends(get_metrics_service)],
    server_service: Annotated[ServerService, Depends(get_server_service)],
    start_time: datetime | None = Query(None, description="开始时间"),
    end_time: datetime | None = Query(None, description="结束时间"),
    limit: int = Query(100, ge=1, le=1000, description="返回数量限制"),
):
    """
    获取服务器历史指标

    默认返回最近24小时的数据

    需要Bearer Token认证
    """
    # 验证服务器所有权
    server = await server_service.get_server_by_id(server_id, current_user.id)
    if not server:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Server not found",
        )

    # 获取历史指标
    metrics = await metrics_service.get_metrics_history(
        server_id=server_id,
        start_time=start_time,
        end_time=end_time,
        limit=limit,
    )

    return MetricsHistoryResponse(
        total=len(metrics),
        items=[MetricResponse.model_validate(m) for m in metrics],
    )


@router.get("/servers/{server_id}/summary", response_model=MetricsSummaryResponse)
async def get_metrics_summary(
    server_id: UUID,
    current_user: CurrentUser,
    metrics_service: Annotated[MetricsService, Depends(get_metrics_service)],
    server_service: Annotated[ServerService, Depends(get_server_service)],
    hours: int = Query(24, ge=1, le=168, description="统计时间范围（小时，最多7天）"),
):
    """
    获取服务器指标统计摘要

    返回指定时间范围内的平均值和峰值

    需要Bearer Token认证
    """
    # 验证服务器所有权
    server = await server_service.get_server_by_id(server_id, current_user.id)
    if not server:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Server not found",
        )

    # 获取统计摘要
    summary = await metrics_service.get_metrics_summary(server_id, hours)

    return MetricsSummaryResponse(**summary)
