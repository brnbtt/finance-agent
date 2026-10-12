from pathlib import Path

from pydantic import SecretStr
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    telegram_bot_token: SecretStr
    invite_codes: str  # comma-separated
    azure_openai_endpoint: str
    azure_openai_deployment: str = "gpt-6-luna"
    # Leave empty to authenticate with Entra ID (az login locally, managed identity in Azure).
    azure_openai_api_key: SecretStr | None = None
    database_path: Path = Path("data/finance_bot.db")

    @property
    def invite_code_list(self) -> list[str]:
        return [code.strip() for code in self.invite_codes.split(",") if code.strip()]
