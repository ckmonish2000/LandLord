// Shapes returned by the FastAPI backend (see backend/src/*/schemas.py).

export interface User {
  id: string;
  email: string;
  name: string;
  created_at: string;
}
