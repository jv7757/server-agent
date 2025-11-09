"""
Pydantic模式模块
"""

from app.schemas.auth import (
    LoginRequest,
    LoginResponse,
    RefreshTokenRequest,
    RefreshTokenResponse,
    TokenPayload,
    TokenResponse,
)
from app.schemas.chat import (
    ChatMessageResponse,
    ChatMessagesResponse,
    ChatRequest,
    ChatResponse,
    ChatStreamRequest,
    ConversationDeleteResponse,
    ConversationListItem,
    ConversationListResponse,
)
from app.schemas.execute import (
    BatchCommandRequest,
    BatchCommandResponse,
    BatchCommandResult,
    CommandExecuteRequest,
    CommandExecuteResponse,
    CommandHistoryListResponse,
    CommandHistoryResponse,
    CommandValidateRequest,
    CommandValidateResponse,
)
from app.schemas.metric import (
    CurrentMetricsResponse,
    MetricResponse,
    MetricsHistoryResponse,
    MetricsQueryParams,
    MetricsSummaryParams,
    MetricsSummaryResponse,
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
    ServerPermissionItem,
    ServerPermissionListResponse,
    UserPermissionItem,
    UserPermissionListResponse,
)
from app.schemas.server import (
    ConnectionTestResponse,
    ServerCreate,
    ServerDetailResponse,
    ServerListResponse,
    ServerQueryParams,
    ServerResponse,
    ServerUpdate,
    SystemInfoResponse,
)
from app.schemas.user import (
    PasswordChange,
    PasswordReset,
    UserCreate,
    UserDetailResponse,
    UserListResponse,
    UserResponse,
    UserUpdate,
    UserUpdateRole,
    UserUpdateStatus,
)

__all__ = [
    # Auth
    "LoginRequest",
    "LoginResponse",
    "RefreshTokenRequest",
    "RefreshTokenResponse",
    "TokenResponse",
    "TokenPayload",
    # User
    "UserCreate",
    "UserUpdate",
    "UserUpdateRole",
    "UserUpdateStatus",
    "UserResponse",
    "UserDetailResponse",
    "UserListResponse",
    "PasswordChange",
    "PasswordReset",
    # Server
    "ServerCreate",
    "ServerUpdate",
    "ServerResponse",
    "ServerDetailResponse",
    "ServerListResponse",
    "ServerQueryParams",
    "ConnectionTestResponse",
    "SystemInfoResponse",
    # Metrics
    "MetricResponse",
    "CurrentMetricsResponse",
    "MetricsHistoryResponse",
    "MetricsSummaryResponse",
    "MetricsQueryParams",
    "MetricsSummaryParams",
    # Execute
    "CommandExecuteRequest",
    "CommandExecuteResponse",
    "CommandValidateRequest",
    "CommandValidateResponse",
    "CommandHistoryResponse",
    "CommandHistoryListResponse",
    "BatchCommandRequest",
    "BatchCommandResponse",
    "BatchCommandResult",
    # Chat
    "ChatRequest",
    "ChatResponse",
    "ChatStreamRequest",
    "ChatMessageResponse",
    "ChatMessagesResponse",
    "ConversationListItem",
    "ConversationListResponse",
    "ConversationDeleteResponse",
    # Permission
    "PermissionGrant",
    "PermissionRevoke",
    "PermissionCheck",
    "PermissionResponse",
    "PermissionGrantResponse",
    "PermissionRevokeResponse",
    "PermissionCheckResponse",
    "UserPermissionItem",
    "UserPermissionListResponse",
    "ServerPermissionItem",
    "ServerPermissionListResponse",
    "AccessibleServersResponse",
]
