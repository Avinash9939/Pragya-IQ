from functools import lru_cache
from typing import List
from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    """
    Application Settings class.
    Reads values from environment variables or a .env file.
    """
    app_name: str = "AI-Powered BI Platform"
    app_env: str = "development"
    debug: bool = True
    secret_key: str = "replace_me_with_a_secure_random_key_in_production"
    access_token_expire_minutes: int = 60
    database_url: str = "postgresql://postgres:postgres@localhost:5432/bi_platform"
    cors_origins: str = "http://localhost:3000,http://127.0.0.1:3000"
    max_upload_size_mb: int = 50
    churn_config: dict = {"recency_threshold_days": 90}
    gemini_api_key: str = ""
    embedding_model_name: str = "models/embedding-001"

    # SettingsConfigDict specifies configuring behavior of settings loading
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore"
    )

    @property
    def cors_origin_list(self) -> List[str]:
        """
        Parses the comma-separated cors_origins string into a list of origins.
        Why: Fastapi CORSMiddleware expects a list of origins.
        """
        if not self.cors_origins:
            return []
        return [origin.strip() for origin in self.cors_origins.split(",") if origin.strip()]

    @property
    def is_production(self) -> bool:
        """
        Check if the current app environment is production.
        Why: Conditionally apply select features like autogenerating database tables.
        """
        return self.app_env.lower() == "production"

@lru_cache
def get_settings() -> Settings:
    """
    Yields a cached settings singleton instance.
    Why: Avoid reading the env file and system env variables repeatedly.
    """
    return Settings()

settings = get_settings()
