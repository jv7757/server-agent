# 修复权限表结构问题

## 问题描述

错误信息：
```
Unknown column 'user_server_permissions.can_read' in 'field list'
```

这表示数据库中的 `user_server_permissions` 表缺少必需的权限列。

## 原因

数据库表结构与当前代码模型不一致，可能是因为：
1. 数据库是从旧版本升级的
2. 数据库迁移没有完全执行
3. 表结构是手动创建的

## 解决方案

### 方案 1: 使用 SQL 脚本修复（推荐）

1. **连接到你的 MySQL 数据库**：
   ```bash
   mysql -u your_username -p your_database_name
   ```

2. **执行简单修复脚本**：
   ```sql
   -- 切换到正确的数据库
   USE your_database_name;

   -- 添加缺失的列
   ALTER TABLE user_server_permissions ADD COLUMN can_read TINYINT(1) NOT NULL DEFAULT 0;
   ALTER TABLE user_server_permissions ADD COLUMN can_write TINYINT(1) NOT NULL DEFAULT 0;
   ALTER TABLE user_server_permissions ADD COLUMN can_execute TINYINT(1) NOT NULL DEFAULT 0;
   ALTER TABLE user_server_permissions ADD COLUMN can_admin TINYINT(1) NOT NULL DEFAULT 0;
   ALTER TABLE user_server_permissions ADD COLUMN granted_by CHAR(36) NULL;

   -- 验证表结构
   DESCRIBE user_server_permissions;
   ```

   **注意**：如果某些列已经存在，会报错但不影响其他列的添加。

3. **或者使用提供的 SQL 文件**：
   ```bash
   mysql -u your_username -p your_database_name < fix_permission_table_simple.sql
   ```

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

- `fix_permission_table.py` - Python 自动修复脚本
- `fix_permission_table.sql` - SQL 完整修复脚本（带检查）
- `fix_permission_table_simple.sql` - SQL 简单修复脚本（直接添加）
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
