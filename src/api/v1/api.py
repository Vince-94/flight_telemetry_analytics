#!/usr/bin/env python3
from fastapi import APIRouter

from src.api.v1.drones import router as drones_router
from src.api.v1.telemetry import router as telemetry_router
from src.api.v1.flight import router as flight_router


router = APIRouter(prefix="/v1")

# Include routers
router.include_router(drones_router)
router.include_router(telemetry_router)
router.include_router(flight_router)
