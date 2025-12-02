#!/usr/bin/env python3
from contextlib import asynccontextmanager
from fastapi import FastAPI, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text
from redis.asyncio import Redis

from src.db.session import get_db
from src.core.config import settings
from src.api.v1.api import router as v1_router


@asynccontextmanager
async def lifespan(app: FastAPI):
    redis = Redis.from_url(settings.REDIS_URL, decode_responses=True)
    app.state.redis = redis                     # ← this is correct
    print("Redis connected successfully")
    yield
    await redis.close()
    print("Redis disconnected")


# Instantiate FastAPI
app = FastAPI(
    title="Drone Telemetry Platform",
    version="0.1.0",
    lifespan=lifespan
)


# Add router
app.include_router(v1_router)


# Root
@app.get("/")
async def root():
    return {"message": "Drone Telemetry Platform is running"}


# Health endpoint
@app.get("/health")
async def health(db: AsyncSession = Depends(get_db)):
    # Ping DB
    try:
        await db.execute(text("SELECT 1"))
        db_status = "up"
    except Exception as e:
        raise HTTPException(status_code=503, detail=f"DB down: {e}")

    # Ping Redis properly using app.state
    redis_status = "down"
    try:
        await app.state.redis.ping()
        redis_status = "up"
    except Exception as e:
        redis_status = f"down ({e})"

    return {
        "status": "ok" if db_status == "up" and redis_status == "up" else "degraded",
        "db": db_status,
        "redis": redis_status
    }
