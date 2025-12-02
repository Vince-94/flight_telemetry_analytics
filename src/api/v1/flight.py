#!/usr/bin/env python3
from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.db.session import get_db
from src.db.models.drone import Drone
from src.core.security import get_current_drone
from src.db.models.flight import Flight


router = APIRouter(prefix="/telemetry", tags=["telemetry"])


@router.get("/", response_model=list[dict])
async def list_flights(
    drone: Drone = Depends(get_current_drone),
    db: AsyncSession = Depends(get_db),
    limit: int = 50,
    offset: int = 0
):
    # Query flights
    result = await db.execute(
        select(Flight)
        .where(Flight.drone_id == drone.id)
        .order_by(Flight.start_ts.desc())
        .limit(limit)
        .offset(offset)
    )

    flights = result.scalars().all()
    flights_list = [
        {
            "id": str(f.id),
            "start_ts": f.start_ts.isoformat(),
            "end_ts": f.end_ts.isoformat() if f.end_ts else None,
            "duration_s": f.duration_s,
            "total_mah": f.total_mah,
            "peak_power_w": f.computed_metrics.get("peak_power_w"),
            "wh_per_km": f.computed_metrics.get("wh_per_km"),
            "freestyle_score": f.computed_metrics.get("freestyle_score"),
            # add more as you like
        }
        for f in flights
    ]

    return flights_list




