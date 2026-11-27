# __PROJECT_NAME__

Monorepo:

- `backend/`: FastAPI + SQLAlchemy (SQLite by default)
- `frontend/`: React app (Vite + TypeScript)

How the code is organised and the rules it follows: [PRACTICES.md](PRACTICES.md).

## Run in development

Backend (http://127.0.0.1:8000, API docs at /docs):

```sh
cd backend
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

## Settings

`backend/.env` holds local settings (it is git ignored). `backend/.env.example` lists every setting.

## Tests and code quality (backend)

```sh
cd backend
uv run pytest                # tests
uv run ruff check . --fix    # lint
uv run ruff format .         # format
```
