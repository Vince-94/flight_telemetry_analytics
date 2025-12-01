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

# Every time you change models during early dev
python -m src.db.init_db
```

### Start application
1. Start PostgreSQL docker container:
    ```sh
    docker run -d --name pg-drone -e POSTGRES_PASSWORD=postgres -e POSTGRES_DB=dronedb -p 5432:5432 postgres:15
    ```
2. Start application:
    ```sh
    uvicorn src.main:app --reload
    ```

### Endpoints
- Health
    ```sh
    http://127.0.0.1:8000/health
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
