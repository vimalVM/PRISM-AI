export type ArtifactStatus = 
  | 'PENDING_REVIEW' 
  | 'APPROVED' 
  | 'REJECTED' 
  | 'CHANGES_REQUESTED'
  | 'pending_review' 
  | 'approved' 
  | 'rejected'
  | 'changes_requested';

export interface ValidationItem {
  name: string;
  passed: boolean;
  message?: string;
}

export interface Artifact {
  id: string;
  task_id: string;
  owner_id: string;
  clearance?: string;
  kind?: string;
  file_type?: string;
  filename: string;
  sha256: string;
  status: ArtifactStatus;
  validation_passed?: boolean;
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
