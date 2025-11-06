# API 文档

## 概述

Server Management System REST API 文档。

**基础URL**: `http://localhost:8000`
**API版本**: v1
**认证方式**: Bearer Token (JWT)

## 认证

除了注册和登录接口外，所有API都需要在请求头中包含JWT令牌：

```
Authorization: Bearer <access_token>
```

## 响应格式

### 成功响应

```json
{
  "data": {},
  "message": "Success"
}
```

### 错误响应

```json
{
  "detail": "Error message"
}
```

## API 端点

### 1. 认证 (Authentication)

#### 1.1 用户注册

**POST** `/api/v1/auth/register`

注册新用户账户。

**请求体**:
```json
{
  "username": "string",
  "email": "user@example.com",
  "password": "string"
}
```

**响应**: `201 Created`
```json
{
  "id": "uuid",
  "username": "string",
  "email": "user@example.com",
  "role": "user",
  "is_active": true,
  "created_at": "2025-01-01T00:00:00Z"
}
```

#### 1.2 用户登录

**POST** `/api/v1/auth/login`

用户登录获取访问令牌。

**请求体**:
```json
{
  "username": "string",
  "password": "string"
}
```

**响应**: `200 OK`
```json
{
  "access_token": "string",
  "refresh_token": "string",
  "token_type": "bearer",
  "user": {
    "id": "uuid",
    "username": "string",
    "email": "user@example.com",
    "role": "user"
  }
}
```

#### 1.3 刷新令牌

**POST** `/api/v1/auth/refresh`

使用refresh_token获取新的access_token。

**请求体**:
```json
{
  "refresh_token": "string"
}
```

**响应**: `200 OK`
```json
{
  "access_token": "string",
  "token_type": "bearer"
}
```

#### 1.4 获取当前用户

**GET** `/api/v1/auth/me`

获取当前登录用户信息。

**认证**: 必需

**响应**: `200 OK`
```json
{
  "id": "uuid",
  "username": "string",
  "email": "user@example.com",
  "role": "user",
  "is_active": true,
  "created_at": "2025-01-01T00:00:00Z"
}
```

#### 1.5 更新用户资料

**PUT** `/api/v1/auth/me`

更新当前用户的资料。

**认证**: 必需

**请求体**:
```json
{
  "email": "newemail@example.com"
}
```

**响应**: `200 OK`

#### 1.6 修改密码

**POST** `/api/v1/auth/change-password`

修改当前用户密码。

**认证**: 必需

**请求体**:
```json
{
  "old_password": "string",
  "new_password": "string"
}
```

**响应**: `200 OK`

---

### 2. 服务器管理 (Servers)

#### 2.1 创建服务器

**POST** `/api/v1/servers`

创建新服务器。

**认证**: 必需

**请求体**:
```json
{
  "name": "string",
  "host": "192.168.1.100",
  "port": 22,
  "ssh_username": "root",
  "ssh_password": "string",  // 与ssh_key二选一
  "ssh_key": "string",       // 与ssh_password二选一
  "description": "string",
  "tags": ["tag1", "tag2"]
}
```

**响应**: `201 Created`
```json
{
  "id": "uuid",
  "name": "string",
  "host": "192.168.1.100",
  "port": 22,
  "ssh_username": "root",
  "description": "string",
  "tags": ["tag1", "tag2"],
  "status": "unknown",
  "created_at": "2025-01-01T00:00:00Z"
}
```

#### 2.2 获取服务器列表

**GET** `/api/v1/servers`

获取服务器列表（支持分页、筛选、搜索）。

**认证**: 必需

**查询参数**:
- `page` (integer): 页码，默认1
- `size` (integer): 每页数量，默认20，最大100
- `status` (string): 状态筛选 (online|offline|error|unknown)
- `tags` (string): 标签筛选，逗号分隔
- `search` (string): 搜索关键词

**响应**: `200 OK`
```json
{
  "total": 100,
  "page": 1,
  "size": 20,
  "items": [
    {
      "id": "uuid",
      "name": "string",
      "host": "192.168.1.100",
      "port": 22,
      "status": "online",
      "tags": ["tag1"],
      "created_at": "2025-01-01T00:00:00Z"
    }
  ]
}
```

#### 2.3 获取服务器详情

**GET** `/api/v1/servers/{server_id}`

获取单个服务器的详细信息。

**认证**: 必需

**响应**: `200 OK`
```json
{
  "id": "uuid",
  "name": "string",
  "host": "192.168.1.100",
  "port": 22,
  "ssh_username": "root",
  "description": "string",
  "tags": ["tag1"],
  "status": "online",
  "owner_id": "uuid",
  "created_at": "2025-01-01T00:00:00Z",
  "updated_at": "2025-01-01T00:00:00Z"
}
```

