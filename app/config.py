from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = "SupportOps Copilot"
    app_mode: str = "mock"
    database_url: str = "sqlite:///supportops.db"
    azure_openai_endpoint: str | None = None
    azure_openai_api_key: str | None = None
    azure_openai_deployment: str | None = None
    azure_openai_api_version: str = "2024-02-15-preview"

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")

    @property
    def use_azure(self) -> bool:
        return (
            self.app_mode.lower() == "azure"
            and bool(self.azure_openai_endpoint)
            and bool(self.azure_openai_api_key)
            and bool(self.azure_openai_deployment)
        )


@lru_cache
def get_settings() -> Settings:
    return Settings()
