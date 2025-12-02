#!/usr/bin/env python3
import json
import orjson
import uuid
from fastapi import APIRouter, Depends, HTTPException, status, Request, BackgroundTasks
from fastapi.responses import JSONResponse
from sqlalchemy.ext.asyncio import AsyncSession

from src.db.session import get_db
from src.db.models.telemetry import TelemetryRaw
from src.db.models.drone import Drone
from src.core.security import get_current_drone
from src.schemas.telemetry import TelemetryIngestRequest
from src.services.flight_service import handle_flight_detection_and_analytics


router = APIRouter(prefix="/telemetry", tags=["telemetry"])


def get_redis(request: Request):
    """Safe way to get redis_client without circular imports"""
    return request.app.state.redis


"""Load telementry to database by receiving a list of TelemetryIngestRequest,
   and set in redis the last packet received from the drone

Args:
    packets (list[TelemetryIngestRequest]): _description_
    drone (Drone, optional): _description_. Defaults to Depends(get_current_drone).
    db (AsyncSession, optional): _description_. Defaults to Depends(get_db).

Raises:
    HTTPException: _description_

Returns:
    dict: ingested: [int] length of packets
"""
@router.post("/", status_code=status.HTTP_201_CREATED)
async def ingest_telemetry(
    request: Request,
    packets: list[TelemetryIngestRequest],
    drone: Drone = Depends(get_current_drone),
    db: AsyncSession = Depends(get_db),
    background: BackgroundTasks = None,
):
    # Check if there are no packets
    if len(packets) == 0:
        return JSONResponse({"ingested": 0})

    # Check if there are more than 500 packets
    if len(packets) > 500:
        raise HTTPException(status_code=413, detail="Max 500 packets per request")

    # Create TelemetryRaw list of packets
    db_packets = [
        TelemetryRaw(
            drone_id=drone.id,
            ts=p.ts,
            throttle=p.throttle,
            voltage=p.voltage,
            current=p.current,
            mah_drawn=p.mah_drawn,
            latitude=p.latitude,
            longitude=p.longitude,
            altitude=p.altitude,
            vx=p.vx,
            vy=p.vy,
            vz=p.vz,
            roll=p.roll,
            pitch=p.pitch,
            yaw=p.yaw,
            rssi=p.rssi,
            extra=p.extra,
        )
        for p in packets
    ]

    # Add db_packets to database
    db.add_all(db_packets)
    await db.commit()

    # Update live cache with the latest packet
    latest_packet = packets[-1].model_dump()
    latest_packet["drone_id"] = str(drone.id)
    redis = get_redis(request)
    await redis.set(
        f"drone:{drone.id}:live",
        orjson.dumps(latest_packet).decode(),
        ex=60,  # expire after 60 seconds of no data
    )

    # Trigger flight session detection + analytics in background (non-blocking)
    background.add_task(
        handle_flight_detection_and_analytics,
        drone.id,
        [p.model_dump() for p in packets],   # send raw dicts (with proper ts strings)
        request,
    )

    return {"ingested": len(packets)}


@router.get("/live")
async def get_live_telemetry(
    request: Request,
    drone: Drone = Depends(get_current_drone)
):
    # Get redis instance
    redis = get_redis(request)

    data = await redis.get(f"drone:{drone.id}:live")
    if not data:
        return {"status": "no recent telemetry"}

    return json.loads(data)
