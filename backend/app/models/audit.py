"""
操作审计日志模型
"""

import uuid
from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import DateTime, ForeignKey, String
from sqlalchemy.dialects.postgresql import INET, JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base

if TYPE_CHECKING:
    from app.models.server import Server
    from app.models.user import User


class AuditLog(Base):
    """操作审计日志模型"""

    __tablename__ = "audit_logs"

    # 主键
    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)

    # 外键
    user_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"), index=True
    )
    server_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("servers.id", ondelete="SET NULL"), index=True
    )

    # 操作信息
    action: Mapped[str] = mapped_column(
        String(50), nullable=False, index=True
    )  # create, update, delete, execute_command, login, logout, etc.
    resource_type: Mapped[str | None] = mapped_column(
        String(50), index=True
    )  # server, user, permission, etc.

    # 详细信息（JSON格式存储操作详情）
    details: Mapped[dict | None] = mapped_column(JSONB)

    # IP地址
    ip_address: Mapped[str | None] = mapped_column(INET)

    # 时间戳
    created_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, nullable=False, index=True
    )

    # 关系
    user: Mapped["User | None"] = relationship("User", back_populates="audit_logs")
    server: Mapped["Server | None"] = relationship("Server", back_populates="audit_logs")

    def __repr__(self) -> str:
        return f"<AuditLog {self.action} by {self.user_id} at {self.created_at}>"

    def to_dict(self) -> dict:
        """转换为字典"""
        return {
            "id": self.id,
            "user_id": str(self.user_id) if self.user_id else None,
            "server_id": str(self.server_id) if self.server_id else None,
            "action": self.action,
            "resource_type": self.resource_type,
            "details": self.details,
            "ip_address": str(self.ip_address) if self.ip_address else None,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }
