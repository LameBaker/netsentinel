# Iteration 1 Backend Foundation Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Build a minimal FastAPI backend foundation with health endpoint, core schemas, in-memory storage abstraction, structured logging, and baseline tests.

**Architecture:** Keep a thin HTTP layer in `app/api`, domain contracts in `app/domain`, and storage behind an interface in `app/storage`. Use an application factory in `app/main.py` to centralize middleware and routes. Keep persistence in-memory for MVP but isolate it behind a protocol to avoid lock-in.

**Tech Stack:** Python 3.11+, FastAPI, Uvicorn, Pydantic v2, pytest, httpx

---

### Task 1: Scaffold project structure and dependencies

**Files:**
- Create: `pyproject.toml`
- Create: `app/__init__.py`
- Create: `app/main.py`
- Create: `app/api/__init__.py`
- Create: `app/api/health.py`
- Create: `app/domain/__init__.py`
- Create: `app/domain/models.py`
- Create: `app/storage/__init__.py`
- Create: `app/storage/repository.py`
- Create: `tests/__init__.py`

**Step 1: Create failing test for app startup contract**
- Write test expecting app factory and health route presence.

**Step 2: Run test to verify failure**
- Run: `pytest tests/test_health.py::test_health_endpoint_contract -v`

**Step 3: Add minimal project files and app factory**
- Add dependency metadata and app skeleton.

**Step 4: Run test to verify pass**
- Run same test command; expect PASS.

### Task 2: Implement health contract and structured logging middleware

**Files:**
- Modify: `app/main.py`
- Modify: `app/api/health.py`
- Create: `app/core/__init__.py`
- Create: `app/core/logging.py`
- Create: `tests/test_logging.py`

**Step 1: Write failing tests**
- Health response must include: `status`, `service`, `version`, `timestamp`, `uptime_s`.
- Middleware should attach request id and return `X-Request-ID` response header.

**Step 2: Run tests to verify failure**
- Run health and logging tests individually.

**Step 3: Implement minimal code**
- Track process start time.
- Return required health fields.
- Add HTTP middleware with request-id + duration logging.

**Step 4: Run tests to verify pass**
- Run both tests; expect PASS.

### Task 3: Define domain schemas and storage abstraction

**Files:**
- Modify: `app/domain/models.py`
- Modify: `app/storage/repository.py`
- Create: `tests/test_models.py`

**Step 1: Write failing schema validation tests**
- Validate Node required fields and port ranges.
- Validate ProbeResult latency and status constraints.

**Step 2: Run tests to verify failure**
- Run model tests only.

**Step 3: Implement minimal schema and repository interface**
- Add Pydantic models and a repository protocol with in-memory implementation.

**Step 4: Run tests to verify pass**
- Run model tests; expect PASS.

### Task 4: Documentation and operational memory update

**Files:**
- Modify: `README.md`
- Modify: `PROJECT_STATE.md`

**Step 1: Update README run/test instructions**
- Include install, run, and test commands.

**Step 2: Update project operational state**
- Reflect new implemented capabilities and next iteration.

**Step 3: Final verification**
- Run: `pytest -q`
- Confirm all tests pass.
