import type {
  ApiErrorBody,
  Connection,
  ConnectionCreateInput,
  ConnectionTestResult,
  SchemaCacheResponse,
  TokenResponse,
  User,
} from "@/types";
import { clearTokens, getAccessToken, getRefreshToken, storeTokens } from "@/lib/auth";

const API_BASE = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";

export class ApiError extends Error {
  constructor(
    public status: number,
    message: string,
  ) {
    super(message);
  }
}

async function refreshAccessToken(): Promise<boolean> {
  const refreshToken = getRefreshToken();
  if (!refreshToken) return false;

  const res = await fetch(`${API_BASE}/api/v1/auth/refresh`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ refresh_token: refreshToken }),
  });
  if (!res.ok) return false;

  storeTokens((await res.json()) as TokenResponse);
  return true;
}

async function request<T>(path: string, options: RequestInit = {}, retry = true): Promise<T> {
  const accessToken = getAccessToken();

  const res = await fetch(`${API_BASE}${path}`, {
    ...options,
    headers: {
      "Content-Type": "application/json",
      ...(accessToken ? { Authorization: `Bearer ${accessToken}` } : {}),
      ...options.headers,
    },
  });

  if (res.status === 401 && retry && (await refreshAccessToken())) {
    return request<T>(path, options, false);
  }

  if (res.status === 401) {
    clearTokens();
  }

  if (!res.ok) {
    const body = (await res.json().catch(() => ({ detail: res.statusText }))) as ApiErrorBody;
    throw new ApiError(res.status, body.detail);
  }

  if (res.status === 204) return undefined as T;
  return (await res.json()) as T;
}

export const api = {
  register: (email: string, password: string) =>
    request<User>("/api/v1/auth/register", {
      method: "POST",
      body: JSON.stringify({ email, password }),
    }),

  login: (email: string, password: string) =>
    request<TokenResponse>("/api/v1/auth/login", {
      method: "POST",
      body: JSON.stringify({ email, password }),
    }),

  me: () => request<User>("/api/v1/auth/me"),

  logout: (refreshToken: string) =>
    request<void>("/api/v1/auth/logout", {
      method: "POST",
      body: JSON.stringify({ refresh_token: refreshToken }),
    }),

  listConnections: () => request<Connection[]>("/api/v1/connections"),

  createConnection: (input: ConnectionCreateInput) =>
    request<Connection>("/api/v1/connections", {
      method: "POST",
      body: JSON.stringify(input),
    }),

  deleteConnection: (id: string) =>
    request<void>(`/api/v1/connections/${id}`, { method: "DELETE" }),

  testConnection: (id: string) =>
    request<ConnectionTestResult>(`/api/v1/connections/${id}/test`, { method: "POST" }),

  refreshConnectionSchema: (id: string) =>
    request<SchemaCacheResponse>(`/api/v1/connections/${id}/schema`, { method: "POST" }),
};
