"""
日志配置
"""
import sys
from pathlib import Path

from loguru import logger

from app.config import settings

# 移除默认处理器
logger.remove()

# 添加控制台处理器
logger.add(
    sys.stderr,
    format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level: <8}</level> | <cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - <level>{message}</level>",
    level=settings.log_level,
    colorize=True,
)

# 添加文件处理器
log_path = Path(settings.log_file)
log_path.parent.mkdir(parents=True, exist_ok=True)

logger.add(
    settings.log_file,
    rotation="00:00",  # 每天午夜轮换
    retention="30 days",  # 保留30天
    compression="zip",  # 压缩旧日志
    format="{time:YYYY-MM-DD HH:mm:ss} | {level: <8} | {name}:{function}:{line} - {message}",
    level=settings.log_level,
)

# 导出logger
__all__ = ["logger"]
