#!/usr/bin/env python3
from contextlib import asynccontextmanager
from fastapi import FastAPI, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text
import asyncio

from src.db.session import get_db
from src.core.config import settings


@asynccontextmanager
async def lifespan(app: FastAPI):
    print("Application startup complete")
    yield
    # Shutdown
    print("Application shutdown")


app = FastAPI(
    title="Drone Telemetry Platform",
    version="0.1.0",
    lifespan=lifespan
)


# Root
@app.get("/")
async def root():
    return {"message": "Drone Telemetry Platform is running"}


# Health endpoint
@app.get("/health")
async def health(db: AsyncSession = Depends(get_db)):
    """
    Health check that also pings the database asynchronously.
    Returns 200 + {"status": "ok", "db": "ok"} if everything is fine.
    """
    try:
        # Simple async query to test DB connectivity
        await db.execute(text("SELECT 1"))
        return {"status": "ok", "db": "ok"}
    except Exception as e:
        raise HTTPException(status_code=503, detail=f"Database not available: {str(e)}")
