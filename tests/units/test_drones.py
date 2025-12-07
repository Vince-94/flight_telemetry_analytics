#!/usr/bin/env python3
# tests/test_drones.py
import pytest
from httpx import AsyncClient, ASGITransport

@pytest.mark.asyncio
async def test_register_drone(client: AsyncClient):
    response = await client.post("/v1/drones", json={"name": "Test Beast"})
    assert response.status_code == 201
    data = response.json()
    assert data["name"] == "Test Beast"
    assert "api_key" in data
    return data["api_key"]


@pytest.mark.asyncio
async def test_list_drones(client: AsyncClient):
    api_key = await test_register_drone(client)
    response = await client.get("/v1/drones", headers={"X-API-Key": api_key})
    assert response.status_code == 200
    assert len(response.json()) == 1