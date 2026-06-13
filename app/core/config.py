from functools import cached_property
from urllib.parse import quote_plus

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    postgre_username: str = Field(alias="POSTGRE_USERNAME")
    postgre_password: str = Field(alias="POSTGRE_PASSWORD")
    postgre_host: str = Field(alias="POSTGRE_HOST")
    postgre_port: int = Field(alias="POSTGRE_PORT")
    postgre_db: str = Field(alias="POSTGRE_DB")

    @cached_property
    def database_url(self) -> str:
        username = quote_plus(self.postgre_username)
        password = quote_plus(self.postgre_password)
        return (
            f"postgresql+psycopg://{username}:{password}"
            f"@{self.postgre_host}:{self.postgre_port}/{self.postgre_db}"
        )


settings = Settings()

