"""
自定义异常类
"""
from typing import Any, Dict


class ServerAgentException(Exception):
    """服务器代理基础异常"""

    def __init__(self, message: str, details: Dict[str, Any] | None = None):
        self.message = message
        self.details = details or {}
        super().__init__(self.message)


class AuthenticationError(ServerAgentException):
    """认证错误"""

    pass


class AuthorizationError(ServerAgentException):
    """授权错误"""

    pass


class ResourceNotFoundError(ServerAgentException):
    """资源未找到错误"""

    pass


class ValidationError(ServerAgentException):
    """验证错误"""

    pass


class SSHConnectionError(ServerAgentException):
    """SSH连接错误"""

    pass


class CommandExecutionError(ServerAgentException):
    """命令执行错误"""

    pass


class PermissionDeniedError(ServerAgentException):
    """权限拒绝错误"""

    pass


class DuplicateResourceError(ServerAgentException):
    """资源重复错误"""

    pass


class ConfigurationError(ServerAgentException):
    """配置错误"""

    pass


class AIProviderError(ServerAgentException):
    """AI提供商错误"""

    pass
