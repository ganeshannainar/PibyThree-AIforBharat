from pydantic_settings import BaseSettings
from typing import Optional

class Settings(BaseSettings):

    # Database
    db_username: str
    db_password: str
    db_hostname: str
    db_port: str
    db_name: str

    # JWT
    secret_key: str
    algorithm: str
    access_token_expire_minutes: int

    # Langfuse
    LANGFUSE_SECRET_KEY: Optional[str] = None
    LANGFUSE_PUBLIC_KEY: Optional[str] = None
    LANGFUSE_BASE_URL: Optional[str] = None

    # AI APIs
    GOOGLE_API_KEY: Optional[str] = None
    ANTHROPIC_API_KEY: Optional[str] = None
    SERP_API_KEY: Optional[str] = None

    # Langchain
    langchain_tracing_v2: Optional[str] = None
    langchain_api_key: Optional[str] = None

    # AWS
    aws_access_key_id: str
    aws_secret_access_key: str
    aws_region: str

    # LLM
    llm_model_id: str

    class Config:
        env_file = ".env"

settings = Settings()