#### 2.4 更新服务器

**PUT** `/api/v1/servers/{server_id}`

更新服务器信息。

**认证**: 必需（需要所有者或管理员权限）

**请求体**:
```json
{
  "name": "string",
  "description": "string",
  "tags": ["tag1", "tag2"]
}
```

**响应**: `200 OK`

#### 2.5 删除服务器

**DELETE** `/api/v1/servers/{server_id}`

删除服务器。

**认证**: 必需（需要所有者或管理员权限）

**响应**: `204 No Content`

#### 2.6 测试服务器连接

**POST** `/api/v1/servers/{server_id}/test-connection`

测试SSH连接。

**认证**: 必需

**响应**: `200 OK`
```json
{
  "success": true,
  "message": "Connection successful",
  "latency": 123.45
}
```

---

### 3. 监控指标 (Metrics)

#### 3.1 获取当前指标

**GET** `/api/v1/metrics/{server_id}/current`

获取服务器的当前性能指标。

**认证**: 必需

**响应**: `200 OK`
```json
{
  "cpu_percent": 45.2,
  "memory_percent": 62.8,
  "memory_used_mb": 4096,
  "memory_total_mb": 8192,
  "disk_percent": 35.5,
  "disk_used_gb": 142.5,
  "disk_total_gb": 500,
  "network_sent_mb": 1024.5,
  "network_recv_mb": 2048.3,
  "collected_at": "2025-01-01T00:00:00Z"
}
```

#### 3.2 获取历史指标

**GET** `/api/v1/metrics/{server_id}/history`

获取服务器的历史性能指标。

**认证**: 必需

**查询参数**:
- `start_time` (datetime): 开始时间
- `end_time` (datetime): 结束时间
- `interval` (integer): 时间间隔（分钟）

**响应**: `200 OK`
```json
{
  "metrics": [
    {
      "cpu_percent": 45.2,
      "memory_percent": 62.8,
      "collected_at": "2025-01-01T00:00:00Z"
    }
  ]
}
```

#### 3.3 获取指标摘要

**GET** `/api/v1/metrics/{server_id}/summary`

获取服务器指标的统计摘要。

**认证**: 必需

**查询参数**:
- `hours` (integer): 统计时间范围（小时），默认24

**响应**: `200 OK`
```json
{
  "cpu": {
    "avg": 45.2,
    "min": 10.5,
    "max": 89.3
  },
  "memory": {
    "avg": 62.8,
    "min": 45.2,
    "max": 85.6
  },
  "disk": {
    "current": 35.5
  }
}
```

#### 3.4 触发手动采集

**POST** `/api/v1/metrics/{server_id}/collect`

手动触发指标采集。

**认证**: 必需

**响应**: `200 OK`

---

### 4. 命令执行 (Execute)

#### 4.1 执行命令

**POST** `/api/v1/execute/command`

在服务器上执行命令。

**认证**: 必需（需要execute权限）

**请求体**:
```json
{
  "server_id": "uuid",
  "command": "uptime",
  "timeout": 30
}
```

**响应**: `200 OK`
```json
{
  "success": true,
  "stdout": "command output",
  "stderr": "",
  "exit_code": 0,
  "execution_time": 0.5
}
```

#### 4.2 验证命令

**POST** `/api/v1/execute/validate`

验证命令是否安全（检查危险命令）。

**认证**: 必需

**请求体**:
```json
{
  "command": "rm -rf /tmp/test"
}
```

**响应**: `200 OK`
```json
{
  "is_safe": false,
  "is_dangerous": true,
  "message": "Command contains dangerous pattern: rm -rf"
}
```

#### 4.3 批量执行命令

**POST** `/api/v1/execute/batch`

在多个服务器上执行相同命令。

**认证**: 必需

**请求体**:
```json
{
  "server_ids": ["uuid1", "uuid2"],
  "command": "uptime",
  "timeout": 30
}
```

**响应**: `200 OK`
```json
{
  "results": [
    {
      "server_id": "uuid1",
      "success": true,
      "stdout": "output"
    }
  ]
}
```

#### 4.4 获取命令历史

**GET** `/api/v1/execute/history`

获取命令执行历史。

**认证**: 必需

**查询参数**:
- `page` (integer): 页码
- `size` (integer): 每页数量
- `server_id` (uuid): 服务器ID筛选

**响应**: `200 OK`

#### 4.5 获取命令详情

**GET** `/api/v1/execute/history/{audit_id}`

获取单条命令执行记录详情。

