# 测试文档

## 概述

本项目使用 `pytest` 进行测试，包含单元测试和集成测试。

## 测试结构

```
tests/
├── __init__.py              # 测试包初始化
├── conftest.py              # pytest配置和共享fixtures
├── README.md                # 本文档
├── test_api_auth.py         # 认证API测试
├── test_api_servers.py      # 服务器管理API测试
├── test_api_permissions.py  # 权限管理API测试
├── test_api_users.py        # 用户管理API测试
├── test_api_audit_logs.py   # 审计日志API测试
└── test_security.py         # 安全工具函数单元测试
```

## 安装依赖

```bash
cd backend
pip install -r requirements.txt
```

## 运行测试

### 运行所有测试

```bash
pytest
```

### 运行特定模块的测试

```bash
# 认证测试
pytest tests/test_api_auth.py

# 服务器管理测试
pytest tests/test_api_servers.py

# 权限管理测试
pytest tests/test_api_permissions.py

# 用户管理测试
pytest tests/test_api_users.py

# 审计日志测试
pytest tests/test_api_audit_logs.py

# 安全工具函数测试
pytest tests/test_security.py
```

### 运行特定标记的测试

```bash
# 只运行集成测试
pytest -m integration

# 只运行单元测试
pytest -m unit

# 只运行认证相关测试
pytest -m auth

# 只运行权限相关测试
pytest -m permission

# 只运行用户管理相关测试
pytest -m users

# 只运行审计日志相关测试
pytest -m audit

# 只运行安全相关测试
pytest -m security
```

### 运行特定的测试类或函数

```bash
# 运行特定的测试类
pytest tests/test_api_auth.py::TestAuthAPI

# 运行特定的测试函数
pytest tests/test_api_auth.py::TestAuthAPI::test_login_success
```

### 生成测试覆盖率报告

```bash
# 运行测试并生成覆盖率报告
pytest --cov=app --cov-report=html

# 查看HTML报告（生成在 htmlcov/ 目录）
open htmlcov/index.html  # macOS
xdg-open htmlcov/index.html  # Linux
```

### 详细输出

```bash
# 显示详细输出
pytest -v

# 显示非常详细的输出（包括所有print语句）
pytest -vv -s
```

### 只运行失败的测试

```bash
# 第一次运行
pytest

# 只重新运行失败的测试
pytest --lf
```

### 并行运行测试（更快）

```bash
# 安装pytest-xdist
pip install pytest-xdist

# 使用4个进程并行运行
pytest -n 4
```

## 测试配置

测试配置位于 `pytest.ini` 文件中，包括：

- **测试路径**: `tests/`
- **测试文件模式**: `test_*.py`
- **异步支持**: 自动启用
- **覆盖率配置**: 覆盖 `app/` 目录
- **日志配置**: 启用CLI日志输出

## Fixtures 说明

### 数据库 Fixtures

- `test_db`: 测试数据库会话（每个测试函数独立）
- `client`: HTTP测试客户端

### 用户 Fixtures

- `test_user`: 普通用户（username: testuser, password: testpass123）
- `test_admin`: 管理员用户（username: admin, password: adminpass123）
- `test_viewer`: 查看者用户（username: viewer, password: viewerpass123）

### 服务器 Fixtures

- `test_server`: 单个测试服务器
- `multiple_servers`: 5个测试服务器

### 认证 Fixtures

- `user_token`: 普通用户访问令牌
- `admin_token`: 管理员访问令牌
- `viewer_token`: 查看者访问令牌
- `auth_headers`: 普通用户认证请求头
- `admin_headers`: 管理员认证请求头
- `viewer_headers`: 查看者认证请求头

### 工具 Fixtures

- `faker_instance`: Faker实例用于生成随机数据
- `random_email`: 随机邮箱地址
- `random_username`: 随机用户名
- `random_password`: 随机密码

## 测试标记

使用 pytest 标记来组织测试：

