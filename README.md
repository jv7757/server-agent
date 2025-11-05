# 服务器管理系统 (Server Management System)

一个现代化的服务器管理系统，支持多用户权限隔离、服务器信息监控、SSH远程管理，以及AI Chatbot智能控制。

[中文](./README.md) | [English](./README_EN.md)

## ✨ 核心功能

- 🔐 **用户认证与授权** - 注册、登录、JWT认证、RBAC权限管理
- 🖥️ **服务器管理** - 增删改查、SSH密钥管理、连接测试
- 📊 **实时监控** - CPU、内存、磁盘、网络实时监控和历史数据
- 🔑 **SSH远程管理** - 命令执行、Web Terminal (xterm.js)
- 🤖 **AI Chatbot** - 自然语言控制服务器（支持OpenAI/Claude/Ollama）
- 👥 **多用户权限隔离** - 资源级权限控制
- 🌍 **国际化** - 中英双语支持

## 🛠️ 技术栈

### 后端
- **FastAPI** 0.104+ - 现代化Python Web框架
- **PostgreSQL** 15+ / **MySQL** 8.0+ - 可配置数据库
- **Redis** - 缓存和消息队列
- **SQLAlchemy** 2.0+ - ORM
- **Paramiko** - SSH连接管理
- **Celery** - 异步任务队列
- **JWT** - 认证授权

### 前端
- **Vue 3** - 渐进式前端框架
- **TypeScript** - 类型安全
- **Vite** - 快速构建工具
- **Element Plus** - UI组件库
- **Pinia** - 状态管理
- **ECharts** - 数据可视化
- **xterm.js** - Web终端
- **Vue I18n** - 国际化

### AI集成
- **适配器模式** 支持多AI提供商：
  - OpenAI (GPT-4, GPT-3.5)
  - Anthropic Claude
  - Ollama (本地部署)

## 📦 快速开始

### 环境要求

- Python 3.10+
- Node.js 18+
- PostgreSQL 15+ / MySQL 8.0+
- Redis 7+
- Docker & Docker Compose (可选)

### 使用Docker Compose (推荐)

```bash
# 1. 克隆项目
git clone <repository-url>
cd server-agent

# 2. 复制环境变量配置
cp backend/.env.example backend/.env

# 3. 编辑配置文件，填入必要的配置
nano backend/.env

# 4. 启动所有服务
docker-compose up -d

# 5. 访问应用
# 前端: http://localhost:5173
# 后端API: http://localhost:8000
# API文档: http://localhost:8000/docs
```

### 手动安装

#### 后端设置

```bash
cd backend

# 创建虚拟环境
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# 安装依赖
pip install -r requirements.txt

# 配置环境变量
cp .env.example .env
# 编辑 .env 文件

# 运行数据库迁移
alembic upgrade head

# 启动服务
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

#### 前端设置

```bash
cd frontend

# 安装依赖
npm install

# 启动开发服务器
npm run dev
```

## 📖 项目结构

```
server-agent/
├── backend/                 # 后端代码
│   ├── app/
│   │   ├── api/            # API路由
│   │   ├── models/         # 数据库模型
│   │   ├── schemas/        # Pydantic模式
│   │   ├── services/       # 业务逻辑
│   │   ├── core/           # 核心功能
│   │   └── tasks/          # Celery任务
│   ├── tests/              # 测试
│   └── alembic/            # 数据库迁移
├── frontend/               # 前端代码
│   ├── src/
│   │   ├── views/          # 页面组件
│   │   ├── components/     # 通用组件
│   │   ├── stores/         # 状态管理
│   │   └── api/            # API请求
└── docker-compose.yml      # Docker配置
```

## 🚀 主要功能

### 1. 服务器管理

- 添加、编辑、删除服务器
- SSH密钥或密码认证
- 连接状态实时检测
- 服务器标签分类

### 2. 实时监控

- CPU使用率趋势图
- 内存使用情况
- 磁盘空间监控
- 网络流量统计
- 历史数据查询

### 3. SSH终端

- 浏览器内SSH终端
- 命令执行记录
- 危险命令拦截
- 操作审计日志

### 4. AI Chatbot

支持自然语言操作：

```
用户: "显示所有在线的服务器"
AI: "当前有3台服务器在线：Web-01, DB-01, Cache-01"

用户: "检查192.168.1.100的磁盘使用情况"
AI: "服务器磁盘使用率45.8%，剩余空间充足。"

用户: "重启nginx服务"
AI: "已在服务器Web-01上重启nginx服务，状态：成功"
```

### 5. 权限系统

- **Admin**: 全部权限
- **User**: 管理自己的服务器，可被授权访问其他服务器
- **Viewer**: 只读权限

## 🔧 配置

### 环境变量

查看 `backend/.env.example` 获取完整配置示例：

```env
# 数据库
DATABASE_TYPE=postgresql
DATABASE_URL=postgresql://user:pass@localhost/db

# AI配置
AI_PROVIDER=openai  # openai, claude, ollama
AI_MODEL=gpt-4
OPENAI_API_KEY=sk-...

# JWT
SECRET_KEY=your-secret-key
```

### 数据库选择

支持PostgreSQL和MySQL，通过配置切换：

```env
# PostgreSQL
DATABASE_URL=postgresql://user:password@localhost:5432/server_agent

# MySQL
DATABASE_URL=mysql+aiomysql://user:password@localhost:3306/server_agent
```

## 🧪 测试

```bash
# 后端测试
cd backend
pytest

# 前端测试
cd frontend
npm run test
```

## 📝 API文档

启动后端服务后访问：

- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

## 🤝 贡献

欢迎贡献代码！请查看 [DESIGN.md](./DESIGN.md) 了解项目设计。

## 📄 许可证

MIT License

## 🔗 相关文档

- [系统设计文档](./DESIGN.md)
- [API文档](http://localhost:8000/docs)
- [部署指南](./docs/deployment.md) (待完善)

## 📧 联系方式

有问题或建议？欢迎提交Issue或Pull Request！
