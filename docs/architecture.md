# Architecture Overview

## Current Baseline (Iteration 1)

- `app/main.py`: application factory, middleware wiring, and route registration.
- `app/api/health.py`: system health route (`GET /health`).
- `app/domain/models.py`: core domain contracts (`Node`, `ProbeResult`).
- `app/storage/repository.py`: storage boundary (`Repository` protocol) and in-memory implementation.
- `app/core/logging.py`: shared logging configuration for request observability.

## Runtime Flow

1. API request enters FastAPI app.
2. HTTP middleware assigns or propagates `X-Request-ID`.
3. Request is processed by route handler.
4. Middleware records structured request completion log and response duration.

## Design Constraints

- MVP simplicity: in-memory storage only.
- Replaceability: storage interactions go through repository contract.
- Operational clarity: health endpoint and request-level logging available from first iteration.
