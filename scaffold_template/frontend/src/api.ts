import type { User } from "./types";

const TOKEN_KEY = "__PROJECT_SLUG__.token";

export const tokenStore = {
  get(): string | null {
    try {
      return localStorage.getItem(TOKEN_KEY);
    } catch {
      return null;
    }
  },
  set(token: string) {
    try {
      localStorage.setItem(TOKEN_KEY, token);
    } catch {
      /* storage unavailable: token lives only for this page load */
    }
  },
  clear() {
    try {
      localStorage.removeItem(TOKEN_KEY);
    } catch {
      /* ignore */
    }
  },
};

export class ApiError extends Error {
  constructor(public status: number, message: string) {
    super(message);
  }
}

let onUnauthorized: (() => void) | null = null;
/** Called when a request with a token gets 401 (expired / invalid token). */
export function setOnUnauthorized(fn: () => void) {
  onUnauthorized = fn;
}

async function errorMessage(res: Response): Promise<string> {
  try {
    const data = await res.json();
    if (typeof data.detail === "string") return data.detail;
    if (Array.isArray(data.detail)) return data.detail.map((d: { msg: string }) => d.msg).join(", ");
  } catch {
    /* not JSON */
  }
  return res.statusText || `Request failed (${res.status})`;
}

async function request(path: string, init: RequestInit = {}): Promise<Response> {
  const token = tokenStore.get();
  const headers = new Headers(init.headers);
  if (token) headers.set("Authorization", `Bearer ${token}`);
  if (init.body && !headers.has("Content-Type")) headers.set("Content-Type", "application/json");

  const res = await fetch(`/api${path}`, { ...init, headers });
  if (!res.ok) {
    if (res.status === 401 && token) onUnauthorized?.();
    throw new ApiError(res.status, await errorMessage(res));
  }
  return res;
}

const json = async <T>(path: string, init?: RequestInit) => (await request(path, init)).json() as Promise<T>;

export const api = {
  signup: (body: { name: string; email: string; password: string }) =>
    json<User>("/auth/signup", { method: "POST", body: JSON.stringify(body) }),
  signin: (body: { email: string; password: string }) =>
    json<{ access_token: string; token_type: string }>("/auth/signin", {
      method: "POST",
      body: JSON.stringify(body),
    }),
  me: () => json<User>("/auth/me"),
};
