"""
WebSocket连接路由
支持SSH Terminal和实时监控
"""

import asyncio
import json
from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, WebSocket, WebSocketDisconnect
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.dependencies import get_current_user_ws
from app.models.server import Server
from app.models.user import User
from app.services.metrics_service import MetricsService
from app.services.ssh_service import SSHService
from app.utils.logger import logger

router = APIRouter()


class ConnectionManager:
    """WebSocket连接管理器"""

    def __init__(self):
        # 监控连接: {server_id: [websocket1, websocket2, ...]}
        self.monitoring_connections: dict[UUID, list[WebSocket]] = {}
        # Terminal连接: {connection_id: websocket}
        self.terminal_connections: dict[str, WebSocket] = {}

    async def connect_monitoring(self, server_id: UUID, websocket: WebSocket):
        """连接监控WebSocket"""
        await websocket.accept()
        if server_id not in self.monitoring_connections:
            self.monitoring_connections[server_id] = []
        self.monitoring_connections[server_id].append(websocket)
        logger.info(f"Monitoring WebSocket connected for server {server_id}")

    def disconnect_monitoring(self, server_id: UUID, websocket: WebSocket):
        """断开监控WebSocket"""
        if server_id in self.monitoring_connections:
            self.monitoring_connections[server_id].remove(websocket)
            if not self.monitoring_connections[server_id]:
                del self.monitoring_connections[server_id]
        logger.info(f"Monitoring WebSocket disconnected for server {server_id}")

    async def connect_terminal(self, connection_id: str, websocket: WebSocket):
        """连接Terminal WebSocket"""
        await websocket.accept()
        self.terminal_connections[connection_id] = websocket
        logger.info(f"Terminal WebSocket connected: {connection_id}")

    def disconnect_terminal(self, connection_id: str):
        """断开Terminal WebSocket"""
        if connection_id in self.terminal_connections:
            del self.terminal_connections[connection_id]
        logger.info(f"Terminal WebSocket disconnected: {connection_id}")

    async def broadcast_metrics(self, server_id: UUID, data: dict):
        """广播监控数据"""
        if server_id in self.monitoring_connections:
            disconnected = []
            for websocket in self.monitoring_connections[server_id]:
                try:
                    await websocket.send_json(data)
                except Exception as e:
                    logger.error(f"Failed to send metrics: {e}")
                    disconnected.append(websocket)

            # 清理断开的连接
            for ws in disconnected:
                self.disconnect_monitoring(server_id, ws)


manager = ConnectionManager()


