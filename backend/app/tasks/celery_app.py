"""
Celery应用配置
"""
from celery import Celery
from celery.schedules import crontab

from app.config import settings

# 创建Celery应用
celery_app = Celery(
    "server_agent",
    broker=settings.celery_broker_url,
    backend=settings.celery_result_backend,
    include=["app.tasks.monitor_tasks"],
)

# 配置Celery
celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
    task_track_started=True,
    task_time_limit=300,  # 5分钟超时
    task_soft_time_limit=240,  # 4分钟软超时
    worker_prefetch_multiplier=1,
    worker_max_tasks_per_child=1000,
)

# 配置定时任务
celery_app.conf.beat_schedule = {
    # 每分钟采集一次服务器指标
    "collect-all-servers-metrics": {
        "task": "app.tasks.monitor_tasks.collect_all_servers_metrics",
        "schedule": settings.metrics_collection_interval,  # 从配置读取，默认60秒
    },
    # 每天凌晨清理旧数据
    "cleanup-old-metrics": {
        "task": "app.tasks.monitor_tasks.cleanup_old_metrics",
        "schedule": crontab(hour=2, minute=0),  # 每天凌晨2点
    },
}
