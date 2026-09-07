import base64
from pydantic_settings import BaseSettings
from pydantic import Field

# Google Gemini 10 ta API key (avtomatik rotatsiya uchun o'rnatilgan)
_DEFAULT_GEMINI_B64 = (
    "QVEuQWI4Uk42SWpSRldmYjlqS1NyVF9wNTVBYUFHeXhtZUtIQWhSVDlWY3dNdFVKd0F0R2cs"
    "QVEuQWI4Uk42SzJzdUpUZ0psY29sOXBrU3Q3OVFCX3dfWkpXLWR1S2tHcnVTMHNZVVVGUFEs"
    "QVEuQWI4Uk42TGszNzluMFAyQUJTYWRNdkxTQS1RcDZ5dVNZekNObTNiNEFLcGxSNTlPQ1Es"
    "QVEuQWI4Uk42Sm9UQ2ZtSU9XQWRULUtYaFkzTkxKZFNtczNEQUFwbHhnUkFGbWdZSE5ZaFEs"
    "QVEuQWI4Uk42TFIzbEtaQUdzbm1mN1RwcE9RcTJfS2hWZ00xUkVJUFhab01ZY1Ffd3RQS0Es"
    "QVEuQWI4Uk42SmVBWk9iS2MtSkU1eGx4alZGUHNyV1lQdlRlTmkxOXU2S2FLcDVQaWlyQlEs"
    "QVEuQWI4Uk42S3c0aUhpOEU5LTFZc3JlX3hqN0dFMV9kN3RpTWZvTUFsRnUtNnNPWEI3d0Es"
    "QVEuQWI4Uk42SmJTVDQ4b3F3cXhFQkE3dWI5T1d6Wlprd2VPVjFfc2FOTTBBSWZlUGR0d2cs"
    "QVEuQWI4Uk42TDRhTnhJQXhWVXlsVDRzZm13cDBnOGU5UDdmTnl6RUpyMk5TRFZ2NWFva2cs"
    "QVEuQWI4Uk42SzhmMzNNTW1wZUh1cG9OVkUyNTRLMkUtWWpObXFKV3ZSNVg5aHVJT0Q2OFE="
)
_DEFAULT_GEMINI_KEYS = base64.b64decode(_DEFAULT_GEMINI_B64).decode()


# Standart Telegram Bot Token
_DEFAULT_BOT_TOKEN_B64 = "ODgxNTA5NTcyOTpBQUdMLUUyd0tfZzFEdnVZTkx1WFNoNWVkVmJZU0dIUmhoRQ=="
_DEFAULT_BOT_TOKEN = base64.b64decode(_DEFAULT_BOT_TOKEN_B64).decode()


class Settings(BaseSettings):
    """Teahouse application settings loaded from environment variables."""

    # Telegram
    bot_token: str = Field(
        _DEFAULT_BOT_TOKEN,
        alias="BOT_TOKEN",
    )

    # Database
    database_url: str = Field(
        "sqlite+aiosqlite:///./teahouse.db",
        alias="DATABASE_URL",
    )

    # Redis
    redis_url: str = Field("redis://localhost:6379/0", alias="REDIS_URL")

    # Google Gemini (10 ta key vergul bilan ajratilgan)
    gemini_api_keys: str = Field(_DEFAULT_GEMINI_KEYS, alias="GEMINI_API_KEYS")
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
    admin_secret_key: str = Field("teahouse_admin_2024_secret", alias="ADMIN_SECRET_KEY")
    admin_port: int = Field(8000, alias="ADMIN_PORT")

    model_config = {"env_file": ".env", "env_file_encoding": "utf-8", "extra": "ignore"}


settings = Settings()
