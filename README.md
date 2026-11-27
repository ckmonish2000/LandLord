# Landlord

Monorepo:

- `backend/`: FastAPI + neonize (WhatsApp) API
- `frontend/`: React app (Vite + TypeScript)

## Run in development

Backend (http://127.0.0.1:8000):

```sh
cd backend
cp .env.example .env   # then set AUTH_SECRET; start LM Studio's server for Alfred
uv sync
uv run fastapi dev src/main.py
```

Frontend (http://localhost:5173):

```sh
cd frontend
npm install
npm run dev
```

The frontend calls `/api/*`; Vite forwards those requests to the backend on port 8000.

## Code quality (backend)

[Ruff](https://docs.astral.sh/ruff/) lints and formats the Python code (like ESLint + Prettier). Settings are in `backend/pyproject.toml`.

```sh
cd backend
uv run ruff check .          # lint
uv run ruff check . --fix    # lint and auto-fix what it can
uv run ruff format .         # format
```

In VS Code, install the Ruff extension and turn on format on save.
