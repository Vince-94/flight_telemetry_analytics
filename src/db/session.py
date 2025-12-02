#!/usr/bin/env python3
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
import yaml

from src.core.config import settings
# from models.base import Base   # noqa: F401  (needed for Alembic)


CONFIG_FILEPATH = "src/config/config.yaml"
with open(CONFIG_FILEPATH, "r") as file:
    config = yaml.safe_load(file)


engine = create_async_engine(
    settings.DATABASE_URL,
    echo=config.get("DEBUG"),           # set True only for debugging
    future=True,
)


AsyncSessionLocal = sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False,
)


async def get_db() -> AsyncSession:
    async with AsyncSessionLocal() as session:
        yield session
