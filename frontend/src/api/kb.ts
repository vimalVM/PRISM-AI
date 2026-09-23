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
    const data = await apiRequest<KBDocumentResponse[] | { documents: KBDocumentResponse[] }>('/kb/documents');
    if (Array.isArray(data)) {
      return data;
    }
    return (data as any).documents || [];
  } catch (err) {
    console.error('Failed to load KB documents:', err);
    return [];
  }
}

export async function uploadKBDocument(
  file: File, 
  docId: string, 
  classification: number = 2
): Promise<any> {
  const formData = new FormData();
  formData.append('file', file);
  formData.append('doc_id', docId);
  formData.append('classification', String(classification));
  formData.append('version', '1');
  return await apiRequest<any>('/kb/upload', {
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

export async function searchKB(query: string, k = 5): Promise<any[]> {
  try {
    const data = await apiRequest<{ query: string; total: number; chunks: any[] }>('/kb/search', {
      method: 'POST',
      body: JSON.stringify({ query, k }),
    });
    return data.chunks || [];
  } catch (err) {
    console.error('KB Search failed:', err);
    return [];
  }
}

