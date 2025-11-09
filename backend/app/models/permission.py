"""
用户服务器权限模型
"""

import uuid
from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import DateTime, ForeignKey, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base

if TYPE_CHECKING:
    from app.models.server import Server
    from app.models.user import User


class UserServerPermission(Base):
    """用户服务器权限模型"""

    __tablename__ = "user_server_permissions"
    __table_args__ = (UniqueConstraint("user_id", "server_id", name="uq_user_server"),)

    # 主键
    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)

    # 外键
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )
    server_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("servers.id", ondelete="CASCADE"), nullable=False, index=True
    )

    # 权限标志
    can_read: Mapped[bool] = mapped_column(default=False, nullable=False)
    can_write: Mapped[bool] = mapped_column(default=False, nullable=False)
    can_execute: Mapped[bool] = mapped_column(default=False, nullable=False)
    can_admin: Mapped[bool] = mapped_column(default=False, nullable=False)

    # 授权信息
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)
    granted_by: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id"))

    # 关系
    user: Mapped["User"] = relationship(
        "User", back_populates="permissions", foreign_keys=[user_id]
    )
    server: Mapped["Server"] = relationship("Server", back_populates="permissions")
    granter: Mapped["User | None"] = relationship("User", foreign_keys=[granted_by])

    def __repr__(self) -> str:
        permissions = []
        if self.can_read:
            permissions.append("read")
        if self.can_write:
            permissions.append("write")
        if self.can_execute:
            permissions.append("execute")
        if self.can_admin:
            permissions.append("admin")
        return f"<Permission {self.user_id} -> {self.server_id}: {','.join(permissions)}>"
