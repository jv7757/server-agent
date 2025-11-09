"""
审计日志API路由
"""

from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import and_, desc, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.dependencies import CurrentUser
from app.models.audit import AuditLog
from app.models.server import Server
from app.models.user import User
from app.schemas.audit import AuditLogListResponse, AuditLogResponse

router = APIRouter()


@router.get("/audit-logs", response_model=AuditLogListResponse)
async def get_audit_logs(
    current_user: CurrentUser,
    db: Annotated[AsyncSession, Depends(get_db)],
    page: int = Query(1, ge=1, description="页码"),
    size: int = Query(20, ge=1, le=100, description="每页数量"),
    user_id: UUID | None = Query(None, description="按用户ID筛选"),
    server_id: UUID | None = Query(None, description="按服务器ID筛选"),
    action: str | None = Query(None, description="按操作类型筛选"),
    resource_type: str | None = Query(None, description="按资源类型筛选"),
    search: str | None = Query(None, description="搜索关键词"),
):
    """
    获取审计日志列表（仅管理员）

    支持筛选和分页：
    - user_id: 按用户筛选
    - server_id: 按服务器筛选
    - action: 按操作类型筛选（execute_command, create_server等）
    - resource_type: 按资源类型筛选（server, user, permission等）
    - search: 搜索用户名或服务器名

    需要管理员权限
    """
    # 检查管理员权限
    if current_user.role != "admin":
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="需要管理员权限")

    # 构建查询条件
    conditions = []

    if user_id:
        conditions.append(AuditLog.user_id == user_id)

    if server_id:
        conditions.append(AuditLog.server_id == server_id)

    if action:
        conditions.append(AuditLog.action == action)

    if resource_type:
        conditions.append(AuditLog.resource_type == resource_type)

    # 构建基础查询，关联用户和服务器表以获取名称
    query = (
        select(AuditLog, User.username, Server.name.label("server_name"))
        .outerjoin(User, AuditLog.user_id == User.id)
        .outerjoin(Server, AuditLog.server_id == Server.id)
    )

    # 添加筛选条件
    if conditions:
        query = query.where(and_(*conditions))

    # 搜索功能
    if search:
        search_pattern = f"%{search}%"
        query = query.where(
            or_(
                User.username.ilike(search_pattern),
                Server.name.ilike(search_pattern),
                AuditLog.action.ilike(search_pattern),
            )
        )

    # 获取总数
    count_query = select(AuditLog.id)
    if conditions:
        count_query = count_query.where(and_(*conditions))

    if search:
        count_query = (
            count_query.outerjoin(User, AuditLog.user_id == User.id)
            .outerjoin(Server, AuditLog.server_id == Server.id)
            .where(
                or_(
                    User.username.ilike(search_pattern),
                    Server.name.ilike(search_pattern),
                    AuditLog.action.ilike(search_pattern),
                )
            )
        )

    total_result = await db.execute(count_query)
    total = len(total_result.all())

    # 分页和排序
    query = query.order_by(desc(AuditLog.created_at)).offset((page - 1) * size).limit(size)

    result = await db.execute(query)
    rows = result.all()

    # 组装响应数据
    items = []
    for audit_log, username, server_name in rows:
        item = AuditLogResponse(
            id=audit_log.id,
            user_id=str(audit_log.user_id) if audit_log.user_id else None,
            username=username,
            server_id=str(audit_log.server_id) if audit_log.server_id else None,
            server_name=server_name,
            action=audit_log.action,
            resource_type=audit_log.resource_type,
            details=audit_log.details,
            ip_address=str(audit_log.ip_address) if audit_log.ip_address else None,
            created_at=audit_log.created_at,
        )
        items.append(item)

    return AuditLogListResponse(total=total, page=page, size=size, items=items)


@router.get("/audit-logs/{log_id}", response_model=AuditLogResponse)
async def get_audit_log(
    log_id: int,
    current_user: CurrentUser,
    db: Annotated[AsyncSession, Depends(get_db)],
):
    """
    获取单条审计日志详情（仅管理员）

    需要管理员权限
    """
    # 检查管理员权限
    if current_user.role != "admin":
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="需要管理员权限")

    # 查询日志，关联用户和服务器
    query = (
        select(AuditLog, User.username, Server.name.label("server_name"))
        .outerjoin(User, AuditLog.user_id == User.id)
        .outerjoin(Server, AuditLog.server_id == Server.id)
        .where(AuditLog.id == log_id)
    )

    result = await db.execute(query)
    row = result.first()

    if not row:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="审计日志不存在")

    audit_log, username, server_name = row

    return AuditLogResponse(
        id=audit_log.id,
        user_id=str(audit_log.user_id) if audit_log.user_id else None,
        username=username,
        server_id=str(audit_log.server_id) if audit_log.server_id else None,
        server_name=server_name,
        action=audit_log.action,
        resource_type=audit_log.resource_type,
        details=audit_log.details,
        ip_address=str(audit_log.ip_address) if audit_log.ip_address else None,
        created_at=audit_log.created_at,
    )
