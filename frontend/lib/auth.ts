import type { TokenResponse } from "@/types";

const ACCESS_KEY = "sql_assistant_access_token";
const REFRESH_KEY = "sql_assistant_refresh_token";

// Middleware can't read localStorage (it runs at the edge, before the page
// loads), so we also drop a plain, non-sensitive cookie whose only job is to
// tell middleware "a session exists" for redirect purposes. It carries no
// secret and is not what actually authorizes API calls — the backend is the
// only thing that verifies the real JWTs, sent as Authorization headers.
const SESSION_FLAG_COOKIE = "has_session";

export function storeTokens(tokens: TokenResponse): void {
  localStorage.setItem(ACCESS_KEY, tokens.access_token);
  localStorage.setItem(REFRESH_KEY, tokens.refresh_token);
  document.cookie = `${SESSION_FLAG_COOKIE}=1; path=/; max-age=${60 * 60 * 24 * 30}; samesite=lax`;
}

export function getAccessToken(): string | null {
  return localStorage.getItem(ACCESS_KEY);
}

export function getRefreshToken(): string | null {
  return localStorage.getItem(REFRESH_KEY);
}

export function clearTokens(): void {
  localStorage.removeItem(ACCESS_KEY);
  localStorage.removeItem(REFRESH_KEY);
  document.cookie = `${SESSION_FLAG_COOKIE}=; path=/; max-age=0`;
}
