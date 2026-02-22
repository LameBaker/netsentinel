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

Iteration 1 baseline implemented.

Current backend capabilities:
- FastAPI application bootstrap
- `/health` endpoint with runtime metadata
- request logging middleware with request ID propagation
- domain models for `Node` and `ProbeResult`
- in-memory repository abstraction
- baseline pytest suite

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

4. Check health endpoint:

```bash
curl http://127.0.0.1:8000/health
```

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
