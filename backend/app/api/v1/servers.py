"""
服务器管理API路由
"""

from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.dependencies import CurrentUser
from app.schemas.server import (
    ConnectionTestResponse,
    ServerCreate,
    ServerDetailResponse,
    ServerListResponse,
    ServerResponse,
    ServerUpdate,
)
from app.services.server_service import ServerService

router = APIRouter()


async def get_server_service(db: Annotated[AsyncSession, Depends(get_db)]) -> ServerService:
    """获取服务器服务依赖"""
    return ServerService(db)


@router.post("", response_model=ServerResponse, status_code=status.HTTP_201_CREATED)
async def create_server(
    server_data: ServerCreate,
    current_user: CurrentUser,
    server_service: Annotated[ServerService, Depends(get_server_service)],
):
    """
    创建服务器

    - **name**: 服务器名称
    - **host**: 主机地址（IP或域名）
    - **port**: SSH端口（默认22）
    - **ssh_username**: SSH用户名
    - **ssh_password**: SSH密码（与ssh_key二选一）
    - **ssh_key**: SSH私钥（与ssh_password二选一）
    - **description**: 服务器描述（可选）
    - **tags**: 服务器标签（可选）

    需要Bearer Token认证
    """
    try:
        server = await server_service.create_server(server_data, current_user.id)
        return server
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )


@router.get("", response_model=ServerListResponse)
async def get_servers(
    current_user: CurrentUser,
    server_service: Annotated[ServerService, Depends(get_server_service)],
    page: int = Query(1, ge=1, description="页码"),
    size: int = Query(20, ge=1, le=100, description="每页数量"),
    status: str
    | None = Query(None, pattern="^(online|offline|error|unknown)$", description="状态筛选"),
    tags: str | None = Query(None, description="标签筛选（逗号分隔）"),
    search: str | None = Query(None, description="搜索关键词"),
):
    """
    获取服务器列表

    支持分页、状态筛选、标签筛选、关键词搜索

    需要Bearer Token认证
    """
    # 解析标签
    tag_list = None
    if tags:
        tag_list = [t.strip() for t in tags.split(",") if t.strip()]

    servers = await server_service.get_servers(
        user_id=current_user.id,
        page=page,
        size=size,
        status=status,
        tags=tag_list,
        search=search,
    )

    return servers


@router.get("/{server_id}", response_model=ServerDetailResponse)
async def get_server(
    server_id: UUID,
    current_user: CurrentUser,
    server_service: Annotated[ServerService, Depends(get_server_service)],
):
    """
    获取服务器详情

    需要Bearer Token认证
    """
    server = await server_service.get_server_by_id(server_id, current_user.id)

    if not server:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Server not found",
        )

    return ServerDetailResponse.model_validate(server)


@router.put("/{server_id}", response_model=ServerResponse)
async def update_server(
    server_id: UUID,
    server_data: ServerUpdate,
    current_user: CurrentUser,
    server_service: Annotated[ServerService, Depends(get_server_service)],
):
    """
    更新服务器信息

    可以更新任意字段，未提供的字段保持不变

    需要Bearer Token认证
    """
    try:
        server = await server_service.update_server(server_id, current_user.id, server_data)
        return server
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e),
        )


@router.delete("/{server_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_server(
    server_id: UUID,
    current_user: CurrentUser,
    server_service: Annotated[ServerService, Depends(get_server_service)],
):
    """
    删除服务器

    会同时删除该服务器的所有监控数据、权限配置等

    需要Bearer Token认证
    """
    try:
        await server_service.delete_server(server_id, current_user.id)
        return None
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e),
        )


@router.post("/{server_id}/test-connection", response_model=ConnectionTestResponse)
async def test_server_connection(
    server_id: UUID,
    current_user: CurrentUser,
    server_service: Annotated[ServerService, Depends(get_server_service)],
):
    """
    测试服务器连接

    尝试建立SSH连接并执行简单命令

    返回连接状态、消息和延迟时间

    需要Bearer Token认证
    """
    try:
        result = await server_service.test_connection(server_id, current_user.id)
        return result
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e),
        )
