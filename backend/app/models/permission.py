"""
用户服务器权限模型
"""
import uuid
from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import DateTime, ForeignKey, String, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base

if TYPE_CHECKING:
    from app.models.user import User
    from app.models.server import Server


class UserServerPermission(Base):
    """用户服务器权限模型"""

    __tablename__ = "user_server_permissions"
    __table_args__ = (
        UniqueConstraint("user_id", "server_id", name="uq_user_server"),
    )

    # 主键
    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )

    # 外键
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )
    server_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("servers.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )

    # 权限类型
    permission: Mapped[str] = mapped_column(
        String(20), nullable=False
    )  # read, write, execute, admin

    # 授权信息
    granted_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, nullable=False
    )
    granted_by: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id")
    )

    # 关系
    user: Mapped["User"] = relationship("User", back_populates="permissions", foreign_keys=[user_id])
    server: Mapped["Server"] = relationship("Server", back_populates="permissions")
    granter: Mapped["User | None"] = relationship("User", foreign_keys=[granted_by])

    def __repr__(self) -> str:
        return f"<Permission {self.user_id} -> {self.server_id}: {self.permission}>"

    @property
    def can_read(self) -> bool:
        """是否有读权限"""
        return self.permission in ["read", "write", "execute", "admin"]

    @property
    def can_write(self) -> bool:
        """是否有写权限"""
        return self.permission in ["write", "execute", "admin"]

    @property
    def can_execute(self) -> bool:
        """是否有执行权限"""
        return self.permission in ["execute", "admin"]

    @property
    def is_admin(self) -> bool:
        """是否有管理员权限"""
        return self.permission == "admin"
