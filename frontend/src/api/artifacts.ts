import { apiRequest } from './client';
import { Artifact, ReviewDecisionPayload } from '../types/artifact';

export async function getArtifacts(): Promise<Artifact[]> {
  const data = await apiRequest<{ artifacts: Artifact[] }>('/artifacts');
  return data.artifacts || [];
}

export async function getArtifact(id: string): Promise<Artifact> {
  const data = await apiRequest<{ artifact: Artifact }>(`/artifacts/${id}`);
  return data.artifact;
}

export async function getReviewQueue(): Promise<Artifact[]> {
  const data = await apiRequest<{ queue: Artifact[] }>('/review/queue');
  return data.queue || [];
}

export async function submitReview(artifactId: string, payload: ReviewDecisionPayload): Promise<Artifact> {
  const data = await apiRequest<{ artifact: Artifact }>(`/artifacts/${artifactId}/review`, {
    method: 'POST',
    body: JSON.stringify(payload),
  });
  return data.artifact;
}

export function getArtifactDownloadUrl(artifactId: string): string {
  return `/api/artifacts/${artifactId}/download`;
}
