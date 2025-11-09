# 代码质量工具指南

本项目配置了完整的代码质量检查工具，包括代码格式化、静态分析和自动化 hooks。

## 📋 目录

- [工具概览](#工具概览)
- [快速开始](#快速开始)
- [后端工具](#后端工具)
- [前端工具](#前端工具)
- [Pre-commit Hooks](#pre-commit-hooks)
- [CI/CD 集成](#cicd-集成)
- [常见问题](#常见问题)

---

## 工具概览

### 后端 (Python)

| 工具 | 用途 | 配置文件 |
|------|------|---------|
| **Black** | 代码格式化 | `backend/pyproject.toml` |
| **Flake8** | 代码检查 (PEP 8) | `backend/.flake8` |
| **isort** | import 语句排序 | `backend/pyproject.toml` |
| **mypy** | 类型检查 | `backend/pyproject.toml` |
| **pytest** | 单元测试 | `backend/pyproject.toml` |

### 前端 (Vue/TypeScript)

| 工具 | 用途 | 配置文件 |
|------|------|---------|
| **ESLint** | 代码检查 | `frontend/.eslintrc.cjs` |
| **Prettier** | 代码格式化 | `frontend/.prettierrc.json` |
| **TypeScript** | 类型检查 | `frontend/tsconfig.json` |

---

## 快速开始

### 1. 安装依赖

#### 后端依赖
```bash
cd backend
pip install -r requirements.txt
```

#### 前端依赖
```bash
cd frontend
npm install
```

### 2. 安装 Pre-commit Hooks

从项目根目录运行：

```bash
make install-hooks
# 或者
pip install pre-commit
pre-commit install
```

### 3. 运行代码检查

```bash
# 检查所有代码
make lint

# 仅检查后端
make lint-backend

# 仅检查前端
make lint-frontend
```

### 4. 格式化代码

```bash
# 格式化所有代码
make format

# 仅格式化后端
make format-backend

# 仅格式化前端
make format-frontend
```

---

## 后端工具

### Black - 代码格式化

Black 是一个固执的 Python 代码格式化工具，确保代码风格一致。

**手动运行:**
```bash
cd backend

# 检查代码格式
black --check app/ tests/

# 格式化代码
black app/ tests/

# 格式化单个文件
black app/main.py
```

**配置:** `backend/pyproject.toml`
- 行长度: 100 字符
- 目标 Python 版本: 3.10, 3.11
- 排除: alembic/versions

### Flake8 - 代码检查

Flake8 检查代码是否符合 PEP 8 规范和常见错误。

**手动运行:**
```bash
cd backend

# 检查所有代码
flake8 app/ tests/

# 检查单个文件
flake8 app/main.py

# 显示统计信息
flake8 app/ --statistics
```

**配置:** `backend/.flake8`
- 最大行长度: 100 字符
- 忽略与 Black 冲突的规则 (E203, E501, W503)
- 最大复杂度: 10

### isort - Import 排序

isort 自动排序和格式化 Python import 语句。

**手动运行:**
```bash
cd backend

# 检查 import 顺序
isort --check-only app/ tests/

# 排序 import
isort app/ tests/

# 显示差异而不修改
isort --diff app/
```

**配置:** `backend/pyproject.toml`
- 使用 Black 兼容配置
- 行长度: 100 字符

### mypy - 类型检查

mypy 进行静态类型检查。

**手动运行:**
```bash
cd backend

# 检查类型
mypy app/

# 检查特定模块
mypy app/api/

# 生成报告
mypy app/ --html-report ./mypy-report
```

**配置:** `backend/pyproject.toml`
- 目标版本: Python 3.10
- 忽略第三方库的类型错误

---

## 前端工具

### ESLint - 代码检查

ESLint 检查 JavaScript/TypeScript/Vue 代码质量和风格。

**手动运行:**
```bash
cd frontend

# 检查代码
npm run lint:check

# 自动修复问题
npm run lint

# 检查特定文件
npx eslint src/views/Login.vue
```

**配置:** `frontend/.eslintrc.cjs`
- 基于 Vue 3 推荐配置
- TypeScript 支持
- Prettier 集成

**主要规则:**
- Vue 组件命名: PascalCase
- 未使用的变量: 错误
- console.log: 开发环境允许，生产环境警告
- 要求显式 emits

### Prettier - 代码格式化

Prettier 格式化 Vue/TS/JS/CSS 代码。

**手动运行:**
```bash
cd frontend

# 检查格式
npm run format:check

# 格式化代码
npm run format

# 格式化特定文件
npx prettier --write src/views/Login.vue
```

**配置:** `frontend/.prettierrc.json`
- 单引号
- 无分号
- 行宽: 100 字符
- 2 空格缩进
- 尾随逗号: ES5

### TypeScript 类型检查

**手动运行:**
```bash
cd frontend

# 类型检查
npm run type-check

# 构建时也会进行类型检查
npm run build
```

### 完整检查

运行所有前端检查：
```bash
cd frontend
npm run code-check
```

这会依次运行:
1. ESLint 检查
2. Prettier 格式检查
3. TypeScript 类型检查

---

## Pre-commit Hooks

Pre-commit hooks 在每次 git commit 前自动运行代码检查，防止低质量代码提交。

### 安装

```bash
# 使用 Makefile
make install-hooks

# 或手动安装
pip install pre-commit
pre-commit install
```

### 配置

**文件:** `.pre-commit-config.yaml`

包含的检查:
- ✅ 尾随空格检查
- ✅ 文件末尾换行
- ✅ YAML/JSON 语法检查
- ✅ 大文件检查 (>1MB)
- ✅ 合并冲突标记检查
- ✅ Python debug 语句检查
- ✅ Black 格式化
- ✅ isort import 排序
- ✅ Flake8 代码检查
- ✅ Prettier 前端格式化
- ✅ ESLint 前端检查

### 使用

**正常提交** (会自动运行 hooks):
```bash
git add .
git commit -m "Your message"
# hooks 会自动运行并格式化代码
```

**跳过 hooks** (不推荐):
```bash
git commit --no-verify -m "Your message"
```

**手动运行所有 hooks**:
```bash
pre-commit run --all-files
```

**更新 hooks**:
```bash
pre-commit autoupdate
```

---

## CI/CD 集成

### GitHub Actions 示例

创建 `.github/workflows/code-quality.yml`:

```yaml
name: Code Quality

on: [push, pull_request]

jobs:
  backend-lint:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - uses: actions/setup-python@v4
        with:
          python-version: '3.10'
      - name: Install dependencies
        run: |
          cd backend
          pip install -r requirements.txt
      - name: Run Black
        run: cd backend && black --check app/ tests/
      - name: Run Flake8
        run: cd backend && flake8 app/ tests/
      - name: Run isort
        run: cd backend && isort --check-only app/ tests/

  frontend-lint:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - uses: actions/setup-node@v3
        with:
          node-version: '18'
      - name: Install dependencies
        run: cd frontend && npm ci
      - name: Run ESLint
        run: cd frontend && npm run lint:check
      - name: Run Prettier
        run: cd frontend && npm run format:check
      - name: Type check
        run: cd frontend && npm run type-check
```

---

## 开发工作流

### 推荐的开发流程

1. **开始开发**
   ```bash
   git checkout -b feature/new-feature
   ```

2. **编写代码** (IDE 可以实时提示)

3. **在提交前运行检查**
   ```bash
   # 快速检查
   make lint

   # 或自动修复
   make format
   ```

4. **提交代码** (pre-commit hooks 自动运行)
   ```bash
   git add .
   git commit -m "feat: add new feature"
   ```

5. **如果 hooks 失败**
   - 查看错误信息
   - 修复问题或运行 `make format`
   - 重新提交

### IDE 集成

#### VSCode

**安装插件:**
- Python (Microsoft)
- Pylance
- Black Formatter
- Flake8
- ESLint
- Prettier
- Vue - Official (Volar)

**设置 (.vscode/settings.json):**
```json
{
  "python.formatting.provider": "black",
  "python.linting.flake8Enabled": true,
  "python.linting.enabled": true,
  "editor.formatOnSave": true,
  "editor.codeActionsOnSave": {
    "source.organizeImports": true
  },
  "[python]": {
    "editor.defaultFormatter": "ms-python.black-formatter"
  },
  "[vue]": {
    "editor.defaultFormatter": "esbenp.prettier-vscode"
  },
  "[typescript]": {
    "editor.defaultFormatter": "esbenp.prettier-vscode"
  }
}
```

#### PyCharm / WebStorm

1. **配置 Black:**
   - Settings → Tools → Black
   - 启用 "On save"

2. **配置 Flake8:**
   - Settings → Tools → External Tools
   - 添加 Flake8

3. **配置 ESLint/Prettier:**
   - Settings → Languages & Frameworks → JavaScript → Prettier
   - 启用 "On save"

---

## 常见问题

### Q: Black 和 Flake8 冲突怎么办？

A: `.flake8` 配置已经忽略了与 Black 冲突的规则 (E203, E501, W503)。如果还有问题，检查配置文件。

### Q: 如何忽略特定的警告？

**后端 (Flake8):**
```python
# 忽略整个文件
# flake8: noqa

# 忽略特定行
result = some_function()  # noqa: E501

# 忽略特定规则
result = some_function()  # noqa: F401
```

**前端 (ESLint):**
```typescript
// 忽略下一行
// eslint-disable-next-line @typescript-eslint/no-explicit-any
const data: any = {}

// 忽略整个文件
/* eslint-disable */
```

### Q: Pre-commit hooks 太慢怎么办？

A: 可以只在特定文件上运行：
```bash
# 只检查暂存的文件
pre-commit run

# 跳过 hooks (不推荐)
git commit --no-verify
```

### Q: 如何更新代码风格规则？

1. 修改对应的配置文件
2. 运行 `make format` 应用新规则
3. 提交配置更改

### Q: 团队成员不想用 pre-commit 怎么办？

A: Pre-commit 是可选的，但强烈推荐。可以：
1. 在 CI 中强制运行检查
2. 在 PR review 时要求通过检查
3. 使用 `make lint` 手动检查

---

## 附录

### 完整命令清单

```bash
# Makefile 命令
make help              # 显示帮助
make install-hooks     # 安装 pre-commit hooks
make lint             # 检查所有代码
make lint-backend     # 检查后端
make lint-frontend    # 检查前端
make format           # 格式化所有代码
make format-backend   # 格式化后端
make format-frontend  # 格式化前端
make test-backend     # 运行后端测试
make clean            # 清理缓存文件

# 后端命令
cd backend
black app/ tests/                    # 格式化
flake8 app/ tests/                   # 检查
isort app/ tests/                    # 排序 imports
mypy app/                            # 类型检查
pytest                               # 运行测试

# 前端命令
cd frontend
npm run lint                         # 检查并修复
npm run lint:check                   # 仅检查
npm run format                       # 格式化
npm run format:check                 # 检查格式
npm run type-check                   # 类型检查
npm run code-check                   # 完整检查

# Pre-commit 命令
pre-commit install                   # 安装
pre-commit run                       # 运行 (仅暂存文件)
pre-commit run --all-files          # 运行 (所有文件)
pre-commit autoupdate               # 更新 hooks
pre-commit uninstall                # 卸载
```

### 相关资源

- [Black 文档](https://black.readthedocs.io/)
- [Flake8 文档](https://flake8.pycqa.org/)
- [isort 文档](https://pycqa.github.io/isort/)
- [mypy 文档](https://mypy.readthedocs.io/)
- [ESLint 文档](https://eslint.org/)
- [Prettier 文档](https://prettier.io/)
- [Pre-commit 文档](https://pre-commit.com/)

---

## 总结

代码质量工具的目标是:
- ✅ 保持代码风格一致
- ✅ 及早发现潜在问题
- ✅ 提高代码可读性
- ✅ 减少 code review 时间
- ✅ 防止低质量代码进入代码库

**建议所有开发者:**
1. 安装 pre-commit hooks
2. 在 IDE 中配置自动格式化
3. 提交前运行 `make lint`
4. 保持配置文件更新

有问题请参考本文档或提交 Issue！
