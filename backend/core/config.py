"""Central application configuration.

All settings are loaded from environment variables (and the local `.env`
file) via pydantic-settings. No secrets are hard-coded here — they live in
`.env`, which is git-ignored. See `.env.example` for the full template.
"""

from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # ---- Runtime ----
    environment: str = "development"
    host: str = "0.0.0.0"
    port: int = 8000
    # Comma-separated list of allowed CORS origins ("*" allows all).
    cors_origins: str = "*"
    # Create the database (if missing) and apply migrations on startup.
    auto_migrate: bool = True

    # ---- Database ----
    db_host: str = "localhost"
    db_port: str = "5432"
    db_name: str = "Manual_order"
    db_user: str = "postgres"
    db_password: str = ""

    # ---- JWT / auth ----
    jwt_secret: str = ""
    jwt_algorithm: str = "HS256"
    jwt_expire_minutes: int = 480

    # ---- SMTP / email ----
    smtp_server: str = "smtp.gmail.com"
    smtp_port: int = 587
    email: str = ""
    password: str = ""

    # ---- Application ----
    app_url: str = "http://localhost:8000"

    # ---- SAP integration ----
    sap_api_url: str = ""
    sap_username: str = ""
    sap_password: str = ""

    @property
    def is_production(self) -> bool:
        return self.environment.strip().lower() in {"production", "prod"}

    @property
    def db_config(self) -> dict:
        return {
            "host": self.db_host,
            "port": self.db_port,
            "database": self.db_name,
            "user": self.db_user,
            "password": self.db_password,
        }

    @property
    def cors_origin_list(self) -> list[str]:
        return [o.strip() for o in self.cors_origins.split(",") if o.strip()]

    def validate_required(self) -> None:
        """Fail fast in production when critical secrets are missing or weak."""
        if not self.is_production:
            return
        problems = []
        if not self.jwt_secret or self.jwt_secret == "change-this-in-production":
            problems.append("JWT_SECRET must be set to a strong random value")
        if not self.db_password:
            problems.append("DB_PASSWORD must be set")
        if problems:
            raise RuntimeError(
                "Invalid production configuration:\n  - " + "\n  - ".join(problems)
            )


@lru_cache
def get_settings() -> Settings:
    settings = Settings()
    settings.validate_required()
    return settings


settings = get_settings()

# ---------------------------------------------------------------------------
# Backwards-compatible module-level names (used across the codebase).
# ---------------------------------------------------------------------------
SMTP_SERVER = settings.smtp_server
SMTP_PORT = settings.smtp_port
EMAIL = settings.email
PASSWORD = settings.password

APP_URL = settings.app_url

DB_CONFIG = settings.db_config

JWT_SECRET = settings.jwt_secret
JWT_ALGORITHM = settings.jwt_algorithm
JWT_EXPIRE_MINUTES = settings.jwt_expire_minutes

SAP_API_URL = settings.sap_api_url
SAP_USERNAME = settings.sap_username
SAP_PASSWORD = settings.sap_password
