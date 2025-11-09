"""
用户管理API路由（仅管理员）
"""

from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import desc, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.dependencies import CurrentUser
from app.models.user import User
from app.schemas.user import (
    UserCreate,
    UserListResponse,
    UserResponse,
    UserUpdate,
    UserUpdateRole,
    UserUpdateStatus,
)
from app.services.auth_service import AuthService
from app.utils.logger import logger

router = APIRouter()


def check_admin_permission(current_user: User):
    """检查管理员权限"""
    if current_user.role != "admin":
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="需要管理员权限")


@router.get("/users", response_model=UserListResponse)
async def get_users(
    current_user: CurrentUser,
    db: Annotated[AsyncSession, Depends(get_db)],
    page: int = Query(1, ge=1, description="页码"),
    size: int = Query(20, ge=1, le=100, description="每页数量"),
    role: str | None = Query(None, description="按角色筛选"),
    is_active: bool | None = Query(None, description="按状态筛选"),
    search: str | None = Query(None, description="搜索用户名或邮箱"),
):
    """
    获取用户列表（仅管理员）

    支持筛选和搜索：
    - role: 按角色筛选（admin/user/viewer）
    - is_active: 按状态筛选
    - search: 搜索用户名或邮箱

    需要管理员权限
    """
    check_admin_permission(current_user)

    # 构建查询
    query = select(User)

    # 角色筛选
    if role:
        query = query.where(User.role == role)

    # 状态筛选
    if is_active is not None:
        query = query.where(User.is_active == is_active)

    # 搜索
    if search:
        search_pattern = f"%{search}%"
        query = query.where(
            or_(
                User.username.ilike(search_pattern),
                User.email.ilike(search_pattern),
                User.full_name.ilike(search_pattern),
            )
        )

    # 获取总数
    count_query = select(User.id)
    if role:
        count_query = count_query.where(User.role == role)
    if is_active is not None:
        count_query = count_query.where(User.is_active == is_active)
    if search:
        count_query = count_query.where(
            or_(
                User.username.ilike(search_pattern),
                User.email.ilike(search_pattern),
                User.full_name.ilike(search_pattern),
            )
        )

    total_result = await db.execute(count_query)
    total = len(total_result.all())

    # 分页和排序
    query = query.order_by(desc(User.created_at)).offset((page - 1) * size).limit(size)

    result = await db.execute(query)
    users = result.scalars().all()

    items = [UserResponse.model_validate(user) for user in users]

    return UserListResponse(total=total, page=page, size=size, items=items)


@router.get("/users/{user_id}", response_model=UserResponse)
async def get_user(
    user_id: UUID,
    current_user: CurrentUser,
    db: Annotated[AsyncSession, Depends(get_db)],
):
    """
    获取用户详情（仅管理员）

    需要管理员权限
    """
    check_admin_permission(current_user)

    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()

    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="用户不存在")

    return UserResponse.model_validate(user)


@router.post("/users", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def create_user(
    user_data: UserCreate,
    current_user: CurrentUser,
    db: Annotated[AsyncSession, Depends(get_db)],
):
    """
    创建用户（仅管理员）

    需要管理员权限
    """
    check_admin_permission(current_user)

    auth_service = AuthService(db)

    try:
        user = await auth_service.register(user_data)
        logger.info(f"Admin {current_user.username} created user: {user.username}")
        return user
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.put("/users/{user_id}", response_model=UserResponse)
async def update_user(
    user_id: UUID,
    user_data: UserUpdate,
    current_user: CurrentUser,
    db: Annotated[AsyncSession, Depends(get_db)],
):
    """
    更新用户信息（仅管理员）

    可更新：email, full_name, password

    需要管理员权限
    """
    check_admin_permission(current_user)

    # 查询用户
    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()

    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="用户不存在")

    # 更新字段
    update_data = user_data.model_dump(exclude_unset=True)

    if "email" in update_data:
        # 检查邮箱是否已被使用
        email_check = await db.execute(
            select(User).where(User.email == update_data["email"], User.id != user_id)
        )
        if email_check.scalar_one_or_none():
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="邮箱已被使用")
        user.email = update_data["email"]

    if "full_name" in update_data:
        user.full_name = update_data["full_name"]

    if "password" in update_data:
        # 密码需要加密
        from app.core.security import hash_password

        user.hashed_password = hash_password(update_data["password"])

    await db.commit()
    await db.refresh(user)

    logger.info(f"Admin {current_user.username} updated user: {user.username}")

    return UserResponse.model_validate(user)


@router.delete("/users/{user_id}", status_code=status.HTTP_200_OK)
async def delete_user(
    user_id: UUID,
    current_user: CurrentUser,
    db: Annotated[AsyncSession, Depends(get_db)],
):
    """
    删除用户（仅管理员）

    注意：删除用户会级联删除其所有相关数据（服务器、聊天记录等）

    需要管理员权限
    """
    check_admin_permission(current_user)

    # 不能删除自己
    if user_id == current_user.id:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="不能删除自己的账号")

    # 查询用户
    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()

    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="用户不存在")

    username = user.username

    # 删除用户
    await db.delete(user)
    await db.commit()

    logger.info(f"Admin {current_user.username} deleted user: {username}")

    return {"message": f"用户 {username} 已删除", "deleted_user_id": str(user_id)}


@router.put("/users/{user_id}/role", response_model=UserResponse)
async def update_user_role(
    user_id: UUID,
    role_data: UserUpdateRole,
    current_user: CurrentUser,
    db: Annotated[AsyncSession, Depends(get_db)],
):
    """
    修改用户角色（仅管理员）

    可选角色：admin, user, viewer

    需要管理员权限
    """
    check_admin_permission(current_user)

    # 不能修改自己的角色
    if user_id == current_user.id:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="不能修改自己的角色")

    # 查询用户
    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()

    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="用户不存在")

    old_role = user.role
    user.role = role_data.role

    await db.commit()
    await db.refresh(user)

    logger.info(
        f"Admin {current_user.username} changed user {user.username} role: "
        f"{old_role} -> {role_data.role}"
    )

    return UserResponse.model_validate(user)


@router.put("/users/{user_id}/status", response_model=UserResponse)
async def update_user_status(
    user_id: UUID,
    status_data: UserUpdateStatus,
    current_user: CurrentUser,
    db: Annotated[AsyncSession, Depends(get_db)],
):
    """
    启用/禁用用户（仅管理员）

    需要管理员权限
    """
    check_admin_permission(current_user)

    # 不能修改自己的状态
    if user_id == current_user.id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="不能修改自己的账号状态"
        )

    # 查询用户
    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()

    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="用户不存在")

    user.is_active = status_data.is_active

    await db.commit()
    await db.refresh(user)

    status_text = "启用" if status_data.is_active else "禁用"
    logger.info(f"Admin {current_user.username} {status_text} user: {user.username}")

    return UserResponse.model_validate(user)
