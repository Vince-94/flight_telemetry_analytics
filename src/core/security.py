#!/usr/bin/env python3
from fastapi import Depends, Header, HTTPException, status
from sqlalchemy import select
from src.db.session import AsyncSession, get_db
from src.db.models.drone import Drone


async def get_current_drone(
    api_key: str = Header(..., alias="X-API-Key"),
    db: AsyncSession = Depends(get_db),
) -> Drone:
    result = await db.execute(select(Drone).where(Drone.api_key == api_key))
    drone = result.scalar_one_or_none()
    if not drone:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or missing API-Key",
            headers={"WWW-Authenticate": "API-Key"},
        )
    return drone
