"""
权限管理API路由
"""
from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status

from app.dependencies import (
    CurrentUser,
    get_permission_service,
)
from app.schemas.permission import (
    AccessibleServersResponse,
    PermissionCheck,
    PermissionCheckResponse,
    PermissionGrant,
    PermissionGrantResponse,
    PermissionResponse,
    PermissionRevoke,
    PermissionRevokeResponse,
    ServerPermissionListResponse,
    UserPermissionListResponse,
)
from app.services.permission_service import PermissionService

router = APIRouter()


@router.post("/grant", response_model=PermissionGrantResponse)
async def grant_permission(
    grant_request: PermissionGrant,
    current_user: CurrentUser,
    permission_service: Annotated[PermissionService, Depends(get_permission_service)],
):
    """
    授予权限

    只有服务器所有者、管理员、或拥有 admin 权限的用户可以授予权限

    权限类型：
    - read: 读取服务器信息和指标
    - write: 修改服务器配置
    - execute: 执行命令
    - admin: 管理权限（可以授予/撤销权限）

    需要Bearer Token认证
    """
    try:
        permission = await permission_service.grant_permission(
            server_id=grant_request.server_id,
            target_user_id=grant_request.target_user_id,
            grantor_id=current_user.id,
            permissions=grant_request.permissions,
        )

        return PermissionGrantResponse(
            success=True,
            message="权限已授予",
            permission=PermissionResponse(
                permission_id=permission.id,
                server_id=str(permission.server_id),
                user_id=str(permission.user_id),
                permissions=permission_service._format_permissions(permission),
                created_at=permission.created_at,
            ),
        )

    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=str(e),
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"授予权限失败: {str(e)}",
        )


@router.post("/revoke", response_model=PermissionRevokeResponse)
async def revoke_permission(
    revoke_request: PermissionRevoke,
    current_user: CurrentUser,
    permission_service: Annotated[PermissionService, Depends(get_permission_service)],
):
    """
    撤销权限

    只有服务器所有者、管理员、或拥有 admin 权限的用户可以撤销权限

    需要Bearer Token认证
    """
    try:
        success = await permission_service.revoke_permission(
            server_id=revoke_request.server_id,
            target_user_id=revoke_request.target_user_id,
            revoker_id=current_user.id,
        )

        if success:
            return PermissionRevokeResponse(
                success=True,
                message="权限已撤销",
            )
        else:
            return PermissionRevokeResponse(
                success=False,
                message="未找到权限记录",
            )

    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=str(e),
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"撤销权限失败: {str(e)}",
        )


@router.post("/check", response_model=PermissionCheckResponse)
async def check_permission(
    check_request: PermissionCheck,
    current_user: CurrentUser,
    permission_service: Annotated[PermissionService, Depends(get_permission_service)],
):
    """
    检查权限

    检查当前用户是否对指定服务器有特定权限

    需要Bearer Token认证
    """
    try:
        has_permission = await permission_service.check_permission(
            server_id=check_request.server_id,
            user_id=current_user.id,
            required_permission=check_request.required_permission,
        )

        return PermissionCheckResponse(
            has_permission=has_permission,
            server_id=str(check_request.server_id),
            required_permission=check_request.required_permission,
        )

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"检查权限失败: {str(e)}",
        )


@router.get("/user/permissions", response_model=UserPermissionListResponse)
async def get_user_permissions(
    current_user: CurrentUser,
    permission_service: Annotated[PermissionService, Depends(get_permission_service)],
    page: int = Query(1, ge=1, description="页码"),
    size: int = Query(20, ge=1, le=100, description="每页数量"),
):
    """
    获取当前用户的所有权限

    返回用户可以访问的服务器及其权限

    需要Bearer Token认证
    """
    try:
        result = await permission_service.get_user_permissions(
            user_id=current_user.id,
            page=page,
            size=size,
        )
        return UserPermissionListResponse(**result)

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"获取用户权限失败: {str(e)}",
        )


@router.get("/server/{server_id}", response_model=ServerPermissionListResponse)
async def get_server_permissions(
    server_id: UUID,
    current_user: CurrentUser,
    permission_service: Annotated[PermissionService, Depends(get_permission_service)],
    page: int = Query(1, ge=1, description="页码"),
    size: int = Query(20, ge=1, le=100, description="每页数量"),
):
    """
    获取服务器的所有权限

    返回该服务器授权给哪些用户及其权限

    只有服务器所有者、管理员、或拥有 admin 权限的用户可以查看

    需要Bearer Token认证
    """
    try:
        result = await permission_service.get_server_permissions(
            server_id=server_id,
            requester_id=current_user.id,
            page=page,
            size=size,
        )
        return ServerPermissionListResponse(**result)

    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=str(e),
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"获取服务器权限失败: {str(e)}",
        )


@router.get("/user/accessible-servers", response_model=AccessibleServersResponse)
async def get_accessible_servers(
    current_user: CurrentUser,
    permission_service: Annotated[PermissionService, Depends(get_permission_service)],
    min_permission: str = Query("read", description="最小权限要求"),
):
    """
    获取用户可访问的服务器ID列表

    根据指定的最小权限要求，返回用户可以访问的所有服务器ID

    权限级别（从低到高）：read < write < execute < admin

    需要Bearer Token认证
    """
    try:
        # 验证权限参数
        valid_permissions = {"read", "write", "execute", "admin"}
        if min_permission not in valid_permissions:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid permission: {min_permission}",
            )

        server_ids = await permission_service.get_accessible_servers(
            user_id=current_user.id,
            min_permission=min_permission,
        )

        return AccessibleServersResponse(
            server_ids=[str(sid) for sid in server_ids],
            count=len(server_ids),
        )

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"获取可访问服务器失败: {str(e)}",
        )
