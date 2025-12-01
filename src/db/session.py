#!/usr/bin/env python3
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker

from src.core.config import settings
# from models.base import Base   # noqa: F401  (needed for Alembic)


engine = create_async_engine(
    settings.DATABASE_URL,
    echo=False,           # set True only for debugging
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
