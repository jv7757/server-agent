"""
用户模型
"""
import uuid
from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import Boolean, DateTime, String
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base

if TYPE_CHECKING:
    from app.models.server import Server
    from app.models.permission import UserServerPermission
    from app.models.chat import ChatHistory
    from app.models.audit import AuditLog


class User(Base):
    """用户模型"""

    __tablename__ = "users"

    # 主键
    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )

    # 基本信息
    username: Mapped[str] = mapped_column(String(50), unique=True, index=True, nullable=False)
    email: Mapped[str] = mapped_column(String(100), unique=True, index=True, nullable=False)
    hashed_password: Mapped[str] = mapped_column(String(255), nullable=False)
    full_name: Mapped[str | None] = mapped_column(String(100))

    # 角色和状态
    role: Mapped[str] = mapped_column(
        String(20), default="user", nullable=False
    )  # admin, user, viewer
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    # 时间戳
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False
    )

    # 关系
    servers: Mapped[list["Server"]] = relationship(
        "Server", back_populates="owner", cascade="all, delete-orphan"
    )
    permissions: Mapped[list["UserServerPermission"]] = relationship(
        "UserServerPermission", back_populates="user", cascade="all, delete-orphan"
    )
    chat_history: Mapped[list["ChatHistory"]] = relationship(
        "ChatHistory", back_populates="user", cascade="all, delete-orphan"
    )
    audit_logs: Mapped[list["AuditLog"]] = relationship(
        "AuditLog", back_populates="user"
    )

    def __repr__(self) -> str:
        return f"<User {self.username}>"

    @property
    def is_admin(self) -> bool:
        """是否为管理员"""
        return self.role == "admin"

    @property
    def is_viewer(self) -> bool:
        """是否为只读用户"""
        return self.role == "viewer"
