#!/usr/bin/env python3
from sqlalchemy import BigInteger, DateTime, ForeignKey, Integer, SmallInteger, func, JSON
from sqlalchemy.dialects.postgresql import UUID, DOUBLE_PRECISION, DOUBLE_PRE
from sqlalchemy.orm import Mapped, mapped_column
from .base import Base
import uuid


class TelemetryRaw(Base):
    __tablename__ = "telemetry_raw"

    # Primary key
    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)

    # ForeignKey: drones.id
    drone_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("drones.id", ondelete="CASCADE"), index=True
    )

    # Timestamp
    ts: Mapped[DateTime] = mapped_column(DateTime(timezone=True), index=True, nullable=False)

    # Core telemetry (all optional except ts)
    latitude: Mapped[float | None] = mapped_column(DOUBLE_PRECISION)
    longitude: Mapped[float | None] = mapped_column(DOUBLE_PRECISION)
    altitude: Mapped[float | None] = mapped_column(DOUBLE_PRECISION)

    # Velocity
    vx: Mapped[float | None] = mapped_column(DOUBLE_PRECISION)
    vy: Mapped[float | None] = mapped_column(DOUBLE_PRECISION)
    vz: Mapped[float | None] = mapped_column(DOUBLE_PRECISION)

    # Attitude
    roll: Mapped[float | None] = mapped_column(DOUBLE_PRECISION)
    pitch: Mapped[float | None] = mapped_column(DOUBLE_PRECISION)
    yaw: Mapped[float | None] = mapped_column(DOUBLE_PRECISION)

    # Throttle
    throttle: Mapped[float | None] = mapped_column(DOUBLE_PRECISION)

    # Battery
    voltage: Mapped[float | None] = mapped_column(DOUBLE_PRECISION)
    current: Mapped[float | None] = mapped_column(DOUBLE_PRECISION)
    mah_drawn: Mapped[int | None] = mapped_column(Integer)
    rssi: Mapped[int | None] = mapped_column(SmallInteger)

    # Flight ID
    flight_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), nullable=True, index=True
    )

    # Further field
    extra: Mapped[dict | None] = mapped_column(JSON, default=dict)
