#!/usr/bin/env python3
from sqlalchemy.ext.asyncio import AsyncEngine
from sqlalchemy import text
from src.db.session import engine
import asyncio


async def create_tables() -> None:
    from src.db.models.base import Base   # imports all models so they're registered

    async with engine.begin() as conn:
        # Drop everything (only dev!)
        await conn.run_sync(Base.metadata.drop_all)
        # Create fresh
        await conn.run_sync(Base.metadata.create_all)

    print("All tables created (dev mode)")


if __name__ == "__main__":
    asyncio.run(create_tables())

