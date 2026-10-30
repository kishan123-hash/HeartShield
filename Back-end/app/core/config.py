from pydantic_settings import (
    BaseSettings,
    SettingsConfigDict
)


class Settings(BaseSettings):

    APP_NAME: str

    DATABASE_URL: str

    JWT_SECRET_KEY: str

    JWT_ALGORITHM: str = "HS256"

    ACCESS_TOKEN_EXPIRE_MINUTES: int = 1440

    GEMINI_API_KEY: str

    GEMINI_MODEL: str = "gemini-3.5-flash-lite"

    FRONTEND_ORIGIN: str = "http://localhost:3000"

    FRONTEND_URL: str | None = None

    UPLOAD_DIRECTORY: str = "reports_storage/medical_reports"

    # ==========================================
    # SMTP / EMAIL SETTINGS (Fallback)
    # ==========================================

    SMTP_HOST: str = "smtp.gmail.com"

    SMTP_PORT: int = 587

    SMTP_USERNAME: str = "projectwork1220@gmail.com"

    SMTP_PASSWORD: str = ""

    SMTP_FROM_EMAIL: str = "projectwork1220@gmail.com"

    # ==========================================
    # BREVO API SETTINGS
    # ==========================================

    BREVO_API_KEY: str = ""

    BREVO_SENDER_EMAIL: str = "workingmeet09@gmail.com"

    BREVO_SENDER_NAME: str = "HeartShield"

    model_config = SettingsConfigDict(
        env_file=".env",
        extra="ignore"
    )


settings = Settings()