@router.websocket("/terminal/{server_id}")
async def terminal_websocket(
    websocket: WebSocket,
    server_id: UUID,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user_ws)],
):
    """
    SSH Terminal WebSocket连接

    客户端发送:
    {
        "type": "input",
        "data": "command or keystroke"
    }
    {
        "type": "resize",
        "rows": 24,
        "cols": 80
    }

    服务端发送:
    {
        "type": "output",
        "data": "terminal output"
    }
    {
        "type": "error",
        "message": "error message"
    }
    """
    connection_id = f"{server_id}_{current_user.id}"

    ssh_service = None
    shell = None

    try:
        await manager.connect_terminal(connection_id, websocket)

        # 获取服务器信息
        result = await db.execute(
            select(Server).where(Server.id == server_id, Server.owner_id == current_user.id)
        )
        server = result.scalar_one_or_none()

        if not server:
            await websocket.send_json({"type": "error", "message": "服务器不存在或无权访问"})
            return

        # 创建SSH服务
        ssh_service = await SSHService.create_from_encrypted(
            host=server.host,
            port=server.port,
            username=server.ssh_username or "",
            encrypted_password=server.ssh_password_encrypted,
            encrypted_key=server.ssh_key_encrypted,
        )

        try:
            # 建立SSH连接
            await ssh_service.connect()

            # 创建交互式shell
            shell = ssh_service.client.invoke_shell(
                term="xterm-256color",
                width=80,
                height=24,
            )
            shell.settimeout(0.1)  # 非阻塞读取

            # 发送欢迎消息
            await websocket.send_json(
                {"type": "output", "data": "\r\n\033[32m连接到服务器成功!\033[0m\r\n\r\n"}
            )

            # 创建读取任务
            async def read_ssh_output():
                """持续读取SSH输出"""
                while True:
                    try:
                        if shell.recv_ready():
                            output = shell.recv(4096).decode("utf-8", errors="ignore")
                            await websocket.send_json({"type": "output", "data": output})
                        await asyncio.sleep(0.01)
                    except Exception as e:
                        logger.error(f"SSH read error: {e}")
                        break

            # 启动读取任务
            read_task = asyncio.create_task(read_ssh_output())

            # 处理客户端消息
            while True:
                try:
                    message = await websocket.receive_text()
                    data = json.loads(message)

                    if data["type"] == "input":
                        # 发送用户输入到SSH
                        shell.send(data["data"])

                    elif data["type"] == "resize":
                        # 调整终端大小
                        shell.resize_pty(width=data.get("cols", 80), height=data.get("rows", 24))

                except WebSocketDisconnect:
                    logger.info(f"Terminal WebSocket disconnected: {connection_id}")
                    break
                except json.JSONDecodeError:
                    logger.warning(f"Invalid JSON from client: {message}")
                except Exception as e:
                    logger.error(f"Terminal error: {e}")
                    await websocket.send_json({"type": "error", "message": str(e)})

            # 取消读取任务
            read_task.cancel()
            try:
                await read_task
            except asyncio.CancelledError:
                pass

        except Exception as e:
            logger.error(f"SSH connection error: {e}")
            await websocket.send_json({"type": "error", "message": f"SSH连接失败: {str(e)}"})

        finally:
            # 清理SSH连接
            if shell:
                shell.close()
            if ssh_service:
                await ssh_service.disconnect()

    except Exception as e:
        logger.error(f"Terminal WebSocket error: {e}")
    finally:
        manager.disconnect_terminal(connection_id)


@router.websocket("/monitoring/{server_id}")
async def monitoring_websocket(
    websocket: WebSocket,
    server_id: UUID,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user_ws)],
):
    """
    实时监控WebSocket连接

    每5秒推送一次服务器监控数据:
    {
        "type": "metrics",
        "data": {
            "cpu_usage_percent": 45.5,
            "memory_usage_percent": 62.3,
            "disk_usage_percent": 45.8,
            ...
        }
    }
    """
    try:
        await manager.connect_monitoring(server_id, websocket)

        metrics_service = MetricsService(db)

        # 发送欢迎消息
        await websocket.send_json({"type": "connected", "message": f"已连接到服务器 {server_id} 监控"})

        # 持续推送监控数据
        while True:
            try:
                # 获取当前监控数据
                metrics = await metrics_service.get_current_metrics(server_id=server_id)

                if metrics:
                    await websocket.send_json(
                        {
                            "type": "metrics",
                            "data": {
                                "cpu": {
                                    "usage": metrics.cpu_usage_percent or 0,
                                    "cores": metrics.cpu_cores or 0,
                                },
                                "memory": {
                                    "usage": metrics.memory_usage_percent or 0,
                                    "total": metrics.memory_total_mb or 0,
                                    "used": metrics.memory_used_mb or 0,
                                },
                                "disk": {
                                    "usage": metrics.disk_usage_percent or 0,
                                    "total": metrics.disk_total_gb or 0,
                                    "used": metrics.disk_used_gb or 0,
                                },
                                "network": {
                                    "bytes_sent": metrics.network_bytes_sent or 0,
                                    "bytes_recv": metrics.network_bytes_recv or 0,
                                },
                                "uptime": metrics.uptime_seconds or 0,
                                "timestamp": (
                                    metrics.collected_at.isoformat()
                                    if metrics.collected_at
                                    else None
                                ),
                            },
                        }
                    )

                # 等待5秒
                await asyncio.sleep(5)

            except WebSocketDisconnect:
                logger.info(f"Monitoring WebSocket disconnected for server {server_id}")
                break
            except Exception as e:
                logger.error(f"Monitoring error: {e}")
                await websocket.send_json({"type": "error", "message": str(e)})
                await asyncio.sleep(5)

    except Exception as e:
        logger.error(f"Monitoring WebSocket error: {e}")
    finally:
        manager.disconnect_monitoring(server_id, websocket)


# 导出manager供其他模块使用
__all__ = ["router", "manager"]
