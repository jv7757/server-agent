# 服务器管理系统 - 系统设计文档

## 1. 系统概述

一个现代化的服务器管理系统，支持多用户权限隔离、服务器信息监控、SSH远程管理，以及AI Chatbot智能控制。

### 1.1 核心功能
- 🔐 用户认证与授权（注册、登录、权限管理）
- 🖥️ 服务器CRUD管理（增删改查）
- 📊 服务器信息监控（CPU、内存、磁盘、网络）
- 🔑 SSH密钥管理与远程连接
- 🤖 AI Chatbot智能控制
- 👥 多用户权限隔离

---

## 2. 技术栈

### 2.1 后端技术栈
- **框架**: FastAPI 0.104+
- **数据库**: PostgreSQL 15+ / MySQL 8.0+ (可配置) + Redis (缓存/会话)
- **ORM**: SQLAlchemy 2.0+ (支持多数据库适配)
- **SSH管理**: Paramiko 3.3+
- **认证**: JWT (JSON Web Token)
- **密码加密**: Passlib + Bcrypt
- **数据验证**: Pydantic V2
- **异步任务**: Celery + Redis
- **AI集成**: 适配器模式支持 OpenAI / Claude / Ollama (可扩展)
- **日志**: Loguru

### 2.2 前端技术栈
- **框架**: Vue 3.3+ (Composition API)
- **构建工具**: Vite 5+
- **UI框架**: Element Plus
- **状态管理**: Pinia
- **路由**: Vue Router 4
- **HTTP客户端**: Axios
- **图表**: ECharts
- **终端**: xterm.js (Web Terminal)
- **WebSocket**: Socket.io-client (实时监控)
- **国际化**: Vue I18n (中英双语)
- **TypeScript**: 全面使用

### 2.3 开发工具
- **容器化**: Docker + Docker Compose
- **API文档**: FastAPI自动生成 (OpenAPI/Swagger)
- **代码规范**: Black, Flake8, ESLint, Prettier
- **版本控制**: Git

---

## 3. 系统架构

```
┌─────────────────────────────────────────────────────┐
│                   前端 (Vue 3)                       │
│  ┌─────────┬──────────┬──────────┬──────────────┐  │
│  │ 登录注册 │ 服务器列表 │ 监控面板 │ AI Chatbot  │  │
│  └─────────┴──────────┴──────────┴──────────────┘  │
└───────────────────┬─────────────────────────────────┘
                    │ HTTP/WebSocket
┌───────────────────┴─────────────────────────────────┐
│              后端 API (FastAPI)                      │
│  ┌─────────┬──────────┬──────────┬──────────────┐  │
│  │ 认证模块 │ 服务器管理 │ 监控模块 │ AI控制模块  │  │
│  └─────────┴──────────┴──────────┴──────────────┘  │
└───────────────────┬─────────────────────────────────┘
                    │
        ┌───────────┼───────────┐
        │           │           │
┌───────▼──┐  ┌────▼────┐  ┌──▼─────────┐
│PostgreSQL│  │  Redis  │  │被管理服务器 │
│  数据库   │  │缓存/队列 │  │ (Paramiko)│
└──────────┘  └─────────┘  └────────────┘
```

---

## 4. 数据库设计

### 4.1 用户表 (users)
```sql
CREATE TABLE users (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    username VARCHAR(50) UNIQUE NOT NULL,
    email VARCHAR(100) UNIQUE NOT NULL,
    hashed_password VARCHAR(255) NOT NULL,
    full_name VARCHAR(100),
    role VARCHAR(20) NOT NULL DEFAULT 'user', -- admin, user, viewer
    is_active BOOLEAN DEFAULT true,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

### 4.2 服务器表 (servers)
```sql
CREATE TABLE servers (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name VARCHAR(100) NOT NULL,
    host VARCHAR(255) NOT NULL,
    port INTEGER DEFAULT 22,
    description TEXT,
    owner_id UUID REFERENCES users(id) ON DELETE CASCADE,

    -- SSH认证信息 (加密存储)
    ssh_username VARCHAR(100),
    ssh_password_encrypted TEXT,
    ssh_key_encrypted TEXT,

    -- 服务器标签
    tags JSONB DEFAULT '[]',

    -- 连接状态
    status VARCHAR(20) DEFAULT 'unknown', -- online, offline, error, unknown
    last_checked_at TIMESTAMP,

    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

### 4.3 服务器监控数据表 (server_metrics)
```sql
CREATE TABLE server_metrics (
    id BIGSERIAL PRIMARY KEY,
    server_id UUID REFERENCES servers(id) ON DELETE CASCADE,

    -- CPU信息
    cpu_usage_percent FLOAT,
    cpu_cores INTEGER,

    -- 内存信息
    memory_total_mb BIGINT,
    memory_used_mb BIGINT,
    memory_usage_percent FLOAT,

    -- 磁盘信息
    disk_total_gb BIGINT,
    disk_used_gb BIGINT,
    disk_usage_percent FLOAT,

    -- 网络信息
    network_bytes_sent BIGINT,
    network_bytes_recv BIGINT,

    -- 系统信息
    uptime_seconds BIGINT,
    load_average JSONB, -- [1min, 5min, 15min]

    collected_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

    INDEX idx_server_id (server_id),
    INDEX idx_collected_at (collected_at)
);
```

### 4.4 用户服务器权限表 (user_server_permissions)
```sql
CREATE TABLE user_server_permissions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID REFERENCES users(id) ON DELETE CASCADE,
    server_id UUID REFERENCES servers(id) ON DELETE CASCADE,
    permission VARCHAR(20) NOT NULL, -- read, write, execute, admin
    granted_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    granted_by UUID REFERENCES users(id),

    UNIQUE(user_id, server_id)
);
```

### 4.5 AI对话历史表 (chat_history)
```sql
CREATE TABLE chat_history (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID REFERENCES users(id) ON DELETE CASCADE,
    server_id UUID REFERENCES servers(id) ON DELETE SET NULL,
    role VARCHAR(20) NOT NULL, -- user, assistant, system
    content TEXT NOT NULL,
    metadata JSONB, -- 存储命令执行结果等
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

    INDEX idx_user_id (user_id),
    INDEX idx_created_at (created_at)
);
```

### 4.6 操作日志表 (audit_logs)
```sql
CREATE TABLE audit_logs (
    id BIGSERIAL PRIMARY KEY,
    user_id UUID REFERENCES users(id) ON DELETE SET NULL,
    server_id UUID REFERENCES servers(id) ON DELETE SET NULL,
    action VARCHAR(50) NOT NULL, -- create, update, delete, execute_command
    resource_type VARCHAR(50), -- server, user, permission
    details JSONB,
    ip_address INET,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

    INDEX idx_user_id (user_id),
    INDEX idx_created_at (created_at)
);
```

---

## 5. API接口设计

### 5.1 认证模块 (`/api/v1/auth`)

#### 用户注册
```
POST /api/v1/auth/register
Request:
{
    "username": "john_doe",
    "email": "john@example.com",
    "password": "SecurePass123!",
    "full_name": "John Doe"
}
Response: {
    "id": "uuid",
    "username": "john_doe",
    "email": "john@example.com",
    "role": "user"
}
```

#### 用户登录
```
POST /api/v1/auth/login
Request:
{
    "username": "john_doe",
    "password": "SecurePass123!"
}
Response: {
    "access_token": "eyJhbGc...",
    "refresh_token": "eyJhbGc...",
    "token_type": "bearer",
    "expires_in": 3600
}
```

#### 刷新Token
```
POST /api/v1/auth/refresh
Headers: Authorization: Bearer <refresh_token>
Response: {
    "access_token": "eyJhbGc...",
    "token_type": "bearer",
    "expires_in": 3600
}
```

### 5.2 服务器管理模块 (`/api/v1/servers`)

#### 获取服务器列表
```
GET /api/v1/servers?page=1&size=20&status=online&tags=production
Response: {
    "total": 50,
    "page": 1,
    "size": 20,
    "items": [
        {
            "id": "uuid",
            "name": "Web Server 01",
            "host": "192.168.1.100",
            "port": 22,
            "status": "online",
            "tags": ["production", "web"],
            "owner": {
                "id": "uuid",
                "username": "john_doe"
            },
            "last_checked_at": "2025-11-05T10:30:00Z"
        }
    ]
}
```

#### 添加服务器
```
POST /api/v1/servers
Request:
{
    "name": "Database Server",
    "host": "192.168.1.200",
    "port": 22,
    "description": "Production MySQL Server",
    "ssh_username": "root",
    "ssh_password": "password", // 或使用ssh_key
    "tags": ["production", "database"]
}
Response: {
    "id": "uuid",
    "name": "Database Server",
    "status": "checking",
    "created_at": "2025-11-05T10:35:00Z"
}
```

#### 更新服务器
```
PUT /api/v1/servers/{server_id}
Request: {
    "name": "Updated Server Name",
    "description": "Updated description",
    "tags": ["production", "updated"]
}
```

#### 删除服务器
```
DELETE /api/v1/servers/{server_id}
Response: {
    "message": "Server deleted successfully"
}
```

#### 测试服务器连接
```
POST /api/v1/servers/{server_id}/test-connection
Response: {
    "status": "success",
    "message": "Connection established",
    "latency_ms": 45
}
```

### 5.3 服务器监控模块 (`/api/v1/servers/{server_id}/metrics`)

#### 获取实时监控数据
```
GET /api/v1/servers/{server_id}/metrics/current
Response: {
    "cpu_usage_percent": 35.5,
    "memory_usage_percent": 62.3,
    "disk_usage_percent": 45.8,
    "network": {
        "bytes_sent": 1234567890,
        "bytes_recv": 9876543210
    },
    "uptime_seconds": 864000,
    "collected_at": "2025-11-05T10:40:00Z"
}
```

#### 获取历史监控数据
```
GET /api/v1/servers/{server_id}/metrics/history?start=2025-11-04&end=2025-11-05&interval=1h
Response: {
    "metrics": [
        {
            "timestamp": "2025-11-04T00:00:00Z",
            "cpu_usage_percent": 25.3,
            "memory_usage_percent": 58.2,
            "disk_usage_percent": 45.5
        }
    ]
}
```

### 5.4 SSH命令执行模块 (`/api/v1/servers/{server_id}/execute`)

#### 执行命令
```
POST /api/v1/servers/{server_id}/execute
Request:
{
    "command": "ls -la /var/log",
    "timeout": 30
}
Response: {
    "exit_code": 0,
    "stdout": "...",
    "stderr": "",
    "execution_time_ms": 150
}
```

### 5.5 AI Chatbot模块 (`/api/v1/chat`)

#### 发送聊天消息
```
POST /api/v1/chat
Request:
{
    "message": "帮我检查服务器192.168.1.100的磁盘使用情况",
    "server_id": "uuid" // 可选，指定操作的服务器
}
Response: {
    "reply": "我已经检查了服务器的磁盘使用情况，当前使用了45.8%，剩余空间充足。",
    "actions_taken": [
        {
            "type": "execute_command",
            "command": "df -h",
            "result": "..."
        }
    ],
    "suggestions": [
        "您可以使用'清理日志'命令释放更多空间"
    ]
}
```

#### 获取聊天历史
```
GET /api/v1/chat/history?limit=50
Response: {
    "messages": [
        {
            "id": "uuid",
            "role": "user",
            "content": "检查服务器状态",
            "created_at": "2025-11-05T10:30:00Z"
        },
        {
            "id": "uuid",
            "role": "assistant",
            "content": "所有服务器运行正常",
            "created_at": "2025-11-05T10:30:05Z"
        }
    ]
}
```

---

## 6. 前端页面结构

### 6.1 页面路由设计

```
/                           # 首页/登录页
/register                   # 注册页
/dashboard                  # 仪表盘（需要认证）
  /servers                  # 服务器列表
  /servers/add              # 添加服务器
  /servers/:id              # 服务器详情
    /overview               # 概览
    /metrics                # 监控数据
    /terminal               # SSH终端（Web Terminal）
    /settings               # 服务器设置
  /chat                     # AI Chatbot
  /profile                  # 个人资料
  /users                    # 用户管理（仅管理员）
  /audit-logs               # 操作日志（仅管理员）
```

### 6.2 页面组件结构

#### 仪表盘 (Dashboard)
- 服务器总览卡片（在线/离线/总数）
- 最近告警列表
- 快速操作入口
- 资源使用趋势图

#### 服务器列表 (Server List)
- 表格视图/卡片视图切换
- 搜索和筛选（按状态、标签、所有者）
- 批量操作（批量删除、批量测试连接）
- 分页

#### 服务器详情 (Server Detail)
- **概览标签页**：基本信息、连接状态、标签
- **监控标签页**：实时CPU/内存/磁盘图表（ECharts），历史数据曲线
- **终端标签页**：Web Terminal (使用xterm.js + WebSocket)
- **设置标签页**：编辑服务器信息、SSH密钥管理、权限设置

#### AI Chatbot
- 聊天界面（类似ChatGPT）
- 支持markdown渲染
- 代码块高亮
- 命令执行结果展示
- 服务器快速切换

---

## 7. 权限系统设计

### 7.1 角色定义

| 角色 | 权限 |
|------|------|
| **admin** | 所有权限，可管理所有用户和服务器 |
| **user** | 可管理自己创建的服务器，可被授权访问其他服务器 |
| **viewer** | 只读权限，可查看被授权的服务器信息，不能执行命令 |

### 7.2 权限检查流程

1. JWT Token验证（用户身份）
2. 资源所有权检查（是否是资源owner）
3. 权限表检查（是否被授权访问）
4. 操作权限检查（read/write/execute）

---

## 8. AI Chatbot集成方案

### 8.1 功能设计

AI Chatbot支持自然语言理解用户意图，并执行相应操作：

**支持的操作类型**：
1. **信息查询**：
   - "显示所有在线的服务器"
   - "192.168.1.100的CPU使用率是多少？"
   - "哪些服务器磁盘快满了？"

2. **命令执行**：
   - "帮我重启nginx服务"
   - "检查服务器的日志文件"
   - "清理/tmp目录下的临时文件"

3. **批量操作**：
   - "重启所有标记为'web'的服务器"
   - "检查所有生产环境服务器的内存使用情况"

4. **智能建议**：
   - 根据服务器状态提供优化建议
   - 告警预测和故障诊断

### 8.2 实现方案

```python
# AI处理流程
1. 用户输入 -> 2. 意图识别 -> 3. 参数提取 -> 4. 权限验证
   -> 5. 执行操作 -> 6. 生成响应 -> 7. 返回结果
```

**技术实现**：
- 使用OpenAI Function Calling或Anthropic Claude Tool Use
- 定义工具函数（list_servers, execute_command, get_metrics等）
- AI自动选择调用合适的函数
- 实施安全防护（命令白名单、危险命令拦截）

### 8.3 AI适配器模式设计

为了支持多个AI提供商（OpenAI、Claude、Ollama等），我们采用**适配器模式**：

```python
# AI提供商抽象接口
class AIProvider(ABC):
    @abstractmethod
    async def chat(self, messages: List[Dict], tools: List[Dict]) -> Dict:
        pass

    @abstractmethod
    async def stream_chat(self, messages: List[Dict], tools: List[Dict]):
        pass

# OpenAI适配器
class OpenAIProvider(AIProvider):
    def __init__(self, api_key: str, model: str = "gpt-4"):
        self.client = OpenAI(api_key=api_key)
        self.model = model

    async def chat(self, messages: List[Dict], tools: List[Dict]) -> Dict:
        response = await self.client.chat.completions.create(
            model=self.model,
            messages=messages,
            tools=tools
        )
        return self._format_response(response)

# Claude适配器
class ClaudeProvider(AIProvider):
    def __init__(self, api_key: str, model: str = "claude-3-5-sonnet-20241022"):
        self.client = Anthropic(api_key=api_key)
        self.model = model

    async def chat(self, messages: List[Dict], tools: List[Dict]) -> Dict:
        response = await self.client.messages.create(
            model=self.model,
            messages=messages,
            tools=tools
        )
        return self._format_response(response)

# Ollama适配器
class OllamaProvider(AIProvider):
    def __init__(self, base_url: str = "http://localhost:11434", model: str = "llama2"):
        self.base_url = base_url
        self.model = model

    async def chat(self, messages: List[Dict], tools: List[Dict]) -> Dict:
        # Ollama API调用
        ...

# AI服务工厂
class AIServiceFactory:
    @staticmethod
    def create(provider: str, **kwargs) -> AIProvider:
        if provider == "openai":
            return OpenAIProvider(**kwargs)
        elif provider == "claude":
            return ClaudeProvider(**kwargs)
        elif provider == "ollama":
            return OllamaProvider(**kwargs)
        else:
            raise ValueError(f"Unsupported AI provider: {provider}")
```

**配置方式**：
```env
AI_PROVIDER=openai  # 可选: openai, claude, ollama
AI_MODEL=gpt-4      # 根据provider选择对应模型
```

**扩展新的AI提供商**：
1. 创建新的适配器类，继承`AIProvider`
2. 实现`chat`和`stream_chat`方法
3. 在工厂类中注册新提供商
4. 无需修改业务逻辑代码

---

## 9. 安全措施

### 9.1 认证安全
- JWT Token有效期：Access Token 1小时，Refresh Token 7天
- 密码强度要求：最少8位，包含大小写字母、数字、特殊字符
- Bcrypt密码哈希（成本因子12）
- 登录失败次数限制（5次失败后锁定10分钟）

### 9.2 SSH密钥安全
- 使用Fernet加密存储SSH密码和私钥
- 密钥存储在环境变量或密钥管理服务（如AWS KMS）
- 支持SSH Key认证优先于密码认证

### 9.3 命令执行安全
- 危险命令黑名单（rm -rf /, mkfs, dd等）
- 命令执行超时限制（默认30秒）
- 操作审计日志记录
- AI命令需要用户确认（可选）

### 9.4 API安全
- CORS配置
- 请求速率限制（每分钟60次）
- SQL注入防护（使用ORM参数化查询）
- XSS防护（前端输入验证和转义）

---

## 10. 项目目录结构

```
server-agent/
├── backend/                       # 后端代码
│   ├── app/
│   │   ├── __init__.py
│   │   ├── main.py               # FastAPI应用入口
│   │   ├── config.py             # 配置管理
│   │   ├── database.py           # 数据库连接
│   │   ├── dependencies.py       # 依赖注入
│   │   │
│   │   ├── models/               # SQLAlchemy模型
│   │   │   ├── __init__.py
│   │   │   ├── user.py
│   │   │   ├── server.py
│   │   │   ├── metric.py
│   │   │   └── chat.py
│   │   │
│   │   ├── schemas/              # Pydantic模式
│   │   │   ├── __init__.py
│   │   │   ├── user.py
│   │   │   ├── server.py
│   │   │   ├── metric.py
│   │   │   └── chat.py
│   │   │
│   │   ├── api/                  # API路由
│   │   │   ├── __init__.py
│   │   │   ├── v1/
│   │   │   │   ├── __init__.py
│   │   │   │   ├── auth.py
│   │   │   │   ├── servers.py
│   │   │   │   ├── metrics.py
│   │   │   │   ├── execute.py
│   │   │   │   └── chat.py
│   │   │
│   │   ├── services/             # 业务逻辑
│   │   │   ├── __init__.py
│   │   │   ├── auth_service.py
│   │   │   ├── server_service.py
│   │   │   ├── ssh_service.py    # Paramiko封装
│   │   │   ├── metrics_service.py
│   │   │   └── ai_service.py     # AI集成
│   │   │
│   │   ├── core/                 # 核心功能
│   │   │   ├── __init__.py
│   │   │   ├── security.py       # JWT, 密码加密
│   │   │   ├── encryption.py     # SSH密钥加密
│   │   │   └── permissions.py    # 权限检查
│   │   │
│   │   ├── tasks/                # Celery异步任务
│   │   │   ├── __init__.py
│   │   │   ├── monitor_tasks.py  # 定期监控任务
│   │   │   └── cleanup_tasks.py
│   │   │
│   │   └── utils/                # 工具函数
│   │       ├── __init__.py
│   │       ├── logger.py
│   │       └── validators.py
│   │
│   ├── alembic/                  # 数据库迁移
│   │   ├── versions/
│   │   └── env.py
│   │
│   ├── tests/                    # 测试代码
│   │   ├── test_auth.py
│   │   ├── test_servers.py
│   │   └── test_ssh.py
│   │
│   ├── requirements.txt          # Python依赖
│   ├── requirements-dev.txt      # 开发依赖
│   ├── .env.example              # 环境变量示例
│   ├── alembic.ini               # Alembic配置
│   └── Dockerfile                # 后端Docker镜像
│
├── frontend/                     # 前端代码
│   ├── src/
│   │   ├── main.ts               # 入口文件
│   │   ├── App.vue
│   │   │
│   │   ├── router/               # 路由配置
│   │   │   └── index.ts
│   │   │
│   │   ├── stores/               # Pinia状态管理
│   │   │   ├── auth.ts
│   │   │   ├── server.ts
│   │   │   └── chat.ts
│   │   │
│   │   ├── views/                # 页面组件
│   │   │   ├── LoginView.vue
│   │   │   ├── RegisterView.vue
│   │   │   ├── DashboardView.vue
│   │   │   ├── ServerListView.vue
│   │   │   ├── ServerDetailView.vue
│   │   │   └── ChatView.vue
│   │   │
│   │   ├── components/           # 通用组件
│   │   │   ├── ServerCard.vue
│   │   │   ├── MetricsChart.vue
│   │   │   ├── Terminal.vue
│   │   │   └── ChatMessage.vue
│   │   │
│   │   ├── api/                  # API请求封装
│   │   │   ├── client.ts         # Axios配置
│   │   │   ├── auth.ts
│   │   │   ├── servers.ts
│   │   │   └── chat.ts
│   │   │
│   │   ├── types/                # TypeScript类型定义
│   │   │   ├── user.ts
│   │   │   ├── server.ts
│   │   │   └── chat.ts
│   │   │
│   │   ├── utils/                # 工具函数
│   │   │   └── format.ts
│   │   │
│   │   └── assets/               # 静态资源
│   │       └── styles/
│   │
│   ├── public/
│   ├── package.json
│   ├── tsconfig.json
│   ├── vite.config.ts
│   └── Dockerfile                # 前端Docker镜像
│
├── docker-compose.yml            # Docker编排
├── .gitignore
├── README.md
└── DESIGN.md                     # 本文档
```

---

## 11. 开发计划

### Phase 1: 基础设施搭建 (1-2天)
- [ ] 初始化项目结构
- [ ] 配置数据库（PostgreSQL + Redis）
- [ ] 设置Docker开发环境
- [ ] 创建数据库模型和迁移
- [ ] 配置FastAPI基础框架

### Phase 2: 用户认证模块 (1-2天)
- [ ] 实现用户注册/登录API
- [ ] JWT Token生成和验证
- [ ] 密码加密和验证
- [ ] 前端登录/注册页面
- [ ] 权限中间件

### Phase 3: 服务器管理模块 (2-3天)
- [ ] 服务器CRUD API
- [ ] SSH连接封装（Paramiko）
- [ ] SSH密钥加密存储
- [ ] 前端服务器列表页面
- [ ] 前端服务器详情页面
- [ ] 连接测试功能

### Phase 4: 监控模块 (2-3天)
- [ ] 服务器指标采集（CPU/内存/磁盘/网络）
- [ ] 指标存储和查询API
- [ ] Celery定时任务（定期采集）
- [ ] 前端监控图表（ECharts）
- [ ] 实时数据推送（WebSocket）

### Phase 5: SSH命令执行 (1-2天)
- [ ] 命令执行API
- [ ] 命令安全检查
- [ ] Web Terminal集成（xterm.js）
- [ ] 操作审计日志

### Phase 6: AI Chatbot (2-3天)
- [ ] AI服务集成（OpenAI/Claude）
- [ ] Function Calling配置
- [ ] 工具函数定义（列表、查询、执行）
- [ ] 聊天历史存储
- [ ] 前端聊天界面
- [ ] 命令确认机制

### Phase 7: 权限系统 (1-2天)
- [ ] 用户角色管理
- [ ] 服务器权限分配
- [ ] 权限检查中间件
- [ ] 前端权限控制

### Phase 8: 测试和优化 (2-3天)
- [ ] 单元测试
- [ ] 集成测试
- [ ] 性能优化
- [ ] 安全审计
- [ ] 文档完善

**总预计时间**: 12-20天

---

## 12. 环境变量配置示例

```env
# 数据库配置
DATABASE_TYPE=postgresql  # 可选: postgresql, mysql
DATABASE_URL=postgresql://user:password@localhost:5432/server_agent
# MySQL示例: mysql+aiomysql://user:password@localhost:3306/server_agent
REDIS_URL=redis://localhost:6379/0

# JWT配置
SECRET_KEY=your-secret-key-here-change-in-production
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=60
REFRESH_TOKEN_EXPIRE_DAYS=7

# SSH密钥加密
ENCRYPTION_KEY=your-fernet-key-here

# AI配置
AI_PROVIDER=openai  # 可选: openai, claude, ollama
AI_MODEL=gpt-4      # openai: gpt-4, gpt-3.5-turbo | claude: claude-3-5-sonnet-20241022 | ollama: llama2, mistral
OPENAI_API_KEY=sk-...
ANTHROPIC_API_KEY=sk-ant-...
OLLAMA_BASE_URL=http://localhost:11434

# 邮件配置（可选，用于密码重置）
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USER=your-email@gmail.com
SMTP_PASSWORD=your-password

# CORS配置
ALLOWED_ORIGINS=http://localhost:5173,http://localhost:3000

# 日志配置
LOG_LEVEL=INFO
```

---

## 13. 部署方案

### 开发环境
```bash
# 启动所有服务
docker-compose up -d

# 访问地址
Frontend: http://localhost:5173
Backend API: http://localhost:8000
API Docs: http://localhost:8000/docs
```

### 生产环境
- 使用Nginx反向代理
- HTTPS证书（Let's Encrypt）
- 数据库主从复制
- Redis持久化
- 应用监控（Prometheus + Grafana）
- 日志聚合（ELK Stack）

---

## 14. 核心技术亮点

1. **现代化技术栈**: FastAPI + Vue 3 + TypeScript
2. **完整的权限系统**: RBAC + 资源级权限控制
3. **实时监控**: WebSocket推送 + 历史数据分析
4. **AI智能控制**: 自然语言操作服务器
5. **安全设计**: 多层加密 + 审计日志 + 危险命令防护
6. **高性能**: 异步I/O + Redis缓存 + 数据库优化
7. **可扩展性**: 微服务架构 + 容器化部署
8. **完善的开发体验**: 自动API文档 + 类型安全 + 热重载

---

## 15. 技术选型确认 ✅

以下设计选择已确认：

1. **数据库选择**: ✅ 支持 PostgreSQL / MySQL（可配置） + Redis
2. **AI供应商**: ✅ 适配器模式支持 OpenAI / Claude / Ollama（可扩展）
3. **UI框架**: ✅ Element Plus
4. **Web Terminal**: ✅ 实现（使用xterm.js + WebSocket）
5. **多语言支持**: ✅ 国际化（i18n）- 中英双语
6. **邮件通知**: ⏸️ 待后续扩展
7. **容器编排**: 开发环境使用Docker Compose，生产环境可选Kubernetes

---

**设计完成日期**: 2025-11-05
**设计确认日期**: 2025-11-05
**文档版本**: v1.1
