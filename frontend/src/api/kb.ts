import { apiRequest } from './client';
import { Clearance } from '../types/auth';

export interface KBDocumentResponse {
  id: string;
  doc_id: string;
  filename: string;
  version: string;
  classification: Clearance;
  sha256: string;
  status: 'indexed' | 'processing' | 'failed';
  chunks: number;
  uploaded_by: string;
  ingested_at: string;
}

export interface KBSearchResult {
  filename: string;
  page?: number;
  score: number;
  content: string;
  classification?: string;
}

export async function getKBDocuments(): Promise<KBDocumentResponse[]> {
  try {
    const data = await apiRequest<{ documents: KBDocumentResponse[] }>('/kb/documents');
    return data.documents || [];
  } catch {
    return [];
  }
}

export async function uploadKBDocument(file: File, classification: Clearance): Promise<KBDocumentResponse> {
  const formData = new FormData();
  formData.append('file', file);
  formData.append('classification', classification);
  return await apiRequest<KBDocumentResponse>('/kb/upload', {
    method: 'POST',
    body: formData,
  });
}

export async function deleteKBDocument(docId: string): Promise<boolean> {
  try {
    await apiRequest(`/kb/documents/${docId}`, { method: 'DELETE' });
    return true;
  } catch {
    return false;
  }
}

export async function searchKB(query: string, limit = 5): Promise<KBSearchResult[]> {
  try {
    const data = await apiRequest<{ results: KBSearchResult[] }>(`/kb/search?q=${encodeURIComponent(query)}&limit=${limit}`);
    return data.results || [];
  } catch {
    return [];
  }
}
