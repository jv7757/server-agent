"""
测试Redis配置
"""
import sys
import os

# 添加项目路径
sys.path.insert(0, os.path.dirname(__file__))

from app.config import settings

print("=" * 60)
print("Redis配置测试")
print("=" * 60)
print(f"Redis Host: {settings.redis_host}")
print(f"Redis Port: {settings.redis_port}")
print(f"Redis Password: {'***' if settings.redis_password else '(未设置)'}")
print(f"Redis DB: {settings.redis_db}")
print(f"Celery Broker DB: {settings.redis_celery_broker_db}")
print(f"Celery Result DB: {settings.redis_celery_result_db}")
print("=" * 60)
print("构建的URL:")
print(f"Redis URL: {settings.redis_url}")
print(f"Celery Broker URL: {settings.celery_broker_url}")
print(f"Celery Result Backend URL: {settings.celery_result_backend}")
print("=" * 60)

# 测试Redis连接
try:
    import redis
    print("\n测试Redis连接...")
    r = redis.from_url(settings.redis_url)
    r.ping()
    print("✅ Redis连接成功!")

    # 测试Celery broker连接
    r_broker = redis.from_url(settings.celery_broker_url)
    r_broker.ping()
    print("✅ Celery Broker连接成功!")

    # 测试Celery result backend连接
    r_result = redis.from_url(settings.celery_result_backend)
    r_result.ping()
    print("✅ Celery Result Backend连接成功!")

except Exception as e:
    print(f"❌ Redis连接失败: {e}")
    sys.exit(1)

print("\n所有配置测试通过!")
