"""
AI工具函数定义（用于Function Calling）
"""
import json
from typing import Any, Callable, Dict, List
from uuid import UUID

from app.services.execute_service import ExecuteService
from app.services.metrics_service import MetricsService
from app.services.server_service import ServerService
from app.utils.logger import logger


class AITools:
    """AI工具函数集合"""

    def __init__(
        self,
        server_service: ServerService,
        metrics_service: MetricsService,
        execute_service: ExecuteService,
        user_id: UUID,
        default_server_id: UUID | None = None,
    ):
        self.server_service = server_service
        self.metrics_service = metrics_service
        self.execute_service = execute_service
        self.user_id = user_id
        self.default_server_id = default_server_id

    def get_tool_definitions(self) -> List[Dict[str, Any]]:
        """
        获取工具函数定义（OpenAI Function Calling格式）

        Returns:
            List[Dict]: 工具函数列表
        """
        return [
            {
                "type": "function",
                "function": {
                    "name": "list_servers",
                    "description": "列出用户的所有服务器。可以按状态（online/offline/error/unknown）、标签或搜索关键词筛选。",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "status": {
                                "type": "string",
                                "enum": ["online", "offline", "error", "unknown"],
                                "description": "服务器状态筛选",
                            },
                            "tags": {
                                "type": "array",
                                "items": {"type": "string"},
                                "description": "标签筛选",
                            },
                            "search": {
                                "type": "string",
                                "description": "搜索关键词（匹配服务器名称或主机地址）",
                            },
                        },
                    },
                },
            },
            {
                "type": "function",
                "function": {
                    "name": "get_server_metrics",
                    "description": "获取指定服务器的当前性能指标，包括CPU、内存、磁盘、网络使用情况。如果没有指定server_id，将使用当前会话的默认服务器。",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "server_id": {
                                "type": "string",
                                "description": "服务器ID（UUID格式，可选）",
                            },
                        },
                        "required": [],
                    },
                },
            },
            {
                "type": "function",
                "function": {
                    "name": "execute_command",
                    "description": "在指定服务器上执行Shell命令。如果没有指定server_id，将使用当前会话的默认服务器。注意：危险命令会被拒绝，除非用户明确允许。",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "server_id": {
                                "type": "string",
                                "description": "服务器ID（UUID格式，可选）",
                            },
                            "command": {
                                "type": "string",
                                "description": "要执行的Shell命令",
                            },
                            "allow_dangerous": {
                                "type": "boolean",
                                "description": "是否允许执行危险命令（默认false）",
                                "default": False,
                            },
                        },
                        "required": ["command"],
                    },
                },
            },
            {
                "type": "function",
                "function": {
                    "name": "get_server_info",
                    "description": "获取服务器的详细信息，包括名称、地址、状态、标签等。如果没有指定server_id，将使用当前会话的默认服务器。",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "server_id": {
                                "type": "string",
                                "description": "服务器ID（UUID格式，可选）",
                            },
                        },
                        "required": [],
                    },
                },
            },
        ]

    def get_tool_map(self) -> Dict[str, Callable]:
        """
        获取工具函数映射

        Returns:
            Dict: 函数名到函数对象的映射
        """
        return {
            "list_servers": self.list_servers,
            "get_server_metrics": self.get_server_metrics,
            "execute_command": self.execute_command,
            "get_server_info": self.get_server_info,
        }

    async def list_servers(
        self, status: str | None = None, tags: List[str] | None = None, search: str | None = None
    ) -> Dict[str, Any]:
        """列出服务器"""
        try:
            result = await self.server_service.get_servers(
                user_id=self.user_id,
                page=1,
                size=50,
                status=status,
                tags=tags,
                search=search,
            )

            servers_info = []
            for server in result.items:
                servers_info.append(
                    {
                        "id": str(server.id),
                        "name": server.name,
                        "host": server.host,
                        "status": server.status,
                        "tags": server.tags,
                    }
                )

            return {
                "success": True,
                "total": result.total,
                "servers": servers_info,
            }

        except Exception as e:
            logger.error(f"Error listing servers: {str(e)}")
            return {
                "success": False,
                "error": str(e),
            }

    async def get_server_metrics(self, server_id: str | None = None) -> Dict[str, Any]:
        """获取服务器指标"""
        try:
            # 如果没有提供server_id，使用默认的
            if server_id is None:
                if self.default_server_id is None:
                    return {
                        "success": False,
                        "error": "找不到服务器或访问被拒绝。请确认服务器ID和访问权限是否正确。",
                    }
                server_uuid = self.default_server_id
            else:
                server_uuid = UUID(server_id)

            # 验证服务器所有权
            server = await self.server_service.get_server_by_id(server_uuid, self.user_id)
            if not server:
                return {
                    "success": False,
                    "error": "Server not found or access denied",
                }

            # 获取最新指标
            metric = await self.metrics_service.get_current_metrics(server_uuid)

            if not metric:
                return {
                    "success": False,
                    "error": "No metrics data available",
                }

            return {
                "success": True,
                "server_name": server.name,
                "metrics": {
                    "cpu_usage_percent": metric.cpu_usage_percent,
                    "memory_usage_percent": metric.memory_usage_percent,
                    "memory_used_mb": metric.memory_used_mb,
                    "memory_total_mb": metric.memory_total_mb,
                    "disk_usage_percent": metric.disk_usage_percent,
                    "disk_used_gb": metric.disk_used_gb,
                    "disk_total_gb": metric.disk_total_gb,
                    "uptime_seconds": metric.uptime_seconds,
                    "load_average": metric.load_average,
                },
            }

        except ValueError as e:
            return {
                "success": False,
                "error": "Invalid server ID format",
            }
        except Exception as e:
            logger.error(f"Error getting server metrics: {str(e)}")
            return {
                "success": False,
                "error": str(e),
            }

    async def execute_command(
        self, server_id: str | None = None, command: str = "", allow_dangerous: bool = False
    ) -> Dict[str, Any]:
        """执行命令"""
        try:
            # 如果没有提供server_id，使用默认的
            if server_id is None:
                if self.default_server_id is None:
                    return {
                        "success": False,
                        "error": "找不到服务器或访问被拒绝。请确认服务器ID和访问权限是否正确。",
                    }
                server_uuid = self.default_server_id
            else:
                server_uuid = UUID(server_id)

            # 验证服务器所有权
            server = await self.server_service.get_server_by_id(server_uuid, self.user_id)
            if not server:
                return {
                    "success": False,
                    "error": "Server not found or access denied",
                }

            # 执行命令
            result = await self.execute_service.execute_command(
                server_id=server_uuid,
                user_id=self.user_id,
                command=command,
                allow_dangerous=allow_dangerous,
                skip_confirmation=True,  # AI执行时跳过确认
            )

            return {
                "success": True,
                "server_name": server.name,
                "command": command,
                "exit_code": result.exit_code,
                "stdout": result.stdout,
                "stderr": result.stderr,
                "execution_time_ms": result.execution_time_ms,
            }

        except ValueError as e:
            return {
                "success": False,
                "error": str(e),
            }
        except Exception as e:
            logger.error(f"Error executing command: {str(e)}")
            return {
                "success": False,
                "error": str(e),
            }

    async def get_server_info(self, server_id: str | None = None) -> Dict[str, Any]:
        """获取服务器信息"""
        try:
            # 如果没有提供server_id，使用默认的
            if server_id is None:
                if self.default_server_id is None:
                    return {
                        "success": False,
                        "error": "找不到服务器或访问被拒绝。请确认服务器ID和访问权限是否正确。",
                    }
                server_uuid = self.default_server_id
            else:
                server_uuid = UUID(server_id)

            server = await self.server_service.get_server_by_id(server_uuid, self.user_id)

            if not server:
                return {
                    "success": False,
                    "error": "Server not found or access denied",
                }

            return {
                "success": True,
                "server": {
                    "id": str(server.id),
                    "name": server.name,
                    "host": server.host,
                    "port": server.port,
                    "status": server.status,
                    "tags": server.tags,
                    "description": server.description,
                    "ssh_username": server.ssh_username,
                    "created_at": server.created_at.isoformat(),
                    "last_checked_at": (
                        server.last_checked_at.isoformat() if server.last_checked_at else None
                    ),
                },
            }

        except ValueError:
            return {
                "success": False,
                "error": "Invalid server ID format",
            }
        except Exception as e:
            logger.error(f"Error getting server info: {str(e)}")
            return {
                "success": False,
                "error": str(e),
            }

    async def execute_tool(self, tool_name: str, arguments: str | Dict) -> Dict[str, Any]:
        """
        执行工具函数

        Args:
            tool_name: 工具函数名称
            arguments: 参数（JSON字符串或字典）

        Returns:
            Dict: 执行结果
        """
        tool_map = self.get_tool_map()

        if tool_name not in tool_map:
            return {
                "success": False,
                "error": f"Unknown tool: {tool_name}",
            }

        # 解析参数
        if isinstance(arguments, str):
            try:
                args = json.loads(arguments)
            except json.JSONDecodeError:
                return {
                    "success": False,
                    "error": "Invalid JSON arguments",
                }
        else:
            args = arguments

        # 执行工具函数
        try:
            tool_func = tool_map[tool_name]
            result = await tool_func(**args)
            return result

        except Exception as e:
            logger.error(f"Error executing tool {tool_name}: {str(e)}")
            return {
                "success": False,
                "error": str(e),
            }
