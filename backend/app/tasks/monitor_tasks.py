"""
监控相关的Celery任务
"""
import asyncio

from sqlalchemy import select

from app.config import settings
from app.database import get_celery_async_session
from app.models.server import Server
from app.services.metrics_service import MetricsService
from app.services.ssh_service import SSHService
from app.tasks.celery_app import celery_app
from app.utils.logger import logger


@celery_app.task(name="app.tasks.monitor_tasks.collect_all_servers_metrics")
def collect_all_servers_metrics():
    """
    采集所有服务器的指标

    定时任务，每分钟执行一次
    """
    logger.info("Starting to collect metrics for all servers")

    # 使用asyncio运行异步任务
    asyncio.run(_collect_all_servers_metrics_async())

    logger.info("Finished collecting metrics for all servers")


async def _collect_all_servers_metrics_async():
    """异步采集所有服务器指标"""
    # 为每个任务创建独立的会话，避免事件循环冲突
    CeleryAsyncSession = get_celery_async_session()
    async with CeleryAsyncSession() as db:
        try:
            # 查询所有激活的服务器
            result = await db.execute(
                select(Server).where(Server.status != "offline")
            )
            servers = result.scalars().all()

            logger.info(f"Found {len(servers)} servers to collect metrics")

            metrics_service = MetricsService(db)

            # 并发采集所有服务器的指标
            tasks = []
            for server in servers:
                task = _collect_server_metrics(server, metrics_service)
                tasks.append(task)

            # 等待所有任务完成
            results = await asyncio.gather(*tasks, return_exceptions=True)

            # 统计成功和失败数量
            success_count = sum(1 for r in results if r is True)
            fail_count = sum(1 for r in results if r is not True)

            logger.info(
                f"Metrics collection completed: {success_count} succeeded, {fail_count} failed"
            )

        except Exception as e:
            logger.error(f"Error in collect_all_servers_metrics: {str(e)}")


async def _collect_server_metrics(server: Server, metrics_service: MetricsService) -> bool:
    """
    采集单个服务器的指标

    Args:
        server: 服务器对象
        metrics_service: 指标服务

    Returns:
        bool: 是否成功
    """
    try:
        # 创建SSH服务
        ssh_service = await SSHService.create_from_encrypted(
            host=server.host,
            port=server.port,
            username=server.ssh_username or "",
            encrypted_password=server.ssh_password_encrypted,
            encrypted_key=server.ssh_key_encrypted,
        )

        # 采集指标
        await metrics_service.collect_metrics(server.id, ssh_service)

        # 更新服务器状态为在线
        from datetime import datetime

        server.status = "online"
        server.last_checked_at = datetime.utcnow()
        await metrics_service.db.commit()

        logger.debug(f"Successfully collected metrics for server {server.name}")
        return True

    except Exception as e:
        logger.warning(f"Failed to collect metrics for server {server.name}: {str(e)}")

        # 更新服务器状态为错误
        from datetime import datetime

        server.status = "error"
        server.last_checked_at = datetime.utcnow()
        await metrics_service.db.commit()

        return False


@celery_app.task(name="app.tasks.monitor_tasks.cleanup_old_metrics")
def cleanup_old_metrics():
    """
    清理旧的指标数据

    定时任务，每天执行一次
    """
    logger.info("Starting to cleanup old metrics")

    # 使用asyncio运行异步任务
    deleted_count = asyncio.run(_cleanup_old_metrics_async())

    logger.info(f"Cleaned up {deleted_count} old metric records")


async def _cleanup_old_metrics_async() -> int:
    """异步清理旧指标"""
    # 为每个任务创建独立的会话，避免事件循环冲突
    CeleryAsyncSession = get_celery_async_session()
    async with CeleryAsyncSession() as db:
        try:
            metrics_service = MetricsService(db)
            deleted_count = await metrics_service.cleanup_old_metrics(
                days=settings.metrics_retention_days
            )
            return deleted_count

        except Exception as e:
            logger.error(f"Error in cleanup_old_metrics: {str(e)}")
            return 0


@celery_app.task(name="app.tasks.monitor_tasks.collect_server_metrics_by_id")
def collect_server_metrics_by_id(server_id: str):
    """
    采集指定服务器的指标

    Args:
        server_id: 服务器ID（字符串格式的UUID）
    """
    from uuid import UUID

    logger.info(f"Collecting metrics for server {server_id}")

    # 使用asyncio运行异步任务
    success = asyncio.run(_collect_server_metrics_by_id_async(UUID(server_id)))

    if success:
        logger.info(f"Successfully collected metrics for server {server_id}")
    else:
        logger.warning(f"Failed to collect metrics for server {server_id}")

    return success


async def _collect_server_metrics_by_id_async(server_id) -> bool:
    """异步采集指定服务器的指标"""
    # 为每个任务创建独立的会话，避免事件循环冲突
    CeleryAsyncSession = get_celery_async_session()
    async with CeleryAsyncSession() as db:
        try:
            # 查询服务器
            result = await db.execute(select(Server).where(Server.id == server_id))
            server = result.scalar_one_or_none()

            if not server:
                logger.error(f"Server {server_id} not found")
                return False

            metrics_service = MetricsService(db)
            return await _collect_server_metrics(server, metrics_service)

        except Exception as e:
            logger.error(f"Error collecting metrics for server {server_id}: {str(e)}")
            return False
