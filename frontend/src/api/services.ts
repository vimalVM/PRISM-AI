import { apiRequest } from './client';
import { KBDocument, KBSearchResult, ModelsStatusResponse, AuditEvent, SystemStatus } from '../types/system';
import { Clearance } from '../types/auth';

// KB APIs
export async function getKBDocuments(): Promise<KBDocument[]> {
  const data = await apiRequest<{ documents: KBDocument[] }>('/kb/documents');
  return data.documents || [];
}

export async function uploadKBDocument(file: File, classification: Clearance, version: string = '1.0'): Promise<KBDocument> {
  const formData = new FormData();
  formData.append('file', file);
  formData.append('classification', classification);
  formData.append('version', version);
  const data = await apiRequest<{ document: KBDocument }>('/kb/documents', {
    method: 'POST',
    body: formData,
  });
  return data.document;
}

export async function searchKB(query: string, n_results: number = 5): Promise<KBSearchResult[]> {
  const data = await apiRequest<{ results: KBSearchResult[] }>('/kb/search', {
    method: 'POST',
    body: JSON.stringify({ query, n_results }),
  });
  return data.results || [];
}

export async function deleteKBDocument(id: string): Promise<void> {
  await apiRequest(`/kb/documents/${id}`, { method: 'DELETE' });
}

// Models APIs
export async function getModels(): Promise<ModelsStatusResponse> {
  return await apiRequest<ModelsStatusResponse>('/models');
}

export async function reloadModels(): Promise<{ status: string; message: string; model_count: number }> {
  return await apiRequest('/models/reload', { method: 'POST' });
}

// Audit APIs
export async function getAuditLogs(params: { event_type?: string; limit?: number; offset?: number } = {}): Promise<AuditEvent[]> {
  const query = new URLSearchParams();
  if (params.event_type) query.set('event_type', params.event_type);
  if (params.limit) query.set('limit', String(params.limit));
  if (params.offset) query.set('offset', String(params.offset));
  const qs = query.toString();
  const data = await apiRequest<{ events: AuditEvent[] }>(`/audit${qs ? `?${qs}` : ''}`);
  return data.events || [];
}

export async function verifyAuditChain(): Promise<{ valid: boolean; records_checked: number; message: string }> {
  return await apiRequest('/audit/verify');
}

// System APIs
export async function getSystemHealth(): Promise<any> {
  return await apiRequest('/health');
}
