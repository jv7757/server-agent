"""
命令执行服务
"""

from datetime import datetime
from uuid import UUID

from sqlalchemy import desc, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.command_validator import CommandValidator
from app.models.audit import AuditLog
from app.models.server import Server
from app.models.user import User
from app.schemas.execute import (
    BatchCommandResult,
    CommandExecuteResponse,
    CommandHistoryListResponse,
    CommandHistoryResponse,
    CommandValidateResponse,
)
from app.services.ssh_service import SSHService
from app.utils.logger import logger


class ExecuteService:
    """命令执行服务类"""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def validate_command(self, command: str) -> CommandValidateResponse:
        """
        验证命令

        Args:
            command: 命令

        Returns:
            CommandValidateResponse: 验证结果
        """
        # 清理命令
        command = CommandValidator.sanitize(command)

        # 获取风险级别
        risk_level = CommandValidator.get_command_risk_level(command)

        # 验证命令
        is_valid, message = CommandValidator.validate(command, allow_dangerous=False)

        # 检查是否需要确认
        needs_confirm, _ = CommandValidator.needs_confirmation(command)

        return CommandValidateResponse(
            command=command,
            is_valid=is_valid,
            risk_level=risk_level,
            message=message,
            requires_confirmation=needs_confirm,
        )

    async def execute_command(
        self,
        server_id: UUID,
        user_id: UUID,
        command: str,
        timeout: int = 30,
        allow_dangerous: bool = False,
        skip_confirmation: bool = False,
        ip_address: str | None = None,
    ) -> CommandExecuteResponse:
        """
        执行命令

        Args:
            server_id: 服务器ID
            user_id: 用户ID
            command: 命令
            timeout: 超时时间
            allow_dangerous: 是否允许危险命令
            skip_confirmation: 是否跳过确认
            ip_address: 用户IP地址

        Returns:
            CommandExecuteResponse: 执行结果

        Raises:
            ValueError: 验证失败或执行失败
        """
        # 清理命令
        command = CommandValidator.sanitize(command)

        # 验证命令
        is_valid, message = CommandValidator.validate(
            command, allow_dangerous=allow_dangerous, skip_confirmation=skip_confirmation
        )

        if not is_valid:
            raise ValueError(message)

        # 获取服务器
        result = await self.db.execute(
            select(Server).where(Server.id == server_id, Server.owner_id == user_id)
        )
        server = result.scalar_one_or_none()

        if not server:
            raise ValueError("Server not found")

        # 创建SSH服务
        ssh_service = await SSHService.create_from_encrypted(
            host=server.host,
            port=server.port,
            username=server.ssh_username or "",
            encrypted_password=server.ssh_password_encrypted,
            encrypted_key=server.ssh_key_encrypted,
        )

        try:
            # 连接SSH
            await ssh_service.connect()

            # 执行命令
            result = await ssh_service.execute_command(command, timeout=timeout)

            # 断开连接
            await ssh_service.disconnect()

            # 记录审计日志
            await self._log_command_execution(
                user_id=user_id,
                server_id=server_id,
                command=command,
                exit_code=result["exit_code"],
                execution_time_ms=result["execution_time_ms"],
                ip_address=ip_address,
            )

            logger.info(
                f"Command executed on server {server.name}: {command} (exit: {result['exit_code']})"
            )

            return CommandExecuteResponse(
                command=command,
                exit_code=result["exit_code"],
                stdout=result["stdout"],
                stderr=result["stderr"],
                execution_time_ms=result["execution_time_ms"],
                executed_at=datetime.utcnow(),
            )

        except Exception as e:
            # 记录失败的命令执行
            await self._log_command_execution(
                user_id=user_id,
                server_id=server_id,
                command=command,
                exit_code=-1,
                execution_time_ms=0,
                ip_address=ip_address,
                error=str(e),
            )

            logger.error(f"Command execution failed on server {server.name}: {str(e)}")
            raise ValueError(f"Command execution failed: {str(e)}")

    async def execute_batch_commands(
        self,
        server_ids: list[UUID],
        user_id: UUID,
        command: str,
        timeout: int = 30,
        allow_dangerous: bool = False,
        ip_address: str | None = None,
    ) -> list[BatchCommandResult]:
        """
        批量执行命令

        Args:
            server_ids: 服务器ID列表
            user_id: 用户ID
            command: 命令
            timeout: 超时时间
            allow_dangerous: 是否允许危险命令
            ip_address: 用户IP地址

        Returns:
            list[BatchCommandResult]: 执行结果列表
        """
        results = []

        # 获取所有服务器
        query_result = await self.db.execute(
            select(Server).where(Server.id.in_(server_ids), Server.owner_id == user_id)
        )
        servers = query_result.scalars().all()

        # 逐个执行
        for server in servers:
            try:
                result = await self.execute_command(
                    server_id=server.id,
                    user_id=user_id,
                    command=command,
                    timeout=timeout,
                    allow_dangerous=allow_dangerous,
                    skip_confirmation=True,  # 批量执行时跳过确认
                    ip_address=ip_address,
                )

                results.append(
                    BatchCommandResult(
                        server_id=server.id,
                        server_name=server.name,
                        success=True,
                        exit_code=result.exit_code,
                        stdout=result.stdout,
                        stderr=result.stderr,
                        execution_time_ms=result.execution_time_ms,
                    )
                )

            except Exception as e:
                results.append(
                    BatchCommandResult(
                        server_id=server.id,
                        server_name=server.name,
                        success=False,
                        error=str(e),
                    )
                )

        return results

    async def get_command_history(
        self,
        user_id: UUID,
        server_id: UUID | None = None,
        page: int = 1,
        size: int = 50,
    ) -> CommandHistoryListResponse:
        """
        获取命令执行历史

        Args:
            user_id: 用户ID
            server_id: 服务器ID（可选）
            page: 页码
            size: 每页数量

        Returns:
            CommandHistoryListResponse: 命令历史列表
        """
        # 构建查询条件
        conditions = [
            AuditLog.user_id == user_id,
            AuditLog.action == "execute_command",
        ]

        if server_id:
            conditions.append(AuditLog.server_id == server_id)

        # 查询总数
        from sqlalchemy import func

        count_result = await self.db.execute(
            select(func.count()).select_from(AuditLog).where(*conditions)
        )
        total = count_result.scalar_one()

        # 查询数据
        offset = (page - 1) * size
        query = (
            select(AuditLog, Server, User)
            .join(Server, AuditLog.server_id == Server.id, isouter=True)
            .join(User, AuditLog.user_id == User.id, isouter=True)
            .where(*conditions)
            .order_by(desc(AuditLog.created_at))
            .offset(offset)
            .limit(size)
        )

        result = await self.db.execute(query)
        rows = result.all()

        items = []
        for audit_log, server, user in rows:
            if audit_log.details:
                items.append(
                    CommandHistoryResponse(
                        id=audit_log.id,
                        server_id=audit_log.server_id,
                        server_name=server.name if server else "Unknown",
                        command=audit_log.details.get("command", ""),
                        exit_code=audit_log.details.get("exit_code"),
                        execution_time_ms=audit_log.details.get("execution_time_ms"),
                        executed_at=audit_log.created_at,
                        user_id=audit_log.user_id,
                        username=user.username if user else "Unknown",
                    )
                )

        return CommandHistoryListResponse(
            total=total,
            page=page,
            size=size,
            items=items,
        )

    async def _log_command_execution(
        self,
        user_id: UUID,
        server_id: UUID,
        command: str,
        exit_code: int,
        execution_time_ms: int,
        ip_address: str | None = None,
        error: str | None = None,
    ) -> None:
        """
        记录命令执行到审计日志

        Args:
            user_id: 用户ID
            server_id: 服务器ID
            command: 命令
            exit_code: 退出码
            execution_time_ms: 执行时间
            ip_address: IP地址
            error: 错误信息
        """
        audit_log = AuditLog(
            user_id=user_id,
            server_id=server_id,
            action="execute_command",
            resource_type="command",
            details={
                "command": command,
                "exit_code": exit_code,
                "execution_time_ms": execution_time_ms,
                "error": error,
            },
            ip_address=ip_address,
        )

        self.db.add(audit_log)
        await self.db.commit()
