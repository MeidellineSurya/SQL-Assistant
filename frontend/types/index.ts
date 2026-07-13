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

export interface QueryHistoryItem {
  id: string;
  connection_id: string;
  natural_language: string;
  generated_sql: string;
  is_valid: boolean | null;
  was_executed: boolean;
  row_count: number | null;
  execution_ms: number | null;
  error_message: string | null;
  created_at: string;
}

export interface QueryHistoryPage {
  items: QueryHistoryItem[];
  next_cursor: string | null;
}

export interface ExecutionResult {
  columns: string[];
  rows: unknown[][];
  row_count: number;
  truncated: boolean;
}

export interface ExecuteResponse {
  history: QueryHistoryItem;
  result: ExecutionResult | null;
}

export type ChartType = "bar" | "line" | "pie" | "scatter" | "table";

export interface SuggestChartResponse {
  chart_type: ChartType;
  reasoning: string;
}

export interface ChartConfig {
  x_key: string;
  y_keys: string[];
}

export interface Chart {
  id: string;
  query_id: string;
  chart_type: ChartType;
  config_json: ChartConfig;
  created_at: string;
}
