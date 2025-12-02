# Flight Telemetry Analytics Platform

- [Flight Telemetry Analytics Platform](#flight-telemetry-analytics-platform)
  - [Overview](#overview)
  - [Setup](#setup)
    - [Dependencies](#dependencies)
    - [Start application](#start-application)
    - [Endpoints](#endpoints)
  - [Core Features \& Functional Requirements](#core-features--functional-requirements)
    - [1. Telemetry Ingestion](#1-telemetry-ingestion)
    - [2. Storage (PostgreSQL + SQLAlchemy 2.0)](#2-storage-postgresql--sqlalchemy-20)
    - [3. Real-Time Layer (Redis)](#3-real-time-layer-redis)
    - [4. Post-Flight Analytics Engine (Pandas + NumPy)](#4-post-flight-analytics-engine-pandas--numpy)
      - [Energy \& Power](#energy--power)
      - [Stability \& Smoothness](#stability--smoothness)
      - [Pilot Style Fingerprint](#pilot-style-fingerprint)
    - [5. Observability (OpenTelemetry)](#5-observability-opentelemetry)
    - [6. Minimum Viable API](#6-minimum-viable-api)
  - [Tech Stack (Required)](#tech-stack-required)


## Overview
Flight telemetry ingestion and analytics platform that receives real-time flight data from drones (or any flight controller), stores it efficiently, automatically detects flight sessions, and computes advanced post-flight metrics focused on energy efficiency, flight stability, and pilot style fingerprinting.

---

## Setup

### Dependencies
```sh
# Create virtual env
python3 -m venv venv
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

```

### Start application
1. Start PostgreSQL and redis docker containers:
    ```sh
    docker-compose up -d
    ```
2. Update tables every time you change models during early dev:
    ```sh
    python3 -m src.db.init_db
    ```
3. Start application:
    ```sh
    uvicorn src.main:app --reload
    ```

### Endpoints
- [GET] Health
    ```sh
    curl -X GET http://127.0.0.1:8000/health | python3 -m json.tool | pygmentize -l json
    ```
- [POST] Register new drone
    ```sh
    curl -X POST http://127.0.0.1:8000/v1/drones/ -H "Content-Type: application/json" -d '{"name": "DRONE_NAME"}'
    ```
- [GET] Get the list of drones of the user
    ```sh
    curl -X GET http://127.0.0.1:8000/v1/drones/ -H "X-API-Key: API_KEY" | python3 -m json.tool | pygmentize -l json
    ```
- [GET] Get a specific drone of an user
    ```sh
    curl -X GET http://127.0.0.1:8000/v1/drones/{id}/ -H "X-API-Key: API_KEY" | python3 -m json.tool | pygmentize -l json
    ```
- [POST] Send telemetry
    ```sh
    curl -X POST http://127.0.0.1:8000/v1/telemetry/ -H "X-API-Key: API_KEY" -H "Content-Type: application/json" -d '[{"ts": "2025-12-01T12:00:00Z", "throttle": 0.65, "voltage": 16.8, "current": 45.2, "mah_drawn": 1234}, {"ts": "2025-12-01T12:00:01Z", "throttle": 0.78, "voltage": 16.5, "current": 68.1}]'
    ```
- [GET] Get last telemetry
    ```sh
    curl -X GET http://127.0.0.1:8000/v1/telemetry/live/ -H "X-API-Key: API_KEY" | python3 -m json.tool | pygmentize -l json
    ```

TODO:
- [GET] Get registered drones
    ```sh
    curl -X GET http://127.0.0.1:8000/v1/all_drones
    ```
- [WS] Real-Time streaming
    ```sh
    curl http://127.0.0.1:8000/v1/telemetry/ws/ -H "X-API-Key: API_KEY"
    ```
- [GET] List flights (paginated)
    ```sh
    curl -X GET http://127.0.0.1:8000/v1/drones/{id}/flights/ -H "X-API-Key: API_KEY"
    ```
- [GET] Full flight + raw + analytics
    ```sh
    curl -X GET http://127.0.0.1:8000/v1/flights/{id}/ -H "X-API-Key: API_KEY"
    ```
- [POST] Force recompute analytics
    ```sh
    curl -X POST http://127.0.0.1:8000/v1/flights/{id}/recompute/ -H "X-API-Key: API_KEY"
    ```

---

## Core Features & Functional Requirements

### 1. Telemetry Ingestion
- Async FastAPI endpoints:
  - `POST /telemetry` (bulk JSON packets)
  - `WS /telemetry/ws` (real-time streaming)
- Support at least one protocol (MSP, CRSF, or custom JSON). Bonus for multiple.
- Per-drone authentication (API-Key or JWT)
- Schema validation with Pydantic v2
- Rate-limiting & deduplication

### 2. Storage (PostgreSQL + SQLAlchemy 2.0)
| Table           | Key Fields                                                                                                                              |
| --------------- | --------------------------------------------------------------------------------------------------------------------------------------- |
| `drones`        | id, name, owner, api_key                                                                                                                |
| `telemetry_raw` | id, drone_id, timestamp, position[x,y,z], velocity[x,y,z], attitude[roll,pitch,yaw], throttle, voltage, current, mah_drawn, rsssi, etc. |
| `flights`       | id, drone_id, start_ts, end_ts, total_mah, duration_s, bbox, computed_metrics (JSONB)                                                   |

- Automatic flight detection: new flight when throttle > 5 % for ≥ 3 s after idle

### 3. Real-Time Layer (Redis)
- Store latest telemetry packet per drone (key: `drone:{id}:live`)
- Expire after 30 s of inactivity
- Optional Redis Pub/Sub for pushing live updates to frontend

### 4. Post-Flight Analytics Engine (Pandas + NumPy)
Triggered on flight end or manually. Results stored in `flights.computed_metrics`.

#### Energy & Power
- Total energy used (mAh & Wh)
- Average / peak power (W)
- Wh per km (efficiency score)
- Voltage sag curve under load
- Throttle → power regression

#### Stability & Smoothness
- Roll/pitch/yaw rate STD & max
- Vibration score (high-freq accel if present)
- Throttle smoothness (jerk metric)
- Oscillation/phasing detection

#### Pilot Style Fingerprint
- Average throttle position
- 0→100 % throttle time (aggressiveness)
- Yaw authority vs forward speed
- Freestyle vs Racing score (heuristic)

### 5. Observability (OpenTelemetry)
- Auto-instrument FastAPI, SQLAlchemy, Redis
- Traces → Jaeger/Tempo
- Metrics → Prometheus (ingestion rate, processing latency, errors)
- Structured JSON logging

### 6. Minimum Viable API
| Method | Endpoint               | Description             |
| ------ | ---------------------- | ----------------------- |
| GET    | `/drones`              | List registered drones  |
| GET    | `/drones/{id}/flights` | List flights            |
| GET    | `/flights/{id}`        | Full flight + analytics |
| GET    | `/drones/{id}/live`    | Latest cached telemetry |
| POST   | `/telemetry`           | Ingest packet(s)        |
| WS     | `/telemetry/ws`        | Streaming endpoint      |

---

## Tech Stack (Required)
- **Backend:** FastAPI (Python 3.11+)
- **ORM:** SQLAlchemy 2.0+ (async)
- **Database:** PostgreSQL 15+
- **Time-series processing:** Pandas + NumPy
- **Cache & Queue:** Redis
- **Observability:** OpenTelemetry (tracing + metrics)
- **Validation:** Pydantic v2
- **Migrations:** Alembic
