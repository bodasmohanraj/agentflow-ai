from typing import Literal

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=True,
        extra="ignore",
    )

    PROJECT_NAME: str = "AgentFlow AI"
    API_V1_STR: str = "/api/v1"
    ENVIRONMENT: str = "development"
    CORS_ORIGINS: str = ""

    SECRET_KEY: str
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24 * 7

    DATABASE_URL: str

    FREELLMAPI_BASE_URL: str = ""
    FREELLMAPI_API_KEY: str = ""
    FREELLMAPI_MODEL: str = "gpt-3.5-turbo"
    FREELLMAPI_TEMPERATURE: float = 0.7
    FREELLMAPI_MAX_TOKENS: int = 1000
    WORKFLOW_AI_MODE: Literal["live", "mock"] = "live"

    @property
    def allowed_origins(self) -> list[str]:
        origins = [origin.strip().rstrip("/") for origin in self.CORS_ORIGINS.split(",") if origin.strip()]
        if self.ENVIRONMENT.lower() == "production" and "*" in origins:
            raise ValueError("CORS_ORIGINS must list explicit origins in production")
        if origins:
            return origins
        if self.ENVIRONMENT.lower() != "production":
            return ["http://localhost:3000", "http://localhost:3001", "http://127.0.0.1:3000", "http://127.0.0.1:3001"]
        return []


settings = Settings()
