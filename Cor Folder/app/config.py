from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    GOOGLE_MAPS_API_KEY: str = ""
    OPENAI_API_KEY: str = ""
    # Keep this configurable because model availability is account/project dependent.
    OPENAI_MODEL: str = "gpt-6-luna"
    DATABASE_URL: str = "sqlite:///./tourism.db"
    APP_NAME: str = "Tourism Intelligence Backend"
    APP_VERSION: str = "2.0.0"
    ENVIRONMENT: str = "development"
    CORS_ORIGINS: str = "http://localhost:3000,http://localhost:5173"
    ALLOWED_HOSTS: str = "127.0.0.1,localhost"
    RATE_LIMIT_PER_MINUTE: int = Field(default=120, ge=0, le=10000)
    GOOGLE_TIMEOUT_SECONDS: float = Field(default=20.0, gt=1, le=120)
    GOOGLE_RETRIES: int = Field(default=2, ge=0, le=5)
    OPENAI_TIMEOUT_SECONDS: float = Field(default=30.0, gt=1, le=120)
    OPENAI_RETRIES: int = Field(default=2, ge=0, le=5)
    # Developer 3 — authentication and language-provider settings.
    AUTH_SECRET: str = ""
    ACCESS_TOKEN_MINUTES: int = Field(default=60, ge=5, le=1440)
    TRANSLATION_API_URL: str = ""
    TRANSLATION_API_KEY: str = ""
    SPEECH_TO_TEXT_API_URL: str = ""
    SPEECH_TO_TEXT_API_KEY: str = ""
    BOOTSTRAP_ADMIN_EMAIL: str = ""
    BOOTSTRAP_ADMIN_PASSWORD: str = ""
    AUTO_CREATE_DB: bool = False
    LOG_LEVEL: str = "INFO"

    # -----------------------------------------------------------------------
    # Developer 2 — Gamification settings
    # -----------------------------------------------------------------------
    # Points awarded when a visit is GPS-verified.
    VISIT_REWARD_POINTS: int = Field(default=50, ge=0)
    # Points awarded when a photo proof is accepted on a verified visit.
    PHOTO_REWARD_POINTS: int = Field(default=10, ge=0)
    # Default GPS verification radius in metres (used when the place record
    # does not specify its own radius).
    DEFAULT_VISIT_RADIUS_METERS: float = Field(default=150.0, gt=0)

    model_config = SettingsConfigDict(env_file=".env", extra="ignore", case_sensitive=True)

    @staticmethod
    def _split_csv(value: str) -> list[str]:
        return [x.strip() for x in value.split(",") if x.strip()]

    @property
    def cors_origins(self) -> list[str]:
        return self._split_csv(self.CORS_ORIGINS)

    @property
    def allowed_hosts(self) -> list[str]:
        return self._split_csv(self.ALLOWED_HOSTS)

    @field_validator("ENVIRONMENT", mode="before")
    @classmethod
    def normalize_environment(cls, value: str) -> str:
        return str(value).strip().lower()


settings = Settings()
