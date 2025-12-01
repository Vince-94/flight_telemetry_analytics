#!/usr/bin/env python3
from sqlalchemy.ext.asyncio import AsyncEngine
from sqlalchemy import text
from src.db.session import engine
import asyncio

# Import all the models
import src.db.models


async def create_tables() -> None:
    from src.db.models.base import Base   # now Base.metadata knows everything

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
        await conn.run_sync(Base.metadata.create_all)

    print("All tables created successfully!")


if __name__ == "__main__":
    asyncio.run(create_tables())
