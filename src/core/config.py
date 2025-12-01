#!/usr/bin/env python3
from pydantic_settings import BaseSettings
from functools import lru_cache
import yaml


CONFIG_FILEPATH = "src/config/config.yaml"


with open(CONFIG_FILEPATH, "r") as file:
    config = yaml.safe_load(file)


class Settings(BaseSettings):
    DATABASE_URL: str = config.get("DATABASE_URL")


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
