# Practices

How this codebase is laid out and the rules it follows. Read this before adding code.
New projects can start from the same layout with `scaffold_project.py` on the `mk/helpers` branch.

## 1. Repository layout

```
<project>/
├── PRACTICES.md          this file
├── README.md             how to run it
├── .gitignore            .env, data/, node_modules/, build output
├── backend/              FastAPI (Python 3.13, uv)
│   ├── pyproject.toml    dependencies + Ruff settings
│   ├── .env.example      every setting, documented; copy to .env
│   ├── data/             local data (database files). Never committed
│   ├── src/              the application
│   └── tests/            mirrors src/
└── frontend/             React + Vite + TypeScript
```

One repo, two apps. The frontend calls the backend at `/api/*`; Vite forwards those requests in development.

## 2. Backend: one folder per entity

Every entity (users, properties, bills…) is a folder in `src/` with the same files. Only create the files you need.

| File | Holds | Rule |
|---|---|---|
| `router.py` | HTTP endpoints | Thin: parse input, call the service, map errors to HTTP codes |
| `service.py` | Business logic | All decisions live here. No HTTP, no FastAPI imports |
| `repository.py` | Reading and writing storage | No business rules. One repository per table / collection |
| `models.py` | Database tables (when using an ORM) | Storage shape only |
| `schemas.py` | Request / response shapes (pydantic) | What crosses the API boundary |
| `dependencies.py` | Builds services with their repositories | The only place objects are wired together |
| `exceptions.py` | The entity's errors (`EmailTaken`, `PropertyNotFound`) | Plain classes, raised by the service |
| `constants.py` | Fixed values and limits | No magic numbers in code |
| `config.py` | Settings read from `.env` | One `BaseSettings` class per module |
| `utils.py` | Small pure helpers | No I/O, easy to test |

Shared files at `src/` level: `main.py` (app + lifespan), `config.py` (global settings), `database.py` (storage setup), `utils.py` (helpers like `now_iso()`).

## 3. Who may call whom

```
HTTP      → router → service → repository → storage
Channel   → worker → agent  → tools → service → repository
                        └→ Channel interface (to send messages)
```

- **Routers never touch repositories.** They go through a service.
- **Services never import FastAPI.** They raise their own exceptions; the router turns them into HTTP errors.
- **Agents never import channel code (WhatsApp…) or services.** They use `src/tools/` and the `Channel` interface in `agents/base.py`. `tools/` is the full list of what an agent may do.
- **Logic belongs to the entity's service.** A tool is a thin wrapper; matching, filtering and formatting rules live in the service or the entity's `utils.py`.
- **Wiring happens in `dependencies.py`.** If two modules would import each other, import inside the function there and leave a comment saying why.

## 4. Errors

- Services raise the entity's own exceptions (`raise PropertyNotFound()`).
- Routers map them to HTTP codes and keep the cause: `raise HTTPException(404, "Property not found") from e`.
- Repeated mappings get one shared helper (e.g. `whatsapp/router/errors.py` → `whatsapp_http_errors()`).
- Code that must never break the main flow (sending a reaction, a log line) catches, logs and moves on, and says so in its docstring: "Never raises."

## 5. Data rules

- **Time:** UTC, stored as ISO 8601 strings or timezone aware datetimes. Use the helper in `src/utils.py` (`now_iso()` / `utc_now()`), never `datetime.now()` without a timezone.
- **Money:** integers in the smallest unit (paise). Split with integer maths so shares always add up.
- **Ids:** UUID strings.
- **Secrets and local data** live in `backend/.env` and `backend/data/`, both git ignored. `.env.example` lists every setting with a comment.
- **Settings:** each module has a `config.py` reading `backend/.env`; empty values count as unset (`env_ignore_empty=True`).

## 6. State and long lived objects

- Objects that hold live state (thread pools, timers, connections) are created once per process: cache the factory in `dependencies.py` with `@lru_cache`.
- Keep that state on instances, not module globals, so it can be replaced in tests.
- Never block an event thread (WhatsApp callbacks, request handlers): hand slow work to a worker's thread pool.

