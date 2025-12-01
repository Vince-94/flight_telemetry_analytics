#!/usr/bin/env python3
from sqlalchemy import String, DateTime, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column
import uuid
from .base import Base


class Drone(Base):
    """
    Drone model class
    """
    __tablename__ = "drones"

    # Primary key
    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )

    # Robot name
    name: Mapped[str] = mapped_column(String, nullable=False)

    # API key
    api_key: Mapped[str] = mapped_column(String, unique=True, index=True, nullable=False)

    # Created/Updated timespamp
    created_at: Mapped[DateTime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    updated_at: Mapped[DateTime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )
