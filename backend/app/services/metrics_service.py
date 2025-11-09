"""
服务器监控服务
"""
from datetime import datetime, timedelta
from typing import Any
from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.metric import ServerMetric
from app.services.ssh_service import SSHService
from app.utils.logger import logger


class MetricsService:
    """服务器监控服务类"""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def collect_metrics(self, server_id: UUID, ssh_service: SSHService) -> ServerMetric:
        """
        采集服务器指标

        Args:
            server_id: 服务器ID
            ssh_service: SSH服务实例

        Returns:
            ServerMetric: 采集的指标数据

        Raises:
            Exception: 采集失败
        """
        try:
            # 连接SSH
            await ssh_service.connect()

            # 并发执行所有采集命令
            metrics_data = await self._collect_all_metrics(ssh_service)

            # 断开连接
            await ssh_service.disconnect()

            # 创建指标记录
            metric = ServerMetric(
                server_id=server_id,
                cpu_usage_percent=metrics_data.get("cpu_usage_percent"),
                cpu_cores=metrics_data.get("cpu_cores"),
                memory_total_mb=metrics_data.get("memory_total_mb"),
                memory_used_mb=metrics_data.get("memory_used_mb"),
                memory_usage_percent=metrics_data.get("memory_usage_percent"),
                disk_total_gb=metrics_data.get("disk_total_gb"),
                disk_used_gb=metrics_data.get("disk_used_gb"),
                disk_usage_percent=metrics_data.get("disk_usage_percent"),
                network_bytes_sent=metrics_data.get("network_bytes_sent"),
                network_bytes_recv=metrics_data.get("network_bytes_recv"),
                uptime_seconds=metrics_data.get("uptime_seconds"),
                load_average=metrics_data.get("load_average"),
                collected_at=datetime.utcnow(),
            )

            self.db.add(metric)
            await self.db.commit()
            await self.db.refresh(metric)

            logger.info(f"Metrics collected for server {server_id}")

            return metric

        except Exception as e:
            logger.error(f"Failed to collect metrics for server {server_id}: {str(e)}")
            raise Exception(f"Metrics collection failed: {str(e)}")

    async def _collect_all_metrics(self, ssh_service: SSHService) -> dict[str, Any]:
        """
        采集所有指标数据

        Args:
            ssh_service: SSH服务实例

        Returns:
            dict: 指标数据
        """
        metrics = {}

        # 采集CPU信息
        try:
            cpu_data = await self._get_cpu_metrics(ssh_service)
            metrics.update(cpu_data)
        except Exception as e:
            logger.warning(f"Failed to collect CPU metrics: {str(e)}")

        # 采集内存信息
        try:
            memory_data = await self._get_memory_metrics(ssh_service)
            metrics.update(memory_data)
        except Exception as e:
            logger.warning(f"Failed to collect memory metrics: {str(e)}")

        # 采集磁盘信息
        try:
            disk_data = await self._get_disk_metrics(ssh_service)
            metrics.update(disk_data)
        except Exception as e:
            logger.warning(f"Failed to collect disk metrics: {str(e)}")

        # 采集网络信息
        try:
            network_data = await self._get_network_metrics(ssh_service)
            metrics.update(network_data)
        except Exception as e:
            logger.warning(f"Failed to collect network metrics: {str(e)}")

        # 采集系统信息
        try:
            system_data = await self._get_system_metrics(ssh_service)
            metrics.update(system_data)
        except Exception as e:
            logger.warning(f"Failed to collect system metrics: {str(e)}")

        return metrics

    async def _get_cpu_metrics(self, ssh_service: SSHService) -> dict[str, Any]:
        """获取CPU指标"""
        # 获取CPU核心数
        cpu_cores_result = await ssh_service.execute_command("nproc")
        cpu_cores = int(cpu_cores_result["stdout"].strip())

        # 获取CPU使用率（通过top命令）
        # 使用批处理模式执行一次，获取CPU空闲百分比
        cpu_usage_result = await ssh_service.execute_command(
            "top -bn1 | grep 'Cpu(s)' | awk '{print $8}'"
        )
        cpu_idle = float(cpu_usage_result["stdout"].strip().replace(",", "."))
        cpu_usage_percent = round(100 - cpu_idle, 2)

        # 获取负载平均值
        load_result = await ssh_service.execute_command("cat /proc/loadavg")
        load_parts = load_result["stdout"].strip().split()
        load_average = {
            "1min": float(load_parts[0]),
            "5min": float(load_parts[1]),
            "15min": float(load_parts[2]),
        }

        return {
            "cpu_cores": cpu_cores,
            "cpu_usage_percent": cpu_usage_percent,
            "load_average": load_average,
        }

    async def _get_memory_metrics(self, ssh_service: SSHService) -> dict[str, Any]:
        """获取内存指标"""
        # 使用free命令获取内存信息（MB）
        memory_result = await ssh_service.execute_command("free -m | grep Mem:")
        memory_parts = memory_result["stdout"].strip().split()

        memory_total_mb = int(memory_parts[1])
        memory_used_mb = int(memory_parts[2])
        memory_usage_percent = round((memory_used_mb / memory_total_mb) * 100, 2)

        return {
            "memory_total_mb": memory_total_mb,
            "memory_used_mb": memory_used_mb,
            "memory_usage_percent": memory_usage_percent,
        }

    async def _get_disk_metrics(self, ssh_service: SSHService) -> dict[str, Any]:
        """获取磁盘指标"""
        # 使用df命令获取根分区磁盘使用情况
        disk_result = await ssh_service.execute_command("df -BG / | tail -1")
        disk_parts = disk_result["stdout"].strip().split()

        # 解析磁盘大小（移除G后缀）
        disk_total_gb = int(disk_parts[1].replace("G", ""))
        disk_used_gb = int(disk_parts[2].replace("G", ""))
        disk_usage_percent = float(disk_parts[4].replace("%", ""))

        return {
            "disk_total_gb": disk_total_gb,
            "disk_used_gb": disk_used_gb,
            "disk_usage_percent": disk_usage_percent,
        }

    async def _get_network_metrics(self, ssh_service: SSHService) -> dict[str, Any]:
        """获取网络指标"""
        # 读取网络统计信息
        network_result = await ssh_service.execute_command(
            "cat /proc/net/dev | grep -E 'eth0|ens|enp' | head -1"
        )

        if network_result["stdout"].strip():
            parts = network_result["stdout"].strip().split()
            network_bytes_recv = int(parts[1])
            network_bytes_sent = int(parts[9])
        else:
            # 如果没有找到网络接口，使用总计
            total_result = await ssh_service.execute_command(
                "cat /proc/net/dev | tail -n +3 | awk '{rx+=$2; tx+=$10} END {print rx, tx}'"
            )
            parts = total_result["stdout"].strip().split()
            network_bytes_recv = int(parts[0]) if len(parts) > 0 else 0
            network_bytes_sent = int(parts[1]) if len(parts) > 1 else 0

        return {
            "network_bytes_sent": network_bytes_sent,
            "network_bytes_recv": network_bytes_recv,
        }

    async def _get_system_metrics(self, ssh_service: SSHService) -> dict[str, Any]:
        """获取系统指标"""
        # 获取系统运行时间（秒）
        uptime_result = await ssh_service.execute_command("cat /proc/uptime")
        uptime_seconds = int(float(uptime_result["stdout"].strip().split()[0]))

        return {
            "uptime_seconds": uptime_seconds,
        }

    async def get_current_metrics(self, server_id: UUID) -> ServerMetric | None:
        """
        获取服务器最新指标

        Args:
            server_id: 服务器ID

        Returns:
            ServerMetric: 最新指标数据
        """
        result = await self.db.execute(
            select(ServerMetric)
            .where(ServerMetric.server_id == server_id)
            .order_by(ServerMetric.collected_at.desc())
            .limit(1)
        )
        return result.scalar_one_or_none()

    async def get_metrics_history(
        self,
        server_id: UUID,
        start_time: datetime | None = None,
        end_time: datetime | None = None,
        limit: int = 100,
    ) -> list[ServerMetric]:
        """
        获取服务器历史指标

        Args:
            server_id: 服务器ID
            start_time: 开始时间
            end_time: 结束时间
            limit: 返回数量限制

        Returns:
            list[ServerMetric]: 历史指标列表
        """
        # 默认查询最近24小时
        if not start_time:
            start_time = datetime.utcnow() - timedelta(hours=24)
        if not end_time:
            end_time = datetime.utcnow()

        result = await self.db.execute(
            select(ServerMetric)
            .where(
                ServerMetric.server_id == server_id,
                ServerMetric.collected_at >= start_time,
                ServerMetric.collected_at <= end_time,
            )
            .order_by(ServerMetric.collected_at.desc())
            .limit(limit)
        )

        return list(result.scalars().all())

    async def get_metrics_summary(
        self, server_id: UUID, hours: int = 24
    ) -> dict[str, Any]:
        """
        获取服务器指标摘要统计

        Args:
            server_id: 服务器ID
            hours: 统计时间范围（小时）

        Returns:
            dict: 统计摘要
        """
        start_time = datetime.utcnow() - timedelta(hours=hours)

        # 查询统计数据
        result = await self.db.execute(
            select(
                func.avg(ServerMetric.cpu_usage_percent).label("avg_cpu"),
                func.max(ServerMetric.cpu_usage_percent).label("max_cpu"),
                func.avg(ServerMetric.memory_usage_percent).label("avg_memory"),
                func.max(ServerMetric.memory_usage_percent).label("max_memory"),
                func.avg(ServerMetric.disk_usage_percent).label("avg_disk"),
                func.max(ServerMetric.disk_usage_percent).label("max_disk"),
                func.count().label("data_points"),
            ).where(
                ServerMetric.server_id == server_id,
                ServerMetric.collected_at >= start_time,
            )
        )

        row = result.one()

        return {
            "cpu": {
                "average": round(row.avg_cpu, 2) if row.avg_cpu else None,
                "peak": round(row.max_cpu, 2) if row.max_cpu else None,
            },
            "memory": {
                "average": round(row.avg_memory, 2) if row.avg_memory else None,
                "peak": round(row.max_memory, 2) if row.max_memory else None,
            },
            "disk": {
                "average": round(row.avg_disk, 2) if row.avg_disk else None,
                "peak": round(row.max_disk, 2) if row.max_disk else None,
            },
            "data_points": row.data_points,
            "time_range_hours": hours,
        }

    async def cleanup_old_metrics(self, days: int = 30) -> int:
        """
        清理旧的指标数据

        Args:
            days: 保留天数

        Returns:
            int: 删除的记录数
        """
        cutoff_date = datetime.utcnow() - timedelta(days=days)

        result = await self.db.execute(
            select(func.count())
            .select_from(ServerMetric)
            .where(ServerMetric.collected_at < cutoff_date)
        )
        count = result.scalar_one()

        if count > 0:
            await self.db.execute(
                select(ServerMetric).where(ServerMetric.collected_at < cutoff_date)
            )
            await self.db.commit()
            logger.info(f"Cleaned up {count} old metric records")

        return count
