import { apiRequest } from './client';
import { Task, TaskEvent, CreateTaskPayload } from '../types/task';

export async function getTasks(): Promise<Task[]> {
  const data = await apiRequest<{ tasks: Task[] }>('/tasks');
  return data.tasks || [];
}

export async function getTask(taskId: string): Promise<Task> {
  const data = await apiRequest<{ task: Task }>(`/tasks/${taskId}`);
  return data.task;
}

export async function createTask(payload: CreateTaskPayload): Promise<{ task_id: string; status: string }> {
  return await apiRequest('/tasks', {
    method: 'POST',
    body: JSON.stringify(payload),
  });
}

export async function cancelTask(taskId: string): Promise<void> {
  await apiRequest(`/tasks/${taskId}/cancel`, { method: 'POST' });
}

export async function getTaskAudit(taskId: string): Promise<any[]> {
  const data = await apiRequest<{ audit_events: any[] }>(`/tasks/${taskId}/audit`);
  return data.audit_events || [];
}

export function subscribeToTaskEvents(
  taskId: string,
  onEvent: (event: TaskEvent) => void,
  onError?: (err: any) => void
): () => void {
  const eventSource = new EventSource(`/api/tasks/${taskId}/events`, { withCredentials: true });

  eventSource.onmessage = (e) => {
    try {
      const data = JSON.parse(e.data);
      onEvent(data);
    } catch (err) {
      console.error('Failed to parse SSE event:', err);
    }
  };

  eventSource.onerror = (err) => {
    if (onError) onError(err);
    eventSource.close();
  };

  return () => {
    eventSource.close();
  };
}
