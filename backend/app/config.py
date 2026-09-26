import os
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    # Postgres
    POSTGRES_USER: str = "jobpilot"
    POSTGRES_PASSWORD: str = "jobpilot-local"
    POSTGRES_DB: str = "jobpilot"
    DATABASE_URL: str = "postgresql+psycopg://jobpilot:jobpilot-local@postgres:5432/jobpilot"

    # Redis
    REDIS_URL: str = "redis://redis:6379/0"

    # Kafka
    KAFKA_BOOTSTRAP_SERVERS: str = "kafka:9092"

    # Anthropic
    ANTHROPIC_API_KEY: str = ""

    # Jina
    JINA_API_KEY: str = ""

    # LangFuse
    LANGFUSE_PUBLIC_KEY: str = ""
    LANGFUSE_SECRET_KEY: str = ""
    LANGFUSE_HOST: str = "https://cloud.langfuse.com"

    # Celery
    CELERY_BROKER_URL: str = "redis://redis:6379/1"
    CELERY_RESULT_BACKEND: str = "redis://redis:6379/2"

    # App
    SECRET_KEY: str = "change-me-before-deploy"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30

    class Config:
        env_file = ".env"
        extra = "ignore"


settings = Settings()

# Celery config (loaded via config_from_object)
broker_url = settings.CELERY_BROKER_URL
result_backend = settings.CELERY_RESULT_BACKEND
timezone = "UTC"
enable_utc = True
task_serializer = "json"
result_serializer = "json"
accept_content = ["json"]
task_track_started = True
task_time_limit = 30 * 60
task_soft_time_limit = 25 * 60
