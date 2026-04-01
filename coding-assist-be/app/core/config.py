from functools import lru_cache
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = "Learning Assist Backend"
    app_version: str = "0.1.0"
    api_prefix: str = "/api/v1"
    environment: str = "dev"

    frontend_origin: str = "*"

    execution_backend: str = "judge0"
    judge_image: str = "learning-assist-judge:latest"
    execution_timeout_seconds: int = 3
    execution_memory_mb: int = 128
    docker_disabled_network: str = "none"

    openai_api_key: str = ""
    openai_base_url: str = "https://bedrock-mantle.us-east-1.api.aws/v1"
    bedrock_model_id: str = "openai.gpt-oss-120b"
    bedrock_max_tokens: int = 500
    bedrock_temperature: float = 0.2

    postgres_user: str = "postgres"
    postgres_password: str = ""
    postgres_db: str = "postgres"
    postgres_host: str = ""
    postgres_port: int = 5432
    postgres_sslmode: str = "verify-full"
    postgres_sslrootcert: str = "/certs/global-bundle.pem"
    jwt_secret: str = "learning-assist-dev-secret"
    jwt_algorithm: str = "HS256"
    jwt_expiry_hours: int = 24

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
    )


@lru_cache
def get_settings() -> Settings:
    return Settings()