## 7. Agents (LangGraph)

```
src/agents/
├── base.py         contracts: Channel, AgentContext, AgentResult, Waiting, answers
├── runner.py       start / resume runs, keeps the conversation record
├── repository.py   conversation records
├── checkpoint.py   saved graph state (SQLite)
├── <agent>/        a top level agent: agent.py (start/resume) + graph.py
└── <sub_agent>/    a sub-agent used as a node: graph.py, state.py, prompts.py,
                    schemas.py, messages.py, extract.py, utils.py, constants.py
```

- **One front door:** only the top level agent (Alfred) has `agent.py`. Sub-agents are graphs added as nodes.
- **The LLM decides what; code does it.** The LLM extracts and classifies (structured output with a pydantic schema). Matching, maths and sending are plain code.
- **LLM access only through `get_llm()`** in `src/llm/`. Agents never create clients.
- **Asking the user is two nodes:** `ask_*` sends the question and stores its message ids in `waiting`; `wait_*` calls `interrupt()`. On resume LangGraph re-runs the paused node, so sending must not be in it.
- **State vs context:** state (`TypedDict`) is the conversation's data and is saved while paused. Context (`AgentContext`) is per run tools such as the channel; it is never saved.
- **All user facing text** of an agent lives in its `messages.py`; prompts live in `prompts.py`.

## 8. Workers

One sub-package per channel, each with the same files:

```
src/workers/<channel>/
├── worker.py      the worker class
├── constants.py   settings and fixed texts
├── schemas.py     data passed around inside it
└── utils.py       small helpers
```

A helper used by two workers moves up to `src/workers/utils.py`.

## 9. Code style

- **Ruff** for lint and format (`uv run ruff check . --fix`, `uv run ruff format .`). Settings in `pyproject.toml`; line length 120.
- **Type hints** on every function signature.
- **Docstrings say why**, not what the next line does. A module docstring explains the module's job and, for flows, draws the flow.
- **Names say what a thing is**: `find_by_name`, `list_member_contacts`, `mark_member_notified`. Booleans read as questions: `is_owner`, `lives_here`.
- **Small functions, early returns**, no nested `if` pyramids.
- **No dead code.** Delete it; git remembers.

## 10. Tests

- `backend/tests/` mirrors `src/` (`tests/auth/test_auth.py` tests `src/auth/`).
- Test through the public surface: HTTP routes with FastAPI's `TestClient`, services directly.
- Fake at the boundaries: a fake `Channel`, fake tools, a fake LLM. Never call real WhatsApp or a paid API in tests.
- Each test uses its own temporary data directory or database.

## 11. Frontend

```
frontend/src/
├── main.tsx, App.tsx     entry and routes
├── api.ts                the only place that calls the backend; one function per endpoint
├── auth.tsx              signed in user + token handling
├── types.ts              mirrors the backend's schemas
├── pages/                one file per route
├── components/           reusable pieces
└── styles.css            design tokens on :root, then components
```

- Colours, spacing and radii are tokens in `styles.css`; components never hard code them.
- Every screen handles loading (skeletons), empty, and error states.
- Icons come from Phosphor via `components/Icons.tsx`, so the app uses one icon set.

## 12. Git

- Never commit `.env`, `backend/data/`, session or database files. If one slips in, remove it from history, not just from the latest commit.
- One change per commit, with a short message: `feat: …`, `fix: …`, `chore: …`.
- Run Ruff before committing.

## Checklists

**New entity**
1. `src/<entity>/` with `models.py` / `repository.py`, `service.py`, `schemas.py`, `exceptions.py`, `router.py`, `dependencies.py`.
2. Include the router in `src/main.py`.
3. Types in `frontend/src/types.ts`, calls in `frontend/src/api.ts`.
4. Tests in `tests/<entity>/`.

**New agent capability**
1. Logic in the entity's service; a thin wrapper in `src/tools/`.
2. A sub-agent folder with `graph.py`; add a `Route` value and a node in Alfred's graph; describe it in the router prompt.
3. Wording in `messages.py`; tests with a fake channel and a fake LLM.
