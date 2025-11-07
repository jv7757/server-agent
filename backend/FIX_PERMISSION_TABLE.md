# 修复权限表结构问题

## 问题描述

### 问题 1: 缺少权限列

错误信息：
```
Unknown column 'user_server_permissions.can_read' in 'field list'
```

这表示数据库中的 `user_server_permissions` 表缺少必需的权限列。

### 问题 2: 存在旧的 permission 字段

错误信息：
```
Field 'permission' doesn't have a default value
```

这表示数据库表中存在一个旧的 `permission` 字段（单数形式），该字段是旧版本的设计，应该被删除。新版本使用 `can_read`, `can_write`, `can_execute`, `can_admin` 四个字段替代。

## 原因

数据库表结构与当前代码模型不一致，可能是因为：
1. 数据库是从旧版本升级的
2. 数据库迁移没有完全执行
3. 表结构是手动创建的

## 解决方案

### 完整修复步骤（推荐按顺序执行）

#### 步骤 1: 删除旧的 permission 字段

```bash
# 连接到你的 MySQL 数据库
mysql -u your_username -p your_database_name

# 执行删除旧字段
ALTER TABLE user_server_permissions DROP COLUMN IF EXISTS permission;
```

或使用提供的脚本：
```bash
mysql -u your_username -p your_database_name < fix_permission_table_remove_old_column.sql
```

#### 步骤 2: 添加新的权限字段

```sql
-- 添加缺失的列
ALTER TABLE user_server_permissions ADD COLUMN IF NOT EXISTS can_read TINYINT(1) NOT NULL DEFAULT 0;
ALTER TABLE user_server_permissions ADD COLUMN IF NOT EXISTS can_write TINYINT(1) NOT NULL DEFAULT 0;
ALTER TABLE user_server_permissions ADD COLUMN IF NOT EXISTS can_execute TINYINT(1) NOT NULL DEFAULT 0;
ALTER TABLE user_server_permissions ADD COLUMN IF NOT EXISTS can_admin TINYINT(1) NOT NULL DEFAULT 0;
ALTER TABLE user_server_permissions ADD COLUMN IF NOT EXISTS granted_by CHAR(36) NULL;

-- 验证表结构
DESCRIBE user_server_permissions;
```

或使用提供的脚本：
```bash
mysql -u your_username -p your_database_name < fix_permission_table_simple.sql
```

### 快速一键修复（所有问题）

```bash
# 连接数据库
mysql -u your_username -p your_database_name

# 执行修复（复制粘贴所有命令）
USE your_database_name;

-- 1. 删除旧字段
ALTER TABLE user_server_permissions DROP COLUMN IF EXISTS permission;

-- 2. 添加新字段（忽略已存在的错误）
ALTER TABLE user_server_permissions ADD COLUMN can_read TINYINT(1) NOT NULL DEFAULT 0;
ALTER TABLE user_server_permissions ADD COLUMN can_write TINYINT(1) NOT NULL DEFAULT 0;
ALTER TABLE user_server_permissions ADD COLUMN can_execute TINYINT(1) NOT NULL DEFAULT 0;
ALTER TABLE user_server_permissions ADD COLUMN can_admin TINYINT(1) NOT NULL DEFAULT 0;
ALTER TABLE user_server_permissions ADD COLUMN granted_by CHAR(36) NULL;

-- 3. 验证
DESCRIBE user_server_permissions;
```

**注意**：
- `DROP COLUMN IF EXISTS` 在 MySQL 5.7.6+ 支持
- 添加列时如果已存在会报错，可以忽略
- 对于 MySQL 5.6，需要先检查列是否存在

### 方案 2: 使用 Python 脚本修复

如果你在开发环境中，可以使用 Python 脚本：

```bash
cd backend
python fix_permission_table.py
```

### 方案 3: 重建数据库（适用于开发环境）

**警告**：这将删除所有数据！

```bash
cd backend

# 删除数据库
mysql -u your_username -p -e "DROP DATABASE IF EXISTS your_database_name; CREATE DATABASE your_database_name;"

# 运行迁移
alembic upgrade head

# 或使用 Python 脚本初始化
python -c "from app.database import init_db; import asyncio; asyncio.run(init_db())"
```

## 验证修复

修复后，检查表结构应该包含以下列：

```sql
DESCRIBE user_server_permissions;
```

应该看到：
- id (主键)
- user_id (外键)
- server_id (外键)
- can_read (TINYINT)
- can_write (TINYINT)
- can_execute (TINYINT)
- can_admin (TINYINT)
- created_at (DATETIME)
- granted_by (CHAR(36), 可为空)

## 预防措施

为了避免将来出现类似问题：

1. **始终使用数据库迁移**：
   ```bash
   alembic upgrade head
   ```

2. **在生产环境部署前备份数据库**：
   ```bash
   mysqldump -u username -p database_name > backup.sql
   ```

3. **测试迁移脚本**：
   在开发或测试环境先运行迁移，确认无误后再在生产环境执行。

## 相关文件

- `FIX_PERMISSION_TABLE.md` - 本文档（完整修复指南）
- `fix_permission_table_remove_old_column.sql` - 删除旧 permission 字段
- `fix_permission_table_simple.sql` - 完整修复脚本（删除旧字段+添加新字段）
- `fix_permission_table.sql` - SQL 完整修复脚本（带检查，安全版本）
- `fix_permission_table.py` - Python 自动修复脚本
- `app/models/permission.py` - 权限模型定义
- `alembic/versions/20251105_000001_initial_migration.py` - 初始迁移文件

## 故障排查

### 问题：列已存在
如果某些列已经存在，会看到：
```
ERROR 1060 (42S21): Duplicate column name 'can_read'
```
这是正常的，可以忽略，继续添加其他缺失的列。

### 问题：外键约束失败
如果添加 `granted_by` 外键时失败：
```sql
-- 先不添加外键约束，只添加列
ALTER TABLE user_server_permissions ADD COLUMN granted_by CHAR(36) NULL;
```

### 问题：权限表不存在
如果表本身不存在：
```bash
# 运行完整的数据库初始化
cd backend
alembic upgrade head
```

## 联系支持

如果问题仍然存在，请提供：
1. 数据库类型和版本
2. 完整的错误信息
3. `DESCRIBE user_server_permissions;` 的输出
