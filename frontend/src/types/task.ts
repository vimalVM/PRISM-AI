export type TaskStatus = 
  | 'PENDING'
  | 'RUNNING'
  | 'AWAITING_REVIEW'
  | 'COMPLETED'
  | 'FAILED'
  | 'CANCELLED';

export interface TaskEvent {
  id?: string;
  task_id: string;
  seq: number;
  ts: string;
  type: string;
  node?: string;
  tool?: string;
  model?: string;
  status: string;
  duration_ms?: number;
  summary: string;
  refs?: any;
}

export interface Task {
  id: string;
  owner_id: string;
  request_text: string;
  task_type?: string;
  complexity?: string;
  risk?: string;
  status: TaskStatus;
  selected_models?: string[];
  retry_count?: number;
  created_at: string;
  finished_at?: string | null;
  error?: string | null;
}

export interface CreateTaskPayload {
  message: string;
  file_ids?: string[];
  task_hint?: string;
}
