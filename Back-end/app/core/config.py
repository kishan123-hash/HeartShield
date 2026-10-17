from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):

    APP_NAME: str

    DATABASE_URL: str

    JWT_SECRET_KEY: str

    JWT_ALGORITHM: str = "HS256"

    ACCESS_TOKEN_EXPIRE_MINUTES: int = 1440

    GEMINI_API_KEY: str

    GEMINI_MODEL: str = "gemini-3.5-flash-lite"

    FRONTEND_ORIGIN: str = "http://localhost:5173"

    UPLOAD_DIRECTORY: str = "reports_storage/medical_reports"

    # ==========================================
    # SMTP / EMAIL SETTINGS
    # ==========================================

    SMTP_HOST: str = "smtp.gmail.com"

    SMTP_PORT: int = 587

    SMTP_USERNAME: str = "projectwork1220@gmail.com"

    SMTP_PASSWORD: str="aqguersyznvnaael"

    SMTP_FROM_EMAIL: str = "projectwork1220@gmail.com"

    model_config = SettingsConfigDict(
        env_file=".env"
    )


settings = Settings()