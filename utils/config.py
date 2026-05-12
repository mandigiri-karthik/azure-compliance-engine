from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    azure_storage_connection_string: str
    azure_storage_container_name: str
    azure_storage_account_name: str
    azure_storage_account_key: str

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8"
    )


settings = Settings()