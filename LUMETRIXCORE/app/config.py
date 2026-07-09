from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")
    APP_SECRET: str = "dev-secret-change-me"
    VAULT_KEY: str = ""  # Fernet key; si vacío se deriva de APP_SECRET (solo dev)
    DATABASE_URL: str = "sqlite:///./lumetrix.db"
    REDIS_URL: str = "redis://localhost:6379/0"
    SEND_MODE: str = "background"  # background | celery
    WARMUP_MAX_PER_HOUR: int = 200
    WARMUP_MAX_PER_DAY: int = 1000
    SEND_MIN_DELAY_SEC: int = 8
    SEND_MAX_DELAY_SEC: int = 25
    SEND_PAUSE_EVERY: int = 50
    SEND_PAUSE_SECONDS: int = 300
    BOUNCE_RATE_LIMIT: float = 0.02
    COMPLAINT_RATE_LIMIT: float = 0.003
    RETENTION_DAYS: int = 15
    ADMIN_EMAIL: str = "admin@lumetrixcore.com"
    ADMIN_PASSWORD: str = "Canon2026!"
    AI_MODEL: str = "haiku"   # haiku | sonnet | opus | fable | o el string completo
    AI_MODE: str = "managed"  # managed = usa el token de la plataforma | byo = usa el del usuario
    PLATFORM_AI_TOKEN: str = ""  # API key de Anthropic de la PLATAFORMA (modo gestionado)

settings = Settings()
