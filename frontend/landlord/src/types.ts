// Shapes returned by the FastAPI backend (see backend/src/*/schemas.py).

export interface User {
  id: string;
  email: string;
  name: string;
  created_at: string;
}

export interface Account {
  id: string;
  jid: string | null;
  phone: string | null;
  push_name: string | null;
  business_name: string | null;
  platform: string | null;
  status: "connected" | "logged_out" | string;
  linked_at: string | null;
  last_connected_at: string | null;
}

export interface Group {
  jid: string;
  name: string;
  topic: string | null;
  owner_jid: string | null;
  participant_count: number;
  is_announce: boolean;
  is_locked: boolean;
  is_community: boolean;
  picture_url: string | null;
}

export interface Member {
  jid: string;
  phone: string | null;
  lid: string | null;
  saved_name: string | null;
  push_name: string | null;
  business_name: string | null;
  is_admin: boolean;
  is_super_admin: boolean;
  picture_url: string | null;
}
