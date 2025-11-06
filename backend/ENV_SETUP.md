# 环境配置指南

## 快速开始

1. **复制环境变量文件**
```bash
cp .env.example .env
```

2. **生成必需的密钥**

### 生成 ENCRYPTION_KEY (必需)

SSH 凭证加密密钥，用于安全存储服务器密码和私钥。

```bash
python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"
```

示例输出：
```
xQzT-Hn8vYc6MZi2V7fKJ9kL3pN5rS8tA1wD4eG6hB0=
```

将生成的密钥添加到 `.env` 文件：
```bash
ENCRYPTION_KEY=xQzT-Hn8vYc6MZi2V7fKJ9kL3pN5rS8tA1wD4eG6hB0=
```

### 生成 SECRET_KEY (推荐)

JWT 令牌签名密钥。

```bash
openssl rand -hex 32
```

示例输出：
```
a1b2c3d4e5f6...
```

将生成的密钥添加到 `.env` 文件：
```bash
SECRET_KEY=a1b2c3d4e5f6...
```

## 环境变量说明

### 必需配置

| 变量 | 说明 | 示例 |
|------|------|------|
| `DATABASE_URL` | 数据库连接字符串 | `postgresql+asyncpg://user:pass@localhost/db` |
| `SECRET_KEY` | JWT 签名密钥 | `openssl rand -hex 32` |
| `ENCRYPTION_KEY` | SSH 凭证加密密钥 | 见上方生成方法 |

### 可选配置

| 变量 | 说明 | 默认值 |
|------|------|--------|
| `DEBUG` | 调试模式 | `True` |
| `REDIS_URL` | Redis 连接 | `redis://localhost:6379/0` |
| `AI_PROVIDER` | AI 提供商 | `openai` |
| `OPENAI_API_KEY` | OpenAI API 密钥 | - |
| `ANTHROPIC_API_KEY` | Claude API 密钥 | - |

## 数据库配置

### PostgreSQL (推荐)

```bash
DATABASE_TYPE=postgresql
DATABASE_URL=postgresql+asyncpg://postgres:postgres@localhost:5432/server_agent
```

### MySQL

```bash
DATABASE_TYPE=mysql
DATABASE_URL=mysql+aiomysql://root:password@localhost:3306/server_agent
```

## AI 配置

### OpenAI

```bash
AI_PROVIDER=openai
AI_MODEL=gpt-4
OPENAI_API_KEY=sk-...
```

### Anthropic Claude

```bash
AI_PROVIDER=claude
AI_MODEL=claude-3-opus-20240229
ANTHROPIC_API_KEY=sk-ant-...
```

### Ollama (本地)

```bash
AI_PROVIDER=ollama
AI_MODEL=llama2
OLLAMA_BASE_URL=http://localhost:11434
```

## 验证配置

启动应用检查配置是否正确：

```bash
uvicorn app.main:app --reload
```

如果配置正确，你应该看到：
```
INFO:     Uvicorn running on http://0.0.0.0:8000 (Press CTRL+C to quit)
INFO:     Application startup complete.
```

## 常见问题

### ENCRYPTION_KEY 错误

**错误信息**:
```
ValueError: Fernet key must be 32 url-safe base64-encoded bytes.
```

**解决方法**:
```bash
# 生成新密钥
python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"

# 更新 .env 文件
ENCRYPTION_KEY=<生成的密钥>
```

### 数据库连接错误

确保数据库服务正在运行：

```bash
# PostgreSQL
pg_isready

# MySQL
mysqladmin ping
```

### Redis 连接错误

确保 Redis 正在运行：

```bash
redis-cli ping
# 应该返回: PONG
```

## 生产环境建议

1. **不要使用示例密钥** - 始终生成新的密钥
2. **使用强密码** - 数据库和 Redis 使用强密码
3. **启用 HTTPS** - 生产环境必须使用 HTTPS
4. **限制 CORS** - 只允许可信域名
5. **定期备份** - 定期备份数据库和 Redis 数据

## 完整 .env 示例

```bash
# 应用配置
APP_NAME="Server Management System"
APP_VERSION="1.0.0"
DEBUG=False
ENV=production

# 数据库
DATABASE_TYPE=postgresql
DATABASE_URL=postgresql+asyncpg://postgres:secure_password@localhost:5432/server_agent

# Redis
REDIS_URL=redis://:redis_password@localhost:6379/0

# JWT
SECRET_KEY=<生成的密钥>
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=60
REFRESH_TOKEN_EXPIRE_DAYS=7

# SSH 加密
ENCRYPTION_KEY=<生成的密钥>

# AI
AI_PROVIDER=openai
AI_MODEL=gpt-4
OPENAI_API_KEY=sk-...

# Celery
CELERY_BROKER_URL=redis://localhost:6379/1
CELERY_RESULT_BACKEND=redis://localhost:6379/2

# CORS
ALLOWED_ORIGINS=https://yourdomain.com

# 安全
PASSWORD_MIN_LENGTH=8
LOGIN_ATTEMPT_LIMIT=5
LOGIN_LOCKOUT_DURATION=600
COMMAND_EXECUTION_TIMEOUT=30

# 分页
DEFAULT_PAGE_SIZE=20
MAX_PAGE_SIZE=100
```
