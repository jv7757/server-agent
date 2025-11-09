"""
命令执行API路由
"""
from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, Request, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.dependencies import CurrentUser
from app.schemas.execute import (
    BatchCommandRequest,
    BatchCommandResponse,
    CommandExecuteRequest,
    CommandExecuteResponse,
    CommandHistoryListResponse,
    CommandValidateRequest,
    CommandValidateResponse,
)
from app.services.execute_service import ExecuteService

router = APIRouter()


async def get_execute_service(db: Annotated[AsyncSession, Depends(get_db)]) -> ExecuteService:
    """获取命令执行服务依赖"""
    return ExecuteService(db)


def get_client_ip(request: Request) -> str | None:
    """获取客户端IP地址"""
    # 优先从X-Forwarded-For获取
    forwarded = request.headers.get("X-Forwarded-For")
    if forwarded:
        return forwarded.split(",")[0].strip()

    # 其次从X-Real-IP获取
    real_ip = request.headers.get("X-Real-IP")
    if real_ip:
        return real_ip

    # 最后从客户端直接获取
    if request.client:
        return request.client.host

    return None


@router.post("/validate", response_model=CommandValidateResponse)
async def validate_command(
    validate_request: CommandValidateRequest,
    current_user: CurrentUser,
    execute_service: Annotated[ExecuteService, Depends(get_execute_service)],
):
    """
    验证命令

    检查命令是否安全、是否需要确认

    返回风险级别和验证结果

    需要Bearer Token认证
    """
    result = await execute_service.validate_command(validate_request.command)
    return result


@router.post("/servers/{server_id}", response_model=CommandExecuteResponse)
async def execute_command(
    server_id: UUID,
    execute_request: CommandExecuteRequest,
    request: Request,
    current_user: CurrentUser,
    execute_service: Annotated[ExecuteService, Depends(get_execute_service)],
):
    """
    在指定服务器上执行命令

    - **command**: 要执行的命令
    - **timeout**: 超时时间（秒，默认30秒）
    - **allow_dangerous**: 是否允许危险命令（默认false）
    - **skip_confirmation**: 是否跳过确认提示（默认false）

    危险命令会被默认拦截，除非显式允许

    需要Bearer Token认证
    """
    try:
        ip_address = get_client_ip(request)

        result = await execute_service.execute_command(
            server_id=server_id,
            user_id=current_user.id,
            command=execute_request.command,
            timeout=execute_request.timeout,
            allow_dangerous=execute_request.allow_dangerous,
            skip_confirmation=execute_request.skip_confirmation,
            ip_address=ip_address,
        )

        return result

    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )


@router.post("/batch", response_model=BatchCommandResponse)
async def execute_batch_commands(
    batch_request: BatchCommandRequest,
    request: Request,
    current_user: CurrentUser,
    execute_service: Annotated[ExecuteService, Depends(get_execute_service)],
):
    """
    在多个服务器上批量执行命令

    - **server_ids**: 服务器ID列表
    - **command**: 要执行的命令
    - **timeout**: 超时时间（秒，默认30秒）
    - **allow_dangerous**: 是否允许危险命令（默认false）

    返回每个服务器的执行结果

    需要Bearer Token认证
    """
    try:
        ip_address = get_client_ip(request)

        results = await execute_service.execute_batch_commands(
            server_ids=batch_request.server_ids,
            user_id=current_user.id,
            command=batch_request.command,
            timeout=batch_request.timeout,
            allow_dangerous=batch_request.allow_dangerous,
            ip_address=ip_address,
        )

        success_count = sum(1 for r in results if r.success)
        failed_count = len(results) - success_count

        return BatchCommandResponse(
            total=len(results),
            success=success_count,
            failed=failed_count,
            results=results,
        )

    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )


@router.get("/history", response_model=CommandHistoryListResponse)
async def get_command_history(
    current_user: CurrentUser,
    execute_service: Annotated[ExecuteService, Depends(get_execute_service)],
    server_id: UUID | None = Query(None, description="服务器ID筛选"),
    page: int = Query(1, ge=1, description="页码"),
    size: int = Query(50, ge=1, le=100, description="每页数量"),
):
    """
    获取命令执行历史

    返回用户的命令执行记录，支持按服务器筛选

    需要Bearer Token认证
    """
    history = await execute_service.get_command_history(
        user_id=current_user.id,
        server_id=server_id,
        page=page,
        size=size,
    )

    return history


@router.get("/servers/{server_id}/history", response_model=CommandHistoryListResponse)
async def get_server_command_history(
    server_id: UUID,
    current_user: CurrentUser,
    execute_service: Annotated[ExecuteService, Depends(get_execute_service)],
    page: int = Query(1, ge=1, description="页码"),
    size: int = Query(50, ge=1, le=100, description="每页数量"),
):
    """
    获取指定服务器的命令执行历史

    需要Bearer Token认证
    """
    history = await execute_service.get_command_history(
        user_id=current_user.id,
        server_id=server_id,
        page=page,
        size=size,
    )

    return history
