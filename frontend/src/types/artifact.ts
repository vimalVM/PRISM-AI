export type ArtifactStatus = 'PENDING_REVIEW' | 'APPROVED' | 'REJECTED' | 'CHANGES_REQUESTED';

export interface ValidationItem {
  name: string;
  passed: boolean;
  message?: string;
}

export interface Artifact {
  id: string;
  task_id: string;
  owner_id: string;
  kind: string;
  filename: string;
  sha256: string;
  status: ArtifactStatus;
  validation_report?: {
    valid: boolean;
    checks: Record<string, boolean>;
    findings?: any[];
  } | null;
  reviewer_id?: string | null;
  reviewed_at?: string | null;
  review_comment?: string | null;
  created_at: string;
}

export interface ReviewDecisionPayload {
  decision: 'approve' | 'reject' | 'changes';
  comment: string;
}
