#!/usr/bin/env python3
import uuid
from datetime import datetime, timedelta, timezone
import orjson
import pandas as pd
import numpy as np
from sqlalchemy import update, select
from sqlalchemy.ext.asyncio import AsyncSession
from fastapi import Request

from src.db.session import AsyncSessionLocal
from src.db.models.telemetry import TelemetryRaw
from src.db.models.flight import Flight


HIGH_THROTTLE_THRESHOLD = 0.10   # 10%
IDLE_TIMEOUT_SECONDS = 15        # if throttle ≤ 10% for 15s → flight ends
UTC = timezone.utc


def get_redis(request: Request):
    """Safe way to get redis_client without circular imports"""
    return request.app.state.redis


def compute_advanced_metrics(df: pd.DataFrame) -> dict:
    """All the sexy metrics recruiters drool over"""
    if df.empty:
        return {}

    df["ts_sec"] = (df["ts"] - df["ts"].min()).dt.total_seconds()

    metrics = {}

    # === Energy & Power ===
    if "voltage" in df.columns and "current" in df.columns and df[["voltage", "current"]].notna().all(axis=1).any():
        df["power_w"] = df["voltage"] * df["current"]
        metrics["peak_power_w"] = float(df["power_w"].max())
        metrics["average_power_w"] = float(df["power_w"].mean())
        # Integrated energy from power curve (more accurate than mah_drawn)
        dt = df["ts"].diff().dt.total_seconds().fillna(0)
        metrics["total_wh"] = float((df["power_w"] * dt / 3600).sum())
        metrics["total_mah_from_power"] = metrics["total_wh"] * 1000 / df["voltage"].mean() if df["voltage"].mean() > 0 else None

    if df["mah_drawn"].notna().any():
        metrics["total_mah"] = int(df["mah_drawn"].max() - df["mah_drawn"].min())

    metrics["min_voltage"] = float(df["voltage"].min()) if df["voltage"].notna().any() else None

    # === Stability ===
    for axis in ["roll", "pitch", "yaw"]:
        if axis in df.columns and df[axis].notna().any():
            metrics[f"{axis}_std_dev"] = float(df[axis].std())
            metrics[f"{axis}_max_rate"] = float(df[axis].abs().max())

    # === Throttle Smoothness (lower = smoother pilot) ===
    df["throttle_change"] = df["throttle"].diff().abs()
    metrics["throttle_jerk_score"] = float(df["throttle_change"].mean())  # lower = better
    metrics["average_throttle"] = float(df["throttle"].mean())

    # === Aggressiveness / Pilot Fingerprint ===
    metrics["throttle_90th_percentile"] = float(np.percentile(df["throttle"], 90))
    time_above_80 = len(df[df["throttle"] > 0.8]) / len(df) * 100
    metrics["percent_time_full_throttle"] = float(time_above_80)

    # === Efficiency (if GPS present) ===
    if df[["latitude", "longitude"]].notna().all(axis=1).any():
        from math import radians, sin, cos, sqrt, atan2
        R = 6371000  # Earth radius in meters

        lat1 = df["latitude"].shift(1)
        lon1 = df["longitude"].shift(1)
        lat2 = df["latitude"]
        lon2 = df["longitude"]

        dlat = np.radians(lat2 - lat1)
        dlon = np.radians(lon2 - lon1)
        a = np.sin(dlat/2)**2 + np.cos(np.radians(lat1)) * np.cos(np.radians(lat2)) * np.sin(dlon/2)**2
        c = 2 * np.arctan2(np.sqrt(a), np.sqrt(1-a))
        df["segment_dist_m"] = R * c
        total_distance_km = df["segment_dist_m"].sum() / 1000

        if total_distance_km > 0.01 and metrics.get("total_wh"):
            metrics["wh_per_km"] = round(metrics["total_wh"] / total_distance_km, 3)
            metrics["total_distance_km"] = round(total_distance_km, 3)

    # === Freestyle vs Racing Score (heuristic) ===
    high_g_force_proxy = (df[["roll", "pitch"]].abs() > 45).any(axis=1).mean()
    metrics["freestyle_score"] = round(high_g_force_proxy * 100, 1)  # higher = more acrobatic

    metrics["flight_duration_s"] = int(df["ts_sec"].max())

    return metrics