**认证**: 必需

**响应**: `200 OK`

---

### 5. AI 聊天 (Chat)

#### 5.1 发送消息

**POST** `/api/v1/chat/chat`

发送聊天消息（支持Function Calling）。

**认证**: 必需

**请求体**:
```json
{
  "message": "列出我的所有服务器",
  "conversation_id": "uuid"  // 可选
}
```

**响应**: `200 OK`
```json
{
  "conversation_id": "uuid",
  "message": "AI response",
  "iterations": 2
}
```

#### 5.2 流式聊天

**POST** `/api/v1/chat/stream`

流式聊天响应（Server-Sent Events）。

**认证**: 必需

**请求体**:
```json
{
  "message": "检查服务器状态",
  "conversation_id": "uuid"
}
```

**响应**: `200 OK` (SSE stream)

#### 5.3 获取会话列表

**GET** `/api/v1/chat/conversations`

获取用户的会话列表。

**认证**: 必需

**查询参数**:
- `page` (integer): 页码
- `size` (integer): 每页数量

**响应**: `200 OK`

#### 5.4 获取会话消息

**GET** `/api/v1/chat/conversations/{conversation_id}`

获取会话的消息历史。

**认证**: 必需

**响应**: `200 OK`

#### 5.5 删除会话

**DELETE** `/api/v1/chat/conversations/{conversation_id}`

删除会话及其所有消息。

**认证**: 必需

**响应**: `200 OK`

---

### 6. 权限管理 (Permissions)

#### 6.1 授予权限

**POST** `/api/v1/permissions/grant`

授予用户对服务器的权限。

**认证**: 必需（需要admin权限或服务器所有者）

**请求体**:
```json
{
  "server_id": "uuid",
  "target_user_id": "uuid",
  "permissions": ["read", "write", "execute", "admin"]
}
```

**权限类型**:
- `read`: 读取服务器信息和指标
- `write`: 修改服务器配置
- `execute`: 执行命令
- `admin`: 管理权限

**响应**: `200 OK`
```json
{
  "success": true,
  "message": "权限已授予",
  "permission": {
    "permission_id": 1,
    "server_id": "uuid",
    "user_id": "uuid",
    "permissions": ["read", "write"],
    "created_at": "2025-01-01T00:00:00Z"
  }
}
```

#### 6.2 撤销权限

**POST** `/api/v1/permissions/revoke`

撤销用户对服务器的权限。

**认证**: 必需（需要admin权限或服务器所有者）

**请求体**:
```json
{
  "server_id": "uuid",
  "target_user_id": "uuid"
}
```

**响应**: `200 OK`

#### 6.3 检查权限

**POST** `/api/v1/permissions/check`

检查当前用户是否有特定权限。

**认证**: 必需

**请求体**:
```json
{
  "server_id": "uuid",
  "required_permission": "execute"
}
```

**响应**: `200 OK`
```json
{
  "has_permission": true,
  "server_id": "uuid",
  "required_permission": "execute"
}
```

#### 6.4 获取用户权限列表

**GET** `/api/v1/permissions/user/permissions`

获取当前用户的所有权限。

**认证**: 必需

**查询参数**:
- `page` (integer): 页码
- `size` (integer): 每页数量

**响应**: `200 OK`

#### 6.5 获取服务器权限列表

**GET** `/api/v1/permissions/server/{server_id}`

获取服务器的所有权限配置。

**认证**: 必需（需要admin权限或服务器所有者）

**响应**: `200 OK`

#### 6.6 获取可访问服务器

**GET** `/api/v1/permissions/user/accessible-servers`

获取用户可访问的服务器ID列表。

**认证**: 必需

**查询参数**:
- `min_permission` (string): 最小权限要求 (read|write|execute|admin)

**响应**: `200 OK`
```json
{
  "server_ids": ["uuid1", "uuid2"],
  "count": 2
}
```

---

## 错误代码

| 状态码 | 说明 |
|--------|------|
| 200 | 成功 |
| 201 | 创建成功 |
| 204 | 成功（无内容） |
| 400 | 请求错误 |
| 401 | 未授权 |
| 403 | 禁止访问 |
| 404 | 资源不存在 |
| 422 | 验证错误 |
| 500 | 服务器错误 |

## 速率限制

- 认证接口: 10次/分钟
- 其他接口: 60次/分钟

## WebSocket (计划中)

- `/ws/metrics/{server_id}`: 实时监控数据推送
- `/ws/terminal/{server_id}`: Web终端连接

## 交互式文档

启动应用后访问：
- Swagger UI: `http://localhost:8000/docs`
- ReDoc: `http://localhost:8000/redoc`
