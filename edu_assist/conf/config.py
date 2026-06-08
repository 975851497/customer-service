"""应用配置管理。"""

from __future__ import annotations

from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict

ENV_FILE = Path(__file__).resolve().parent.parent.parent / ".env"


class Settings(BaseSettings):
    """应用配置，自动从 .env 文件加载。"""

    llm_api_key: str = ""
    llm_model: str = "qwen-plus"
    llm_base_url: str = "https://dashscope.aliyuncs.com/compatible-mode/v1"

    edu_api_base_url: str = "http://127.0.0.1:8000"

    database_url: str = "mysql+aiomysql://root:root@127.0.0.1:3306/edu_assist?charset=utf8mb4"

    app_host: str = "0.0.0.0"
    app_port: int = 18082

    model_config = SettingsConfigDict(env_file=ENV_FILE)


settings = Settings()
