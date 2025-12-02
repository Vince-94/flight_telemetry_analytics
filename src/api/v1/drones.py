#!/usr/bin/env python3
from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession
from src.db.session import get_db
from src.db.models.drone import Drone
from src.schemas.drone import DroneRequest, DroneResponse
import secrets


router = APIRouter(prefix="/drones", tags=["drones"])


"""Register a new drone by receiving its name.

Args:
    payload (DroneRequest): Request input schema
    db (AsyncSession, optional): database session. Defaults to Depends(get_db).

Returns:
    DroneResponse: {id, drone_name, api_key}
"""
@router.post("/", response_model=DroneResponse, status_code=status.HTTP_201_CREATED)
async def register_drone(payload: DroneRequest, db: AsyncSession = Depends(get_db)):
    # TODO skip if the drone already registered
    # api_key = str(ulid.new())
    api_key = secrets.token_urlsafe(32)

    # Create Drone object
    drone = Drone(name=payload.name, api_key=api_key)

    # Add drone to database
    db.add(drone)
    await db.commit()
    await db.refresh(drone)

    # Return response
    return DroneResponse.from_orm(drone)
