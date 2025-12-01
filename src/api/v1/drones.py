#!/usr/bin/env python3
from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession
from src.db.session import get_db
from src.db.models.drone import Drone
from src.schemas.drone import DroneRequest, DroneResponse
import secrets


router = APIRouter(prefix="/drones", tags=["drones"])


@router.post("/", response_model=DroneResponse, status_code=status.HTTP_201_CREATED)
async def register_drone(payload: DroneRequest, db: AsyncSession = Depends(get_db)):
    # api_key = str(ulid.new())
    api_key = secrets.token_urlsafe(32)

    drone = Drone(name=payload.name, api_key=api_key)

    db.add(drone)
    await db.commit()
    await db.refresh(drone)

    return DroneResponse.from_orm(drone)
