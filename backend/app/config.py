from functools import lru_cache
from pathlib import Path
from typing import Literal

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict

ROOT = Path(__file__).resolve().parents[2]


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=ROOT / "backend/.env", extra="ignore")
    database_url: str = "mysql+pymysql://unconfigured@127.0.0.1:3306/scu_ecommerce"
    jwt_secret: str = Field(min_length=32)
    app_timezone: Literal["Asia/Shanghai"] = "Asia/Shanghai"


@lru_cache
def settings():
    return Settings()
