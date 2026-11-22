# Landlord

Monorepo:

- `backend/`: FastAPI + neonize (WhatsApp) API
- `frontend/`: React app (Vite + TypeScript)

## Run in development

Backend (http://127.0.0.1:8000):

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
