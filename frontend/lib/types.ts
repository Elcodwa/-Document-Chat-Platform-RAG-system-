export interface CurrentUser {
  id: string;
  tenant_id: string;
  email: string;
  full_name: string | null;
  is_tenant_admin: boolean;
  tenant_name: string | null;
}

export interface TokenResponse {
  access_token: string;
  refresh_token: string;
  token_type: string;
}

export interface DatabaseConnection {
  id: string;
  name: string;
  database_type: "postgresql" | "mysql";
  host: string | null;
  port: number | null;
  database_name: string | null;
  username: string | null;
  ssl_enabled: boolean;
  status: string;
  last_tested_at: string | null;
  last_test_message: string | null;
  schema_sync_status: string;
  last_schema_sync_at: string | null;
  is_active: boolean;
  created_at: string;
}

export interface DatabaseColumn {
  id: string;
  column_name: string;
  data_type: string;
  is_primary_key: boolean;
  is_foreign_key: boolean;
  referenced_table: string | null;
  referenced_column: string | null;
}

export interface DatabaseTable {
  id: string;
  schema_name: string;
  table_name: string;
  estimated_row_count: number | null;
  is_enabled: boolean;
  columns: DatabaseColumn[];
}

export interface ConnectionTestResult {
  success: boolean;
  message: string;
  server_version: string | null;
}

export interface SchemaSyncResult {
  table_count: number;
  column_count: number;
}

export interface KnowledgeBase {
  id: string;
  name: string;
  description: string | null;
  created_at: string;
  file_count: number;
}

export interface KbFile {
  id: string;
  knowledge_base_id: string | null;
  original_name: string;
  extension: string | null;
  file_size_bytes: number | null;
  processing_status: "pending" | "processing" | "completed" | "failed";
  processing_error: string | null;
  page_count: number | null;
  created_at: string;
}

export interface Conversation {
  id: string;
  title: string | null;
  status: string;
  active_connection_ids: string[];
  active_knowledge_base_ids: string[];
  created_at: string;
  updated_at: string;
  last_message_at: string | null;
}

export interface Citation {
  id: string;
  citation_type: "database" | "document";
  file_id: string | null;
  title: string | null;
  source_reference: string | null;
  page_number: number | null;
  relevance_score: number | null;
}

export interface ChatMessage {
  id: string;
  conversation_id: string;
  role: "user" | "assistant";
  content: string;
  detected_intent: "database" | "document" | "hybrid" | "general" | null;
  status: string;
  error_message: string | null;
  created_at: string;
  citations: Citation[];
}

export interface QueryExecutionDetail {
  id: string;
  connection_id: string;
  generated_sql: string;
  normalized_sql: string | null;
  validation_status: "passed" | "blocked";
  validation_errors: string[];
  referenced_tables: string[];
  execution_status: "success" | "error" | null;
  execution_time_ms: number | null;
  returned_row_count: number | null;
  result_preview: { columns: string[]; rows: Record<string, unknown>[] } | null;
  error_message: string | null;
}
