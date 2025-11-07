# API 文档

## 概述

Server Management System REST API 文档。

**基础URL**: `http://localhost:8000`
**API版本**: v1
**认证方式**: Bearer Token (JWT)
**总端点数量**: 42个REST API端点 + 2个WebSocket端点

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
```json
{
  "message": "Password changed successfully"
}
```

#### 1.7 登出

**POST** `/api/v1/auth/logout`

用户登出（注意：JWT无法在服务端主动失效，客户端应删除本地令牌）。

**认证**: 必需

**响应**: `200 OK`
```json
{
  "message": "Logged out successfully"
}
```

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

发送聊天消息（支持Function Calling）。AI助手可以执行命令、查询指标等操作。

**认证**: 必需

**请求体**:
```json
{
  "message": "列出我的所有服务器",
  "conversation_id": "uuid",  // 可选，不提供则创建新会话
  "server_id": "uuid"  // 可选，提供后AI可在该服务器上执行操作
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

### 7. 用户管理 (User Management) - 仅管理员

所有用户管理接口都需要管理员权限（role="admin"）。

#### 7.1 获取用户列表

**GET** `/api/v1/users`

获取用户列表（支持筛选、搜索、分页）。

**认证**: 必需（需要admin权限）

**查询参数**:
- `page` (integer): 页码，默认1
- `size` (integer): 每页数量，默认20，最大100
- `role` (string): 角色筛选 (admin|user|viewer)
- `is_active` (boolean): 状态筛选
- `search` (string): 搜索用户名、邮箱或全名

**响应**: `200 OK`
```json
{
  "total": 50,
  "page": 1,
  "size": 20,
  "items": [
    {
      "id": "uuid",
      "username": "john_doe",
      "email": "john@example.com",
      "full_name": "John Doe",
      "role": "user",
      "is_active": true,
      "created_at": "2025-01-01T00:00:00Z",
      "updated_at": "2025-01-01T00:00:00Z"
    }
  ]
}
```

#### 7.2 获取用户详情

**GET** `/api/v1/users/{user_id}`

获取单个用户的详细信息。

**认证**: 必需（需要admin权限）

**响应**: `200 OK`
```json
{
  "id": "uuid",
  "username": "john_doe",
  "email": "john@example.com",
  "full_name": "John Doe",
  "role": "user",
  "is_active": true,
  "created_at": "2025-01-01T00:00:00Z",
  "updated_at": "2025-01-01T00:00:00Z"
}
```

#### 7.3 创建用户

**POST** `/api/v1/users`

创建新用户（仅管理员）。

**认证**: 必需（需要admin权限）

**请求体**:
```json
{
  "username": "new_user",
  "email": "user@example.com",
  "password": "SecurePass123",
  "full_name": "New User"
}
```

**响应**: `201 Created`
```json
{
  "id": "uuid",
  "username": "new_user",
  "email": "user@example.com",
  "full_name": "New User",
  "role": "user",
  "is_active": true,
  "created_at": "2025-01-01T00:00:00Z",
  "updated_at": "2025-01-01T00:00:00Z"
}
```

#### 7.4 更新用户信息

**PUT** `/api/v1/users/{user_id}`

更新用户信息（可更新邮箱、全名、密码）。

**认证**: 必需（需要admin权限）

**请求体**:
```json
{
  "email": "newemail@example.com",
  "full_name": "Updated Name",
  "password": "NewPassword123"  // 可选
}
```

**响应**: `200 OK`

#### 7.5 删除用户

**DELETE** `/api/v1/users/{user_id}`

删除用户（会级联删除用户的所有相关数据）。

**认证**: 必需（需要admin权限）

**限制**: 不能删除自己的账号

**响应**: `200 OK`
```json
{
  "message": "用户 john_doe 已删除",
  "deleted_user_id": "uuid"
}
```

#### 7.6 修改用户角色

**PUT** `/api/v1/users/{user_id}/role`

修改用户的角色。

**认证**: 必需（需要admin权限）

**限制**: 不能修改自己的角色

**请求体**:
```json
{
  "role": "admin"  // admin | user | viewer
}
```

**响应**: `200 OK`

#### 7.7 启用/禁用用户

**PUT** `/api/v1/users/{user_id}/status`

启用或禁用用户账号。

**认证**: 必需（需要admin权限）

**限制**: 不能修改自己的状态

**请求体**:
```json
{
  "is_active": false
}
```

**响应**: `200 OK`

---

### 8. 审计日志 (Audit Logs) - 仅管理员

审计日志记录系统中的重要操作，包括登录、命令执行、权限变更等。

#### 8.1 获取审计日志列表

**GET** `/api/v1/audit-logs`

获取审计日志列表（支持筛选、搜索、分页）。

**认证**: 必需（需要admin权限）

**查询参数**:
- `page` (integer): 页码，默认1
- `size` (integer): 每页数量，默认20，最大100
- `user_id` (uuid): 按用户筛选
- `server_id` (uuid): 按服务器筛选
- `action` (string): 按操作类型筛选
- `resource_type` (string): 按资源类型筛选
- `search` (string): 搜索关键词（用户名、操作、资源）

**响应**: `200 OK`
```json
{
  "total": 500,
  "page": 1,
  "size": 20,
  "items": [
    {
      "id": 123,
      "user_id": "uuid",
      "username": "john_doe",
      "server_id": "uuid",
      "server_name": "Web Server 01",
      "action": "execute_command",
      "resource_type": "command",
      "details": {
        "command": "systemctl status nginx",
        "exit_code": 0
      },
      "ip_address": "192.168.1.100",
      "created_at": "2025-01-01T00:00:00Z"
    }
  ]
}
```

#### 8.2 获取审计日志详情

**GET** `/api/v1/audit-logs/{log_id}`

获取单条审计日志的详细信息。

**认证**: 必需（需要admin权限）

**响应**: `200 OK`
```json
{
  "id": 123,
  "user_id": "uuid",
  "username": "john_doe",
  "server_id": "uuid",
  "server_name": "Web Server 01",
  "action": "execute_command",
  "resource_type": "command",
  "details": {
    "command": "systemctl status nginx",
    "exit_code": 0,
    "stdout": "nginx is running",
    "execution_time": 0.5
  },
  "ip_address": "192.168.1.100",
  "created_at": "2025-01-01T00:00:00Z"
}
```

**常见操作类型**:
- `login` - 用户登录
- `logout` - 用户登出
- `register` - 用户注册
- `execute_command` - 执行命令
- `create_server` - 创建服务器
- `update_server` - 更新服务器
- `delete_server` - 删除服务器
- `grant_permission` - 授予权限
- `revoke_permission` - 撤销权限
- `create_user` - 创建用户（管理员）
- `update_user` - 更新用户（管理员）
- `delete_user` - 删除用户（管理员）

---

### 9. WebSocket 端点

#### 9.1 实时监控

**WebSocket** `/api/v1/ws/monitoring/{server_id}`

实时推送服务器性能指标数据。

**认证**: 需要在查询参数中提供token: `?token=<access_token>`

**消息格式**:
```json
{
  "type": "metrics",
  "data": {
    "cpu_percent": 45.2,
    "memory_percent": 62.8,
    "memory_used_mb": 4096,
    "memory_total_mb": 8192,
    "disk_percent": 35.5,
    "network_sent_mb": 1024.5,
    "network_recv_mb": 2048.3,
    "timestamp": "2025-01-01T00:00:00Z"
  }
}
```

**推送频率**: 每3秒一次

#### 9.2 Web Terminal

**WebSocket** `/api/v1/ws/terminal/{server_id}`

Web终端连接，提供SSH交互式终端。

**认证**: 需要在查询参数中提供token: `?token=<access_token>`

**客户端消息** (发送命令):
```json
{
  "type": "input",
  "data": "ls -la\n"
}
```

**服务器消息** (命令输出):
```json
{
  "type": "output",
  "data": "total 48\ndrwxr-xr-x  12 user user 4096 Jan  1 00:00 .\n..."
}
```

**错误消息**:
```json
{
  "type": "error",
  "message": "Connection lost"
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

## 使用示例

### cURL 示例

```bash
# 1. 用户登录
curl -X POST http://localhost:8000/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username": "admin", "password": "admin123"}'

# 2. 获取服务器列表
curl -X GET http://localhost:8000/api/v1/servers \
  -H "Authorization: Bearer <access_token>"

# 3. 执行命令
curl -X POST http://localhost:8000/api/v1/execute/command \
  -H "Authorization: Bearer <access_token>" \
  -H "Content-Type: application/json" \
  -d '{"server_id": "uuid", "command": "uptime"}'
```

### Python 示例

```python
import requests

# 登录
response = requests.post(
    "http://localhost:8000/api/v1/auth/login",
    json={"username": "admin", "password": "admin123"}
)
token = response.json()["access_token"]

# 获取服务器列表
headers = {"Authorization": f"Bearer {token}"}
servers = requests.get(
    "http://localhost:8000/api/v1/servers",
    headers=headers
).json()

# 执行命令
result = requests.post(
    "http://localhost:8000/api/v1/execute/command",
    headers=headers,
    json={"server_id": "uuid", "command": "df -h"}
).json()
```

### JavaScript 示例

```javascript
// 登录
const loginResponse = await fetch('http://localhost:8000/api/v1/auth/login', {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({ username: 'admin', password: 'admin123' })
});
const { access_token } = await loginResponse.json();

// 获取服务器列表
const serversResponse = await fetch('http://localhost:8000/api/v1/servers', {
  headers: { 'Authorization': `Bearer ${access_token}` }
});
const servers = await serversResponse.json();

// WebSocket 连接示例
const ws = new WebSocket(`ws://localhost:8000/api/v1/ws/monitoring/${serverId}?token=${access_token}`);
ws.onmessage = (event) => {
  const data = JSON.parse(event.data);
  console.log('Metrics:', data);
};
```

## 交互式文档

启动应用后访问：
- Swagger UI: `http://localhost:8000/docs`
- ReDoc: `http://localhost:8000/redoc`

## 版本历史

- **v1.0** (2025-01-07): 初始版本，包含所有核心功能
  - 认证与用户管理
  - 服务器管理
  - 实时监控与历史指标
  - 命令执行
  - AI助手
  - 权限管理
  - 审计日志
  - WebSocket支持（实时监控、Web终端）
