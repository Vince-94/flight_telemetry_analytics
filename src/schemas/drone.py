#!/usr/bin/env python3
from pydantic import BaseModel, Field


class DroneRequest(BaseModel):
    name: str = Field(..., min_length=1, max_length=64)


class DroneResponse(BaseModel):
    id: str
    name: str
    api_key: str   # only returned on creation

    @staticmethod
    def from_orm(drone) -> "DroneResponse":
        return DroneResponse(
            id=str(drone.id),
            name=drone.name,
            api_key=drone.api_key,
        )
