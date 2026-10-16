"""Application configuration.

Every setting is read from the environment at startup (12-factor principle III).
The same image therefore runs unchanged on a laptop, in docker compose, and in
Kubernetes -- only the environment differs.
"""
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    # Default points at the docker-compose service name so the container works
    # with no extra configuration. Overridden everywhere else.
    database_url: str = "postgresql+psycopg://taskr:taskr@db:5432/taskr"

    # Comma-separated list of origins the browser is allowed to call us from.
    cors_origins: str = "http://localhost:3000,http://localhost:5173"

    app_name: str = "Taskr API"
    environment: str = "development"

    @property
    def cors_origin_list(self) -> list[str]:
        return [o.strip() for o in self.cors_origins.split(",") if o.strip()]


settings = Settings()
