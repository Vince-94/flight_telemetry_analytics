#!/usr/bin/env python3
# tests/conftest.py
import pytest
import pytest_asyncio
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker

from src.main import app
from src.db.session import get_db
from src.db.models.base import Base


# Test DB on port 5433 (your docker-compose test-pg)
TEST_DATABASE_URL = "postgresql+asyncpg://postgres:postgres@localhost:5433/test_dronedb"

engine = create_async_engine(TEST_DATABASE_URL, echo=False)
TestingSessionLocal = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)


async def override_get_db():
    async with TestingSessionLocal() as session:
        yield session


app.dependency_overrides[get_db] = override_get_db


@pytest_asyncio.fixture
async def client():
    # Drop and recreate tables
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
        await conn.run_sync(Base.metadata.create_all)

    # Use transport=ASGITransport (new httpx way)
    async with AsyncClient(
        transport=ASGITransport(app=app),  # ← CORRECT WAY
        base_url="http://test"
    ) as client:
        yield client

    # Cleanup
    app.dependency_overrides.clear()
