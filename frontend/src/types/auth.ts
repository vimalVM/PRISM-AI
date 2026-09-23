export type Role = 'admin' | 'engineer' | 'reviewer' | 'auditor';

export type Clearance = 'PUBLIC' | 'INTERNAL' | 'CONFIDENTIAL' | 'RESTRICTED';

export interface User {
  id: string;
  username: string;
  role: Role;
  clearance: Clearance;
  active: boolean;
  created_at: string;
  last_login_at?: string | null;
}

export interface AuthState {
  user: User | null;
  isAuthenticated: boolean;
  isLoading: boolean;
}
