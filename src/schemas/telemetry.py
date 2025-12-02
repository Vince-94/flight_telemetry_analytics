#!/usr/bin/env python3
from pydantic import BaseModel, Field, field_validator
from datetime import datetime
from typing import Optional
import pytz


class TelemetryIngestRequest(BaseModel):
    ts: datetime
    throttle: float = Field(..., ge=0.0, le=1.0)
    voltage: Optional[float] = None
    current: Optional[float] = None
    mah_drawn: Optional[int] = None
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    altitude: Optional[float] = None
    vx: Optional[float] = None
    vy: Optional[float] = None
    vz: Optional[float] = None
    roll: Optional[float] = None
    pitch: Optional[float] = None
    yaw: Optional[float] = None
    rssi: Optional[int] = None
    extra: dict = Field(default_factory=dict)

    @field_validator("ts")
    def make_aware(cls, value):
        if value.tzinfo is None:
            return value.replace(tzinfo=pytz.UTC)
        return value.astimezone(pytz.UTC)
