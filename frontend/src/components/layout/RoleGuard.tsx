import React, { ReactNode } from 'react';
import { Navigate } from 'react-router-dom';
import { useAuth } from '../../context/AuthContext';
import { Role } from '../../types/auth';

interface RoleGuardProps {
  allowedRoles?: Role[];
  children: ReactNode;
}

export const RoleGuard: React.FC<RoleGuardProps> = ({ allowedRoles, children }) => {
  const { user, isAuthenticated, isLoading } = useAuth();

  if (isLoading) {
    return (
      <div className="flex h-screen w-screen items-center justify-center bg-surface text-on-surface">
        <div className="flex flex-col items-center gap-3">
          <div className="w-8 h-8 rounded-full border-2 border-primary-container border-t-transparent animate-spin" />
          <span className="font-mono text-xs text-outline uppercase tracking-wider">Loading Enclave Session...</span>
        </div>
      </div>
    );
  }

  if (!isAuthenticated || !user) {
    return <Navigate to="/login" replace />;
  }

  if (allowedRoles && !allowedRoles.includes(user.role)) {
    return (
      <div className="flex h-full w-full flex-col items-center justify-center p-12 text-center">
        <div className="p-4 rounded-full bg-rose-500/10 text-rose-400 border border-rose-500/30 mb-4">
          <span className="text-2xl font-mono">403</span>
        </div>
        <h2 className="text-lg font-semibold text-on-surface mb-1">Access Restricted by RBAC Policy</h2>
        <p className="text-sm text-on-surface-variant max-w-md">
          Your current role (<span className="font-mono font-semibold text-primary">{user.role}</span>) does not have authorization to view this enclave module.
        </p>
      </div>
    );
  }

  return <>{children}</>;
};
