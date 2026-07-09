export interface User {
  id: string;
  email: string;
  created_at: string;
  is_active: boolean;
}

export interface TokenResponse {
  access_token: string;
  refresh_token: string;
  token_type: string;
}

export interface ApiErrorBody {
  detail: string;
}
