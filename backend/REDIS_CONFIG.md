# Redis 配置说明

## 配置项

在 `.env` 文件中，你可以配置以下 Redis 相关参数：

```bash
# Redis配置
REDIS_HOST=localhost              # Redis服务器地址
REDIS_PORT=6379                   # Redis服务器端口
REDIS_PASSWORD=your_password      # Redis密码（如果有的话）
REDIS_DB=0                        # 应用使用的Redis数据库编号
REDIS_CELERY_BROKER_DB=1         # Celery消息队列使用的数据库编号
REDIS_CELERY_RESULT_DB=2         # Celery结果存储使用的数据库编号
```

## 使用场景

### 1. 无密码的 Redis（默认配置）

```bash
REDIS_HOST=localhost
REDIS_PORT=6379
REDIS_PASSWORD=
REDIS_DB=0
REDIS_CELERY_BROKER_DB=1
REDIS_CELERY_RESULT_DB=2
```

生成的 URL：
- Redis URL: `redis://localhost:6379/0`
- Celery Broker: `redis://localhost:6379/1`
- Celery Result Backend: `redis://localhost:6379/2`

### 2. 有密码的 Redis

```bash
REDIS_HOST=localhost
REDIS_PORT=6379
REDIS_PASSWORD=mySecretPassword123
REDIS_DB=0
REDIS_CELERY_BROKER_DB=1
REDIS_CELERY_RESULT_DB=2
```

生成的 URL：
- Redis URL: `redis://:mySecretPassword123@localhost:6379/0`
- Celery Broker: `redis://:mySecretPassword123@localhost:6379/1`
- Celery Result Backend: `redis://:mySecretPassword123@localhost:6379/2`

### 3. 远程 Redis 服务器

```bash
REDIS_HOST=redis.example.com
REDIS_PORT=6379
REDIS_PASSWORD=mySecretPassword123
REDIS_DB=0
REDIS_CELERY_BROKER_DB=1
REDIS_CELERY_RESULT_DB=2
```

## 数据库分配说明

为了避免数据冲突，不同组件使用不同的 Redis 数据库：

- **DB 0**: 应用缓存和会话数据
- **DB 1**: Celery 消息队列（Broker）
- **DB 2**: Celery 任务结果存储（Result Backend）

## 配置 Redis 密码

### 方法 1: 通过 redis.conf

编辑 Redis 配置文件（通常在 `/etc/redis/redis.conf`）：

```bash
# 找到以下行并取消注释，设置密码
requirepass your_password_here
```

重启 Redis：
```bash
sudo systemctl restart redis-server
```

### 方法 2: 通过命令行启动

```bash
redis-server --requirepass your_password_here
```

### 方法 3: 在运行时设置

```bash
redis-cli
127.0.0.1:6379> CONFIG SET requirepass "your_password_here"
OK
```

## 测试连接

### 使用 redis-cli 测试

无密码：
```bash
redis-cli -h localhost -p 6379 -n 0 ping
```

有密码：
```bash
redis-cli -h localhost -p 6379 -a your_password -n 0 ping
```

### 使用 Python 测试

```python
import redis

# 无密码
r = redis.Redis(host='localhost', port=6379, db=0)

# 有密码
r = redis.Redis(host='localhost', port=6379, password='your_password', db=0)

# 测试连接
r.ping()  # 返回 True 表示连接成功
```

## 故障排查

### 错误: "Authentication required"

**原因**: Redis 配置了密码，但你没有在 `.env` 中设置 `REDIS_PASSWORD`

**解决方案**: 在 `.env` 文件中添加：
```bash
REDIS_PASSWORD=your_actual_password
```

### 错误: "Connection refused"

**原因**: Redis 服务未启动

**解决方案**: 启动 Redis 服务
```bash
# 方法1: 使用 systemd
sudo systemctl start redis-server

# 方法2: 直接启动
redis-server --daemonize yes

# 方法3: 使用配置文件启动
redis-server /etc/redis/redis.conf
```

### 错误: "WRONGPASS invalid username-password pair"

**原因**: Redis 密码不正确

**解决方案**: 检查 `.env` 中的 `REDIS_PASSWORD` 是否与 Redis 服务器配置的密码一致
