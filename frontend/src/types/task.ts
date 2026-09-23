export type TaskStatus = 
  | 'PENDING' | 'pending'
  | 'RUNNING' | 'running'
  | 'AWAITING_REVIEW' | 'awaiting_review'
  | 'COMPLETED' | 'completed'
  | 'FAILED' | 'failed'
  | 'CANCELLED' | 'cancelled';

export interface TaskEvent {
  id?: string;
  task_id: string;
  seq?: number;
  ts?: string;
  timestamp?: string;
  type?: string;
  event_type?: string;
  node?: string;
  tool?: string;
  model?: string;
  status: string;
  duration_ms?: number;
  summary: string;
  detail?: any;
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
  result?: string | null;
}

export interface CreateTaskPayload {
  request_text: string;
  message?: string;
  file_ids?: string[];
  task_type?: string;
  task_hint?: string;
}
