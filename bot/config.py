from pydantic_settings import BaseSettings
from pydantic import Field


class Settings(BaseSettings):
    """Teahouse application settings loaded from environment variables."""

    # Telegram
    bot_token: str = Field(..., alias="BOT_TOKEN")

    # Database
    database_url: str = Field(
        "postgresql+asyncpg://teahouse:teahouse_secret@localhost:5432/teahouse",
        alias="DATABASE_URL",
    )

    # Redis
    redis_url: str = Field("redis://localhost:6379/0", alias="REDIS_URL")

    # Google Gemini (bir nechta key vergul bilan ajratilgan)
    gemini_api_keys: str = Field(..., alias="GEMINI_API_KEYS")
    gemini_model: str = Field("gemini-3.6-flash", alias="GEMINI_MODEL")

    @property
    def gemini_keys_list(self) -> list[str]:
        """Parse comma-separated API keys into a list."""
        return [k.strip() for k in self.gemini_api_keys.split(",") if k.strip()]

    # App
    timezone: str = Field("Asia/Tashkent", alias="TIMEZONE")
    meeting_price_uzs: int = Field(99000, alias="MEETING_PRICE_UZS")
    min_table_size: int = Field(3, alias="MIN_TABLE_SIZE")
    max_table_size: int = Field(4, alias="MAX_TABLE_SIZE")
    payment_window_minutes: int = Field(60, alias="PAYMENT_WINDOW_MINUTES")

    # Admin
    admin_secret_key: str = Field("change_this", alias="ADMIN_SECRET_KEY")
    admin_port: int = Field(8000, alias="ADMIN_PORT")

    model_config = {"env_file": ".env", "env_file_encoding": "utf-8", "extra": "ignore"}


settings = Settings()