- `@pytest.mark.unit`: 单元测试
- `@pytest.mark.integration`: 集成测试
- `@pytest.mark.auth`: 认证相关测试
- `@pytest.mark.server`: 服务器管理测试
- `@pytest.mark.metrics`: 监控指标测试
- `@pytest.mark.execute`: 命令执行测试
- `@pytest.mark.chat`: AI聊天测试
- `@pytest.mark.permission`: 权限管理测试
- `@pytest.mark.users`: 用户管理测试
- `@pytest.mark.audit`: 审计日志测试
- `@pytest.mark.security`: 安全和加密测试
- `@pytest.mark.slow`: 慢速测试（可以跳过）
- `@pytest.mark.skip_ci`: 在CI环境中跳过

## 编写新测试

### 基本测试结构

```python
import pytest
from httpx import AsyncClient

@pytest.mark.integration
@pytest.mark.your_module
class TestYourModule:
    """模块测试类"""

    async def test_something(
        self,
        client: AsyncClient,
        auth_headers: dict,
    ):
        """测试某个功能"""
        response = await client.get(
            "/api/v1/your-endpoint",
            headers=auth_headers,
        )
        assert response.status_code == 200
        data = response.json()
        assert data["key"] == "expected_value"
```

### 使用 Fixtures

```python
async def test_with_fixtures(
    client: AsyncClient,
    test_user: User,
    test_server: Server,
    auth_headers: dict,
):
    """使用多个fixtures的测试"""
    # test_user 和 test_server 已经在数据库中创建
    # auth_headers 包含有效的认证令牌
    response = await client.get(
        f"/api/v1/servers/{test_server.id}",
        headers=auth_headers,
    )
    assert response.status_code == 200
```

### 测试异常情况

```python
async def test_error_case(client: AsyncClient):
    """测试错误情况"""
    response = await client.get("/api/v1/nonexistent")
    assert response.status_code == 404

    error_data = response.json()
    assert "detail" in error_data
```

## 最佳实践

1. **每个测试应该独立**: 不要依赖其他测试的结果
2. **使用描述性的测试名称**: 测试名应该清楚地说明它在测试什么
3. **测试一个概念**: 每个测试应该只测试一个行为或场景
4. **使用 fixtures**: 重用测试数据和设置
5. **测试边界条件**: 不仅测试正常情况，也要测试边界和异常情况
6. **保持测试简洁**: 测试应该易于阅读和理解
7. **使用适当的断言**: 使用具体的断言而不是简单的 `assert True`

## 持续集成

测试可以集成到 CI/CD 流程中：

```yaml
# .github/workflows/test.yml 示例
name: Tests
on: [push, pull_request]
jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2
      - uses: actions/setup-python@v2
        with:
          python-version: '3.11'
      - run: pip install -r requirements.txt
      - run: pytest --cov=app --cov-report=xml
      - uses: codecov/codecov-action@v2
```

## 调试测试

### 进入调试器

```python
async def test_debug_example(client: AsyncClient):
    response = await client.get("/api/v1/endpoint")

    # 在这里进入调试器
    import pdb; pdb.set_trace()

    assert response.status_code == 200
```

### 使用 pytest 的调试选项

```bash
# 在第一个失败的测试处进入调试器
pytest --pdb

# 在每个测试开始时进入调试器
pytest --trace
```

## 常见问题

### Q: 测试数据库是什么？
A: 测试使用 SQLite 内存数据库，每个测试函数都有独立的数据库实例。

### Q: 如何跳过某些测试？
A: 使用 `@pytest.mark.skip` 或 `@pytest.mark.skipif`：

```python
@pytest.mark.skip(reason="暂时跳过")
async def test_something():
    pass

@pytest.mark.skipif(condition, reason="条件不满足")
async def test_conditional():
    pass
```

### Q: 如何测试需要外部服务的功能？
A: 使用 mock 或创建测试专用的 fixture：

```python
from unittest.mock import AsyncMock, patch

@patch('app.services.external_service.call_api')
async def test_with_mock(mock_call):
    mock_call.return_value = {"status": "success"}
    # 测试代码
```

## 测试覆盖率目标

- **总体覆盖率**: ≥ 80%
- **核心业务逻辑**: ≥ 90%
- **API端点**: 100%
- **工具函数**: ≥ 85%

## 相关资源

- [Pytest 文档](https://docs.pytest.org/)
- [pytest-asyncio 文档](https://pytest-asyncio.readthedocs.io/)
- [HTTPX 文档](https://www.python-httpx.org/)
- [Faker 文档](https://faker.readthedocs.io/)
