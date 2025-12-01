#!/usr/bin/env python3
from sqlalchemy import ForeignKey, DateTime, Integer, func
from sqlalchemy.dialects.postgresql import UUID, DOUBLE_PRECISION, JSONB
from sqlalchemy.orm import Mapped, mapped_column
from .base import Base
import uuid


class Flight(Base):
    __tablename__ = "flights"

    # Primary key
    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )

    # ForeignKey: drones.id
    drone_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("drones.id", ondelete="CASCADE"), index=True
    )

    # Starting/ending timestamp
    start_ts: Mapped[DateTime] = mapped_column(DateTime(timezone=True), nullable=False)
    end_ts: Mapped[DateTime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    # Duration time
    duration_s: Mapped[int | None] = mapped_column(Integer)

    # Battery
    total_mah: Mapped[int | None] = mapped_column(Integer)
    max_current: Mapped[float | None] = mapped_column(DOUBLE_PRECISION)
    min_voltage: Mapped[float | None] = mapped_column(DOUBLE_PRECISION)

    # Metrics
    computed_metrics: Mapped[dict | None] = mapped_column(JSONB, default=dict)

    # Created/Updated timespamp
    created_at: Mapped[DateTime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[DateTime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )