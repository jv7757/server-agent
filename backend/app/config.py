"""
应用配置管理
"""
from functools import lru_cache
from typing import List, Literal

from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """应用配置类"""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # 应用配置
    app_name: str = "Server Management System"
    app_version: str = "1.0.0"
    debug: bool = False
    env: Literal["development", "production", "test"] = "development"

    # 数据库配置
    database_type: Literal["postgresql", "mysql"] = "postgresql"
    database_url: str
    redis_url: str = "redis://localhost:6379/0"

    # JWT配置
    secret_key: str
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 60
    refresh_token_expire_days: int = 7

    # SSH密钥加密
    encryption_key: str

    # AI配置
    ai_provider: Literal["openai", "claude", "ollama"] = "openai"
    ai_model: str = "gpt-4"
    openai_api_key: str | None = None
    anthropic_api_key: str | None = None
    ollama_base_url: str = "http://localhost:11434"

    # Celery配置
    celery_broker_url: str = "redis://localhost:6379/1"
    celery_result_backend: str = "redis://localhost:6379/2"

    # CORS配置
    allowed_origins: str = "http://localhost:5173"

    @field_validator("allowed_origins")
    @classmethod
    def parse_origins(cls, v: str) -> List[str]:
        """解析允许的源"""
        return [origin.strip() for origin in v.split(",")]

    # 邮件配置
    smtp_host: str | None = None
    smtp_port: int = 587
    smtp_user: str | None = None
    smtp_password: str | None = None
    smtp_from: str | None = None

    # 日志配置
    log_level: str = "INFO"
    log_file: str = "logs/app.log"

    # 监控配置
    metrics_collection_interval: int = 60  # 秒
    metrics_retention_days: int = 30

    # 安全配置
    password_min_length: int = 8
    login_attempt_limit: int = 5
    login_lockout_duration: int = 600  # 秒
    command_execution_timeout: int = 30  # 秒

    # 分页配置
    default_page_size: int = 20
    max_page_size: int = 100

    @property
    def is_production(self) -> bool:
        """是否为生产环境"""
        return self.env == "production"

    @property
    def is_development(self) -> bool:
        """是否为开发环境"""
        return self.env == "development"


@lru_cache()
def get_settings() -> Settings:
    """获取配置单例"""
    return Settings()


# 导出配置实例
settings = get_settings()