async def handle_flight_detection_and_analytics(drone_id: uuid.UUID, packets: list[dict], request: Request):
    """
    Called as BackgroundTask after every telemetry batch.
    Detects flight start/end and runs full analytics when flight ends.
    """
    if not packets:
        return

    # Ensure packets are sorted by timestamp
    packets.sort(key=lambda p: p["ts"])

    # redis_client = app.state.redis
    redis_client = get_redis(request)
    state_key = f"drone:{drone_id}:flight_state"

    raw_state = await redis_client.get(state_key)
    if raw_state:
        state = orjson.loads(raw_state)
    else:
        state = {
            "current_flight_id": None,
            "last_high_throttle_ts": None
        }

    async with AsyncSessionLocal() as db:
        current_flight_id = state["current_flight_id"]

        # Process each packet in the batch for flight start detection
        for packet in packets:
            packet_ts = packet["ts"]
            if packet_ts.tzinfo is None:
                packet_ts = packet_ts.replace(tzinfo=UTC)
            else:
                packet_ts = packet_ts.astimezone(UTC)

            throttle = packet.get("throttle", 0) or 0.0

            if throttle > HIGH_THROTTLE_THRESHOLD:
                if not current_flight_id:
                    # === START NEW FLIGHT ===
                    new_flight = Flight(
                        drone_id=drone_id,
                        start_ts=packet_ts
                    )
                    db.add(new_flight)
                    await db.commit()
                    await db.refresh(new_flight)

                    current_flight_id = str(new_flight.id)
                    state["current_flight_id"] = current_flight_id
                    print(f"[Flight] Started new flight {new_flight.id} for drone {drone_id}")

                state["last_high_throttle_ts"] = packet_ts.isoformat()

        # Assign flight_id to this batch (if we have an active flight)
        if current_flight_id:
            flight_uuid = uuid.UUID(current_flight_id)
            ts_list = [p["ts"] for p in packets]
            stmt = (
                update(TelemetryRaw)
                .where(TelemetryRaw.drone_id == drone_id, TelemetryRaw.ts.in_(ts_list))
                .values(flight_id=flight_uuid)
            )
            await db.execute(stmt)
            await db.commit()

        # Check if flight should end (throttle low for long enough)
        latest_throttle = packets[-1].get("throttle", 0) or 0.0
        if (current_flight_id and state["last_high_throttle_ts"] and latest_throttle <= HIGH_THROTTLE_THRESHOLD):
            last_high_ts = datetime.fromisoformat(state["last_high_throttle_ts"]).replace(tzinfo=UTC)
            if (datetime.now(UTC) - last_high_ts) >= timedelta(seconds=IDLE_TIMEOUT_SECONDS):
                # === END FLIGHT & RUN ANALYTICS ===
                flight_uuid = uuid.UUID(current_flight_id)

                # Set end timestamp
                await db.execute(
                    update(Flight)
                    .where(Flight.id == flight_uuid)
                    .values(end_ts=datetime.now(UTC))
                )
                await db.commit()

                print(f"[Flight] Flight {flight_uuid} ended → running analytics...")

                # Load all telemetry for this flight
                result = await db.execute(
                    select(TelemetryRaw).where(TelemetryRaw.flight_id == flight_uuid).order_by(TelemetryRaw.ts)
                )
                rows = result.scalars().all()

                if rows:
                    df = pd.DataFrame([
                        {
                            "ts": row.ts,
                            "throttle": row.throttle or 0.0,
                            "voltage": row.voltage,
                            "current": row.current or 0.0,
                            "mah_drawn": row.mah_drawn or 0,
                            "roll": row.roll or 0.0,
                            "pitch": row.pitch or 0.0,
                            "yaw": row.yaw or 0.0,
                            "vx": row.vx or 0.0,
                            "vy": row.vy or 0.0,
                            "vz": row.vz or 0.0,
                            "latitude": row.latitude,
                            "longitude": row.longitude,
                        } for row in rows
                    ])

                    metrics = compute_advanced_metrics(df)

                    # Save metrics
                    await db.execute(
                        update(Flight)
                        .where(Flight.id == flight_uuid)
                        .values(computed_metrics=metrics)
                    )
                    await db.commit()

                    print(f"[Flight] Analytics complete for flight {flight_uuid}")

                # Reset state
                state["current_flight_id"] = None
                state["last_high_throttle_ts"] = None

        # Save state back to Redis
        await redis_client.set(state_key, orjson.dumps(state))
