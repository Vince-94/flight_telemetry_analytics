import json
from fastapi import APIRouter, Depends, HTTPException, status, Request
from fastapi.responses import JSONResponse
from sqlalchemy.ext.asyncio import AsyncSession
from src.db.session import get_db
from src.db.models.telemetry import TelemetryRaw
from src.db.models.drone import Drone
from src.core.security import get_current_drone
from src.schemas.telemetry import TelemetryIngestRequest
import json
import orjson


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

    redis = get_redis(request)

    # Update live cache with the very latest packet
    latest = packets[-1].model_dump()
    latest["drone_id"] = str(drone.id)
    await redis.set(
        f"drone:{drone.id}:live",
        orjson.dumps(latest).decode(),   # orjson returns bytes → decode to str
        ex=60,
    )

    return {"ingested": len(packets)}


@router.get("/live")
async def get_live_telemetry(
    request: Request,
    drone: Drone = Depends(get_current_drone)
):
    redis = get_redis(request)
    data = await redis.get(f"drone:{drone.id}:live")
    if not data:
        return {"status": "no recent telemetry"}
    return json.loads(data)
