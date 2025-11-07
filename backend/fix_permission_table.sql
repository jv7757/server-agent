-- 修复 user_server_permissions 表结构
-- 添加缺失的权限列

-- 检查并添加 can_read 列
SET @column_exists = (
    SELECT COUNT(*)
    FROM information_schema.columns
    WHERE table_schema = DATABASE()
    AND table_name = 'user_server_permissions'
    AND column_name = 'can_read'
);

SET @add_can_read = IF(@column_exists = 0,
    'ALTER TABLE user_server_permissions ADD COLUMN can_read TINYINT(1) NOT NULL DEFAULT 0',
    'SELECT "Column can_read already exists" AS message'
);

PREPARE stmt FROM @add_can_read;
EXECUTE stmt;
DEALLOCATE PREPARE stmt;

-- 检查并添加 can_write 列
SET @column_exists = (
    SELECT COUNT(*)
    FROM information_schema.columns
    WHERE table_schema = DATABASE()
    AND table_name = 'user_server_permissions'
    AND column_name = 'can_write'
);

SET @add_can_write = IF(@column_exists = 0,
    'ALTER TABLE user_server_permissions ADD COLUMN can_write TINYINT(1) NOT NULL DEFAULT 0',
    'SELECT "Column can_write already exists" AS message'
);

PREPARE stmt FROM @add_can_write;
EXECUTE stmt;
DEALLOCATE PREPARE stmt;

-- 检查并添加 can_execute 列
SET @column_exists = (
    SELECT COUNT(*)
    FROM information_schema.columns
    WHERE table_schema = DATABASE()
    AND table_name = 'user_server_permissions'
    AND column_name = 'can_execute'
);

SET @add_can_execute = IF(@column_exists = 0,
    'ALTER TABLE user_server_permissions ADD COLUMN can_execute TINYINT(1) NOT NULL DEFAULT 0',
    'SELECT "Column can_execute already exists" AS message'
);

PREPARE stmt FROM @add_can_execute;
EXECUTE stmt;
DEALLOCATE PREPARE stmt;

-- 检查并添加 can_admin 列
SET @column_exists = (
    SELECT COUNT(*)
    FROM information_schema.columns
    WHERE table_schema = DATABASE()
    AND table_name = 'user_server_permissions'
    AND column_name = 'can_admin'
);

SET @add_can_admin = IF(@column_exists = 0,
    'ALTER TABLE user_server_permissions ADD COLUMN can_admin TINYINT(1) NOT NULL DEFAULT 0',
    'SELECT "Column can_admin already exists" AS message'
);

PREPARE stmt FROM @add_can_admin;
EXECUTE stmt;
DEALLOCATE PREPARE stmt;

-- 检查并添加 granted_by 列
SET @column_exists = (
    SELECT COUNT(*)
    FROM information_schema.columns
    WHERE table_schema = DATABASE()
    AND table_name = 'user_server_permissions'
    AND column_name = 'granted_by'
);

SET @add_granted_by = IF(@column_exists = 0,
    'ALTER TABLE user_server_permissions ADD COLUMN granted_by CHAR(36) NULL',
    'SELECT "Column granted_by already exists" AS message'
);

PREPARE stmt FROM @add_granted_by;
EXECUTE stmt;
DEALLOCATE PREPARE stmt;

-- 显示最终的表结构
SELECT 'Fixed table structure' AS status;
DESCRIBE user_server_permissions;
