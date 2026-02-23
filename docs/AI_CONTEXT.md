# NetSentinel — AI Collaboration Context

## Project Purpose

NetSentinel is a learning project focused on understanding DevOps practices through AI-assisted development.

The primary goal is to learn DevOps by building and operating a real service with the help of AI coding tools.  
A secondary goal is to learn practical AI-coding workflows by collaborating with an AI engineering agent (Codex).

This project is intentionally educational-first:
learning and operational understanding are prioritized over feature velocity.

---

## Roles

### User (Project Owner / Tech Lead / Learner)

The user acts as:
- technical lead of the project,
- DevOps learner,
- system owner and operator.

Responsibilities:
- define direction and priorities,
- approve iterations,
- learn from implementation decisions,
- operate and observe the system in real environments.

The user is **not primarily writing code**, but managing an AI-driven engineering workflow.

---

### Codex (Engineering Team)

Codex acts as a full engineering team responsible for:

- implementing features,
- proposing iterations aligned with roadmap,
- performing code reviews,
- maintaining architectural consistency,
- following AGENTS.md workflow discipline.

Codex operates inside the repository context and owns implementation decisions within approved scope.

---

### ChatGPT (Meta Advisor / DevOps Guide)

ChatGPT acts as an external advisor helping the user:

- understand what Codex is doing,
- learn DevOps concepts,
- guide workflow and communication with Codex,
- prevent overengineering,
- maintain learning-oriented pacing.

ChatGPT operates outside repository implementation and focuses on strategy, learning, and process clarity.

---

## Development Philosophy

The project follows these principles:

- minimal iterative development
- avoid overengineering
- reliability before features
- deterministic behavior over complexity
- API-first thinking
- infrastructure introduced only when justified
- learning > speed

The goal is clarity and understanding, not rapid feature expansion.

---

## Workflow Model

Development follows an AI-assisted engineering workflow:

1. Codex operates via structured iterations.
2. Each new Codex session begins with `.codex/BOOTSTRAP.md`.
3. Iterations modify system capabilities.
4. Maintenance changes do not count as iterations.
5. ChatGPT provides meta-level guidance and learning support.

---

## Current Project Phase

The project has moved beyond initial MVP construction and entered the **Deployment & Operational Learning Phase**.

Current focus:

- containerizing the application (Docker),
- running locally in production-like conditions,
- deploying to a VPS,
- observing real runtime behavior,
- connecting real VPN nodes,
- evolving iterations based on operational insights.

The system is transitioning from "built software" to "operated service".

---

## Long-Term Direction

NetSentinel is intended to evolve into a small but realistic monitoring service used as a practical DevOps learning platform, including:

- deployment automation,
- runtime observability,
- reliability improvements,
- operational feedback-driven development.

The project emphasizes understanding real system lifecycle over building a feature-heavy product.