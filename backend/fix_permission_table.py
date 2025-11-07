"""
修复权限表结构

检查并修复 user_server_permissions 表，确保包含所有必需的列
"""
import asyncio
import sys
from sqlalchemy import text
from app.database import engine
from app.config import settings

async def check_and_fix_permission_table():
    """检查并修复权限表结构"""

    async with engine.begin() as conn:
        # 检查数据库类型
        is_mysql = 'mysql' in settings.database_url.lower()
        is_postgres = 'postgres' in settings.database_url.lower()

        print(f"数据库类型: {'MySQL' if is_mysql else 'PostgreSQL' if is_postgres else 'Unknown'}")

        # 检查表是否存在
        if is_mysql:
            result = await conn.execute(text("""
                SELECT COUNT(*)
                FROM information_schema.tables
                WHERE table_schema = DATABASE()
                AND table_name = 'user_server_permissions'
            """))
        else:
            result = await conn.execute(text("""
                SELECT COUNT(*)
                FROM information_schema.tables
                WHERE table_schema = 'public'
                AND table_name = 'user_server_permissions'
            """))

        table_exists = result.scalar() > 0
        print(f"表 user_server_permissions 存在: {table_exists}")

        if not table_exists:
            print("表不存在，需要运行数据库迁移")
            return

        # 检查列是否存在
        if is_mysql:
            result = await conn.execute(text("""
                SELECT COLUMN_NAME
                FROM information_schema.columns
                WHERE table_schema = DATABASE()
                AND table_name = 'user_server_permissions'
            """))
        else:
            result = await conn.execute(text("""
                SELECT column_name
                FROM information_schema.columns
                WHERE table_schema = 'public'
                AND table_name = 'user_server_permissions'
            """))

        existing_columns = {row[0] for row in result}
        print(f"现有列: {existing_columns}")

        required_columns = {
            'id', 'user_id', 'server_id',
            'can_read', 'can_write', 'can_execute', 'can_admin',
            'created_at', 'granted_by'
        }

        missing_columns = required_columns - existing_columns

        if not missing_columns:
            print("✅ 所有必需的列都存在")
            return

        print(f"❌ 缺少列: {missing_columns}")

        # 添加缺少的列
        for column in missing_columns:
            if column in ['can_read', 'can_write', 'can_execute', 'can_admin']:
                print(f"添加列: {column}")
                if is_mysql:
                    await conn.execute(text(f"""
                        ALTER TABLE user_server_permissions
                        ADD COLUMN {column} TINYINT(1) NOT NULL DEFAULT 0
                    """))
                else:
                    await conn.execute(text(f"""
                        ALTER TABLE user_server_permissions
                        ADD COLUMN {column} BOOLEAN NOT NULL DEFAULT FALSE
                    """))
            elif column == 'granted_by':
                print(f"添加列: {column}")
                if is_mysql:
                    await conn.execute(text("""
                        ALTER TABLE user_server_permissions
                        ADD COLUMN granted_by CHAR(36) NULL
                    """))
                else:
                    await conn.execute(text("""
                        ALTER TABLE user_server_permissions
                        ADD COLUMN granted_by UUID NULL
                    """))

        print("✅ 表结构修复完成")

if __name__ == '__main__':
    try:
        asyncio.run(check_and_fix_permission_table())
        print("\n修复成功！")
    except Exception as e:
        print(f"\n修复失败: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
