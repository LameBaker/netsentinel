# Project State

## Current Phase
Phase 1 - Monitoring MVP (Iteration 6 complete)

## System Status
Backend foundation is now operational.
Core monitoring flow runs automatically with reliability controls and persistent storage option.

## Implemented Capabilities
- project structure
- AI workflow configuration
- documentation baseline
- FastAPI application factory
- health endpoint with uptime and service metadata
- structured request logging middleware with X-Request-ID propagation
- global fallback error handler returning request-correlated 500 responses
- context-safe logger formatting isolated to NetSentinel logger namespace
- domain models for Node, RegisteredNode, ProbeResult, and probe run contract
- in-memory repository abstraction with node lookup, enabled-node selection, and result limiting
- node registration and listing endpoints (`POST /nodes`, `GET /nodes`)
- probe execution endpoint (`POST /probes/run`) for one node or all enabled nodes
- result retrieval endpoint (`GET /results`) with `node_id` and `limit` filters (latest by `checked_at`)
- TCP probe service for availability and latency measurement with timeout classification
- in-process monitoring scheduler loop with startup/shutdown lifecycle control
- scheduler control endpoints (`GET /scheduler/status`, `POST /scheduler/run-once`)
- scheduler safety controls (fast stop via cancel, serialized run cycle, validated env parsing)
- deterministic probe retry support (`probe_retry_count`, immediate retry only)
- scheduler reliability metrics (`successful_cycles`, `failed_cycles`, `consecutive_failures`, `last_cycle_duration_ms`)
- internal metrics endpoint (`GET /metrics`) for runtime counters and scheduler health
- structured scheduler cycle logs (`cycle_start`, `cycle_complete`, `cycle_failed`) with cycle fields
- guardrails for runtime config (`probe_retry_count` clamp, scheduler/timeout safe minimums)
- integration tests for core monitoring flow, scheduler behavior, observability, reliability metrics, retry, and timeout handling
- SQLite repository adapter (synchronous `sqlite3`, single-process safe access)
- storage backend selection via env (`memory` or `sqlite`)
- startup schema bootstrap for SQLite without external migration framework
- efficient metrics counting via repository `count_probe_results()`
- persistence tests validating data survives app restart on SQLite backend

## Active Focus
Stabilize SQLite-backed operation while preserving existing API contracts.

## Architecture Snapshot
Backend: FastAPI API with nodes/probes/results + scheduler control endpoints
Database: optional SQLite adapter (`memory` fallback retained)
Probes: synchronous TCP probe with automatic periodic execution

## Known Limitations
- Single-process in-memory state only
- No distributed scheduler coordination
- SQLite schema migration/versioning strategy not implemented yet

## Next Iteration Goal
Harden persistent storage operations and observability for long-running single-process deployments.

## Last Updated
Iteration 6 closed
