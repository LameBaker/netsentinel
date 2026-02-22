# Current Iteration

Goal:
Introduce persistent storage behind existing monitoring API contracts.

Tasks:
- add repository adapter for persistent node/result storage
- keep `POST /nodes`, `GET /nodes`, `POST /probes/run`, `GET /results` contracts unchanged
- add migration/bootstrap for local dev storage
- add tests for storage-backed node/probe/result flow
