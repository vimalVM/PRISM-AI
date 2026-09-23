import { Clearance } from './auth';

export interface KBDocument {
  id: string;
  doc_id: string;
  filename: string;
  version: string;
  classification: Clearance;
  sha256: string;
  status: string;
  chunks: number;
  uploaded_by: string;
  ingested_at: string;
}

export interface KBSearchResult {
  doc_id: string;
  filename: string;
  version: string;
  chunk_index: number;
  score: number;
  content: string;
  classification: Clearance;
  page?: number;
  section?: string;
}

export interface ModelEntry {
  model: string;
  provider: string;
  enabled: boolean;
  capabilities: string[];
  present_locally: boolean;
}

export interface ModelsStatusResponse {
  ollama_connected: boolean;
  ollama_base_url: string;
  current_loaded_model: string | null;
  swap_status: Record<string, any>;
  models: Record<string, ModelEntry>;
  embeddings: {
    model: string;
    dimension: number;
  };
  ocr: {
    engine: string;
    lang: string;
  };
  routing_rules: string[];
}

export interface AuditEvent {
  id: number;
  ts: string;
  run_id?: string | null;
  user_id?: string | null;
  role?: string | null;
  event_type: string;
  model?: string | null;
  tool?: string | null;
  file_ids?: string[] | null;
  status: string;
  duration_ms?: number | null;
  details?: Record<string, any> | null;
  prev_hash?: string | null;
  hash: string;
}

export interface SystemStatus {
  app_host: string;
  app_port: number;
  offline: boolean;
  ollama_connected: boolean;
  active_model: string | null;
  non_loopback_connections: number;
  egress_scan_clean: boolean;
}
