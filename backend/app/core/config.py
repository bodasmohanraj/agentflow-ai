from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    PROJECT_NAME: str = "AgentFlow AI"
    API_V1_STR: str = "/api/v1"
    SECRET_KEY: str = "secret-key-change-in-production-12345"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24 * 7  # 7 days
    
    # Database
    DATABASE_URL: str = "sqlite:///./agentflow.db"

    class Config:
        case_sensitive = True

settings = Settings()
