"""
服务器监控数据模型
"""

import uuid
from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import BigInteger, DateTime, Float, ForeignKey, Integer
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base

if TYPE_CHECKING:
    from app.models.server import Server


class ServerMetric(Base):
    """服务器监控数据模型"""

    __tablename__ = "server_metrics"

    # 主键
    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)

    # 服务器外键
    server_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("servers.id", ondelete="CASCADE"), nullable=False, index=True
    )

    # CPU信息
    cpu_usage_percent: Mapped[float | None] = mapped_column(Float)
    cpu_cores: Mapped[int | None] = mapped_column(Integer)

    # 内存信息
    memory_total_mb: Mapped[int | None] = mapped_column(BigInteger)
    memory_used_mb: Mapped[int | None] = mapped_column(BigInteger)
    memory_usage_percent: Mapped[float | None] = mapped_column(Float)

    # 磁盘信息
    disk_total_gb: Mapped[int | None] = mapped_column(BigInteger)
    disk_used_gb: Mapped[int | None] = mapped_column(BigInteger)
    disk_usage_percent: Mapped[float | None] = mapped_column(Float)

    # 网络信息
    network_bytes_sent: Mapped[int | None] = mapped_column(BigInteger)
    network_bytes_recv: Mapped[int | None] = mapped_column(BigInteger)

    # 系统信息
    uptime_seconds: Mapped[int | None] = mapped_column(BigInteger)
    load_average: Mapped[dict | None] = mapped_column(
        JSONB
    )  # {"1min": 0.5, "5min": 0.3, "15min": 0.2}

    # 采集时间
    collected_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, nullable=False, index=True
    )

    # 关系
    server: Mapped["Server"] = relationship("Server", back_populates="metrics")

    def __repr__(self) -> str:
        return f"<ServerMetric {self.server_id} at {self.collected_at}>"

    @property
    def memory_free_mb(self) -> int | None:
        """空闲内存（MB）"""
        if self.memory_total_mb is not None and self.memory_used_mb is not None:
            return self.memory_total_mb - self.memory_used_mb
        return None

    @property
    def disk_free_gb(self) -> int | None:
        """空闲磁盘（GB）"""
        if self.disk_total_gb is not None and self.disk_used_gb is not None:
            return self.disk_total_gb - self.disk_used_gb
        return None

    def to_dict(self) -> dict:
        """转换为字典"""
        return {
            "cpu_usage_percent": self.cpu_usage_percent,
            "cpu_cores": self.cpu_cores,
            "memory_total_mb": self.memory_total_mb,
            "memory_used_mb": self.memory_used_mb,
            "memory_usage_percent": self.memory_usage_percent,
            "disk_total_gb": self.disk_total_gb,
            "disk_used_gb": self.disk_used_gb,
            "disk_usage_percent": self.disk_usage_percent,
            "network_bytes_sent": self.network_bytes_sent,
            "network_bytes_recv": self.network_bytes_recv,
            "uptime_seconds": self.uptime_seconds,
            "load_average": self.load_average,
            "collected_at": self.collected_at.isoformat() if self.collected_at else None,
        }
