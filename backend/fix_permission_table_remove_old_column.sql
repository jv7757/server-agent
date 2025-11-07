-- 修复 user_server_permissions 表 - 删除旧的 permission 字段
-- 这个字段是旧版本的设计，已被 can_read, can_write, can_execute, can_admin 替代

-- 检查是否存在 permission 字段
SELECT COLUMN_NAME, COLUMN_TYPE, IS_NULLABLE, COLUMN_DEFAULT
FROM information_schema.columns
WHERE table_schema = DATABASE()
AND table_name = 'user_server_permissions'
AND column_name = 'permission';

-- 如果存在，删除它
ALTER TABLE user_server_permissions DROP COLUMN IF EXISTS permission;

-- 验证表结构
DESCRIBE user_server_permissions;

-- 显示最终的列
SELECT COLUMN_NAME, COLUMN_TYPE, IS_NULLABLE, COLUMN_DEFAULT
FROM information_schema.columns
WHERE table_schema = DATABASE()
AND table_name = 'user_server_permissions'
ORDER BY ORDINAL_POSITION;
