#!/usr/bin/env python3
from fastapi import APIRouter, Depends, status, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.db.session import get_db
from src.db.models.drone import Drone
from src.schemas.drone import DroneRequest, DroneResponse
import secrets
from src.core.security import get_current_drone


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


"""
List all drones that belong to the authenticated user.
Right now: 1 API key = 1 drone → returns just yours.
Future: if you add user_id → returns all drones of that user.
"""
@router.post("/", response_model=list[DroneResponse])
async def get_register_drones(
    drone: Drone = Depends(get_current_drone),  # TODO to authenticated drone
    db: AsyncSession = Depends(get_db)
):
    # For now: just return the current one (clean & works)
    # Later: query all drones with same owner_id
    return [DroneResponse(
        id=str(drone.id),
        name=drone.name,
        api_key=drone.api_key   # you can remove this line later for security
    )]


@router.post("/{drone_id}", response_model=DroneResponse)
async def get_register_drone(
    drone_id: str,
    current_drone: Drone = Depends(get_current_drone),  # TODO authenticated drone
    db: AsyncSession = Depends(get_db)
):
    # Convert string to UUID if needed (our id is UUID)
    try:
        from uuid import UUID
        target_id = UUID(drone_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid drone ID format")

    # For now: only allow fetching yourself
    if current_drone.id != target_id:
        raise HTTPException(
            status_code=403,
            detail="You can only access your own drone"
        )

    # In future, when you have users:
    # result = await db.execute(select(Drone).where(Drone.id == target_id, Drone.owner_id == current_user.id))
    return DroneResponse(
        id=str(current_drone.id),
        name=current_drone.name,
        api_key=current_drone.api_key  # optional: remove in prod
    )
