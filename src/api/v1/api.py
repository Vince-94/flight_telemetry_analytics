#!/usr/bin/env python3
from fastapi import APIRouter
from src.api.v1.drones import router as drones_router


router = APIRouter(prefix="/v1")

# Include routers (flights, telemetry, etc.)
router.include_router(drones_router)
