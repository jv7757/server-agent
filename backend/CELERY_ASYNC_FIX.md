# Celery + AsyncIO + SQLAlchemy 事件循环问题修复

## 问题描述

在 Celery worker 中运行异步数据库任务时，会出现以下错误：

```
RuntimeError: Task got Future attached to a different loop
RuntimeError: Event loop is closed
```

## 问题原因

1. **事件循环冲突**：
   - Celery 使用 fork/prefork worker 模型
   - 主进程创建的 SQLAlchemy async engine 绑定到主进程的事件循环
   - Worker 进程 fork 后，事件循环引用失效
   - `asyncio.run()` 创建新的事件循环，但 engine 仍绑定到旧循环

2. **连接池问题**：
   - 异步连接池在进程 fork 时无法正确复制
   - 多个 worker 进程共享同一个连接池会导致冲突

## 解决方案

### 1. 使用 NullPool 禁用连接池

在 `app/database.py` 中：

```python
from sqlalchemy.pool import NullPool

engine = create_async_engine(
    settings.database_url,
    poolclass=NullPool,  # 关键：不使用连接池
)
```

**优点**：
- 每次都创建新连接，避免进程间共享
- 适合 Celery 这种 fork 模型的场景

**缺点**：
- 每次请求都建立新连接，性能略有下降
- 对于 FastAPI web 请求可能影响性能

### 2. 为 Celery 任务创建独立会话工厂

在 `app/database.py` 中添加：

```python
def get_celery_async_session():
    """为 Celery 任务创建独立的异步数据库会话"""
    celery_engine = create_async_engine(
        settings.database_url,
        poolclass=NullPool,
    )
    return sessionmaker(
        celery_engine,
        class_=AsyncSession,
        expire_on_commit=False,
    )
```

在 `app/tasks/monitor_tasks.py` 中使用：

```python
async def _collect_all_servers_metrics_async():
    # 为每个任务创建独立的会话
    CeleryAsyncSession = get_celery_async_session()
    async with CeleryAsyncSession() as db:
        # ... 执行数据库操作
```

### 3. 每个任务独立创建事件循环

使用 `asyncio.run()` 而不是全局事件循环：

```python
@celery_app.task
def collect_all_servers_metrics():
    # 每次任务都创建新的事件循环
    asyncio.run(_collect_all_servers_metrics_async())
```

## 最佳实践

### DO ✅

1. **为 Celery 任务使用独立的会话工厂**
   ```python
   CeleryAsyncSession = get_celery_async_session()
   async with CeleryAsyncSession() as db:
       # 数据库操作
   ```

2. **使用 NullPool 避免连接池问题**
   ```python
   create_async_engine(url, poolclass=NullPool)
   ```

3. **使用 asyncio.run() 创建独立事件循环**
   ```python
   def celery_task():
       asyncio.run(async_function())
   ```

4. **确保每个异步上下文都正确关闭**
   ```python
   async with session:
       # ... 操作
   # 自动关闭连接
   ```

### DON'T ❌

1. **不要在全局共享异步引擎**
   ```python
   # 错误：在主进程创建，fork 后失效
   engine = create_async_engine(url)

   @celery_app.task
   def task():
       async with AsyncSessionLocal():  # 会失败
           pass
   ```

2. **不要在 Celery 任务中使用连接池**
   ```python
   # 错误：连接池在 fork 后会冲突
   engine = create_async_engine(url, pool_size=10)
   ```

3. **不要重用事件循环**
   ```python
   # 错误：全局事件循环在 worker fork 后失效
   loop = asyncio.get_event_loop()
   loop.run_until_complete(task())
   ```

## 性能考虑

### NullPool 的性能影响

- **Web 请求**：每次 HTTP 请求都创建新连接，适度影响性能
- **Celery 任务**：任务执行间隔较长（如每分钟），性能影响可忽略

### 优化建议

如果性能是关键问题，可以考虑：

1. **分离 Web 和 Celery 的引擎配置**：
   - Web 使用常规连接池
   - Celery 使用 NullPool

2. **使用 Celery worker signals**：
   ```python
   from celery.signals import worker_process_init

   @worker_process_init.connect
   def init_worker(**kwargs):
       # 在 worker 进程初始化时创建新引擎
       global engine
       engine = create_async_engine(url)
   ```

3. **考虑使用同步 SQLAlchemy**：
   - 如果 Celery 任务不需要高并发
   - 同步代码更简单，避免事件循环问题

## 相关资源

- [SQLAlchemy Async FAQ](https://docs.sqlalchemy.org/en/20/orm/extensions/asyncio.html)
- [Celery Worker Lifecycle](https://docs.celeryq.dev/en/stable/userguide/workers.html)
- [Python asyncio Event Loop](https://docs.python.org/3/library/asyncio-eventloop.html)

## 排查清单

如果仍然遇到事件循环错误，检查：

- [ ] 所有 Celery 任务都使用 `get_celery_async_session()`
- [ ] 引擎配置使用了 `poolclass=NullPool`
- [ ] 任务使用 `asyncio.run()` 而不是全局事件循环
- [ ] 异步上下文管理器正确关闭（使用 `async with`）
- [ ] 没有在任务间共享异步对象（如 engine, session）

## 测试

测试 Celery 任务是否正常：

```bash
# 启动 Celery worker
celery -A app.tasks.celery_app worker --loglevel=info

# 在 Python 中触发任务
from app.tasks.monitor_tasks import collect_all_servers_metrics
result = collect_all_servers_metrics.delay()
```

应该看到任务成功执行，没有事件循环错误。
