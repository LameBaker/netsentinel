# NetSentinel

> AI-assisted VPN and network monitoring platform focused on detecting availability issues, routing degradation, and potential network blocking events.

---

![status](https://img.shields.io/badge/status-early--development-orange)
![ai](https://img.shields.io/badge/AI-assisted-blue)
![devops](https://img.shields.io/badge/DevOps-learning-informational)
![license](https://img.shields.io/badge/license-MIT-green)

---

## 🚀 Overview

NetSentinel is an experimental open-source project exploring **AI-driven software development** and **DevOps practices** through a real-world network monitoring system.

The project monitors VPN nodes and network connectivity to detect:

- availability issues
- latency degradation
- connectivity anomalies
- potential regional blocking events

This repository is intentionally developed with AI acting as a technical lead, guiding iterative improvements and architectural evolution.

---

## 🧠 Philosophy

NetSentinel is not just a monitoring tool.

It is an experiment in:

- AI-assisted engineering workflows
- repository-driven context
- iterative DevOps maturity
- autonomous development patterns

Human role:
- architecture decisions
- direction and validation

AI role:
- propose iterations
- implement changes
- review and improve system design

---

## 🗺️ Roadmap (High-Level)

- **Phase 1** — Monitoring MVP
- **Phase 2** — Operational maturity
- **Phase 3** — Intelligent network analysis

See `ROADMAP.md` for details.

---

## ⚙️ Project Status

Iteration 10 (local Docker runtime) completed.

Current runtime capabilities include:
- FastAPI monitoring API with in-process scheduler
- SQLite-backed persistence option with probe history and summary endpoint
- structured logs to stdout/stderr
- local container runtime via Dockerfile + docker-compose
- `/health`-based container healthcheck and persistent Docker volume for SQLite

For detailed operational state and iteration history, see `PROJECT_STATE.md`.

## 🛠️ Local Run

1. Create virtual environment:

```bash
python3 -m venv .venv
source .venv/bin/activate
```

2. Install dependencies:

```bash
python3 -m pip install -e ".[dev]"
```

3. Run API:

```bash
uvicorn app.main:app --reload
```

Optional: enable SQLite persistence (instead of in-memory storage):

```bash
export NETSENTINEL_STORAGE_BACKEND=sqlite
export NETSENTINEL_SQLITE_PATH=./netsentinel.sqlite3
uvicorn app.main:app --reload
```

4. Check health endpoint:

```bash
curl http://127.0.0.1:8000/health
```

## 🐳 Local Docker Run

1. Build and start:

```bash
docker compose up -d --build
```

2. Verify API is reachable:

```bash
curl http://127.0.0.1:8000/health
```

3. Verify scheduler state (running/degraded signals):

```bash
curl http://127.0.0.1:8000/scheduler/status
curl http://127.0.0.1:8000/metrics
```

Operator note:
- `GET /health` confirms API/process liveness.
- Scheduler issues are treated as degraded state; check `/metrics` scheduler fields (`failed_cycles`, `consecutive_failures`).

4. Verify SQLite persistence via Docker volume:

```bash
# create data (example: register node)
curl -X POST http://127.0.0.1:8000/nodes \
  -H "Content-Type: application/json" \
  -d '{"name":"docker-node","host":"127.0.0.1","port":443,"region":"us","enabled":true}'

# restart container and confirm node still exists
docker compose restart netsentinel
curl http://127.0.0.1:8000/nodes

# recreate container and confirm data still exists (volume kept)
docker compose up -d --force-recreate
curl http://127.0.0.1:8000/nodes
```

5. View runtime logs (stdout/stderr):

```bash
docker compose logs -f netsentinel
```

Data survives restart/re-create while `netsentinel_data` volume exists.
`docker compose down -v` removes the volume and deletes persisted SQLite data.

## ✅ Testing

Run test suite:

```bash
pytest
```

---

## 🤖 AI Development Model

This project uses repository-based context files:

- `AGENTS.md` — AI operating rules
- `PROJECT_CONTEXT.md` — project intent
- `PROJECT_STATE.md` — current system memory
- `ROADMAP.md` — long-term direction

AI agents read these files to maintain continuity across sessions.

---

## 📜 License

MIT
