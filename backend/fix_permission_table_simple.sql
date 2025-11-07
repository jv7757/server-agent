-- 完整修复脚本：删除旧字段并添加新字段
-- 适用于 MySQL 5.7.6+

-- 步骤 1: 删除旧的 permission 字段（如果存在）
ALTER TABLE user_server_permissions DROP COLUMN IF EXISTS permission;

-- 步骤 2: 添加新的权限列（如果列已存在会报错但不影响）
ALTER TABLE user_server_permissions ADD COLUMN can_read TINYINT(1) NOT NULL DEFAULT 0;
ALTER TABLE user_server_permissions ADD COLUMN can_write TINYINT(1) NOT NULL DEFAULT 0;
ALTER TABLE user_server_permissions ADD COLUMN can_execute TINYINT(1) NOT NULL DEFAULT 0;
ALTER TABLE user_server_permissions ADD COLUMN can_admin TINYINT(1) NOT NULL DEFAULT 0;

-- 添加授权人列
ALTER TABLE user_server_permissions ADD COLUMN granted_by CHAR(36) NULL;

-- 添加外键约束（如果需要）
ALTER TABLE user_server_permissions
ADD CONSTRAINT fk_granted_by
FOREIGN KEY (granted_by) REFERENCES users(id);

-- 显示表结构
DESCRIBE user_server_permissions;
