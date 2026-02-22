# Project State

## Current Phase
Phase 1 - Monitoring MVP (Iteration 9 complete)

## System Status
Backend foundation is now operational.
Core monitoring flow runs automatically with reliability controls and hardened SQLite persistence behavior.

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
- SQLite retention policy per node (`NETSENTINEL_RESULT_RETENTION_PER_NODE`, deterministic keep-latest)
- localized repository error mapping for SQLite (`duplicate`, `unavailable`) with lock-retry guard
- duplicate node registration protection on SQLite with API response `409 Node already exists`
- fail-fast app startup on SQLite initialization errors with explicit runtime message
- health and metrics storage diagnostics (`storage`, `storage_path`, `last_repository_error`)
- SQLite schema versioning via `PRAGMA user_version` (`SCHEMA_VERSION=1`)
- linear startup migration path (`v0 -> v1`) with idempotent SQL
- fail-fast guard for unsupported future SQLite schema versions
- fail-fast guard for missing migration step definitions
- migration tests for fresh DB versioning, legacy upgrade, and future-version rejection
- optional inclusive time-window filters for `GET /results` (`from`, `to`) with stable existing params
- additive probe history summary endpoint `GET /results/summary` (`total_checks`, `up_checks`, `down_checks`, `availability_pct`, `avg_latency_ms`, `last_checked_at`)
- on-demand summary computation in both in-memory and SQLite repositories (no caching/background jobs)
- repository parity tests for summary behavior across storage backends

## Active Focus
Improve operator usefulness of stored probe history while preserving existing API contracts.

## Architecture Snapshot
Backend: FastAPI API with nodes/probes/results + scheduler control endpoints
Database: optional SQLite adapter (`memory` fallback retained)
Probes: synchronous TCP probe with automatic periodic execution

## Known Limitations
- Single-process in-memory state only
- No distributed scheduler coordination
- No archival/export strategy beyond retention trimming

## Next Iteration Goal
Add minimal history usability safeguards (request validation for time windows and deterministic defaults/documentation for history queries).

## Last Updated
Iteration 9 closed (history filters + summary endpoint + repository parity)
