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

export interface Connection {
  id: string;
  name: string;
  host: string;
  port: number;
  database_name: string;
  username: string;
  ssl_mode: string;
  schema_cached_at: string | null;
  created_at: string;
}

export interface ConnectionCreateInput {
  name: string;
  host: string;
  port: number;
  database_name: string;
  username: string;
  password: string;
  ssl_mode: string;
}

export interface ConnectionTestResult {
  success: boolean;
  latency_ms: number | null;
  error: string | null;
}

export interface SchemaColumn {
  name: string;
  data_type: string;
  is_nullable: boolean;
}

export interface SchemaTable {
  name: string;
  columns: SchemaColumn[];
}

export interface SchemaCacheResponse {
  schema_cache: { tables: SchemaTable[] } | null;
  schema_cached_at: string | null;
}
