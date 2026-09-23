import { apiRequest } from './client';

export interface UploadedFile {
  id: string;
  original_name: string;
  mime: string;
  size_bytes: number;
  modality: string;
  created_at: string;
}

export async function uploadFile(file: File): Promise<UploadedFile> {
  const formData = new FormData();
  formData.append('file', file);
  return await apiRequest<UploadedFile>('/files/upload', {
    method: 'POST',
    body: formData,
  });
}

export async function getFiles(): Promise<UploadedFile[]> {
  const data = await apiRequest<{ files: UploadedFile[] }>('/files');
  return data.files || [];
}
