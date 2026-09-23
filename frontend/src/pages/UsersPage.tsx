import React from 'react';
import { ShieldAlert, User, ShieldCheck } from 'lucide-react';
import { ClearanceChip } from '../components/common/ClearanceChip';

export const UsersPage: React.FC = () => {
  const users = [
    { username: 'admin', role: 'admin', clearance: 'RESTRICTED', active: true },
    { username: 'engineer', role: 'engineer', clearance: 'CONFIDENTIAL', active: true },
    { username: 'reviewer', role: 'reviewer', clearance: 'CONFIDENTIAL', active: true },
    { username: 'auditor', role: 'auditor', clearance: 'INTERNAL', active: true },
    { username: 'operator', role: 'engineer', clearance: 'CONFIDENTIAL', active: true },
  ];

  return (
    <div className="flex flex-col w-full pb-10 space-y-6">
      {/* Top Banner */}
      <div className="flex items-center justify-between pb-2 border-b border-outline-variant/30">
        <div>
          <h1 className="font-headline text-xl font-bold text-on-surface">
            Security & RBAC Administration
          </h1>
          <p className="text-xs text-on-surface-variant font-mono">
            User Accounts · Role Assignment · Clearance Tiers
          </p>
        </div>
      </div>

      {/* Users Table */}
      <div className="bg-surface-container-low rounded-xl overflow-hidden shadow-lg border border-outline-variant/30">
        <table className="w-full text-left font-mono text-xs">
          <thead className="bg-surface-container-lowest text-outline text-[10px] uppercase border-b border-outline-variant/20">
            <tr>
              <th className="py-3 px-4">Operator / User</th>
              <th className="py-3 px-4">Assigned Role</th>
              <th className="py-3 px-4">Clearance Tier</th>
              <th className="py-3 px-4">Account Status</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-surface-container">
            {users.map((u, i) => (
              <tr key={i} className="hover:bg-surface-container-high/40 transition-colors">
                <td className="py-3.5 px-4 font-semibold text-on-surface flex items-center gap-2">
                  <User className="w-4 h-4 text-primary" />
                  {u.username}
                </td>
                <td className="py-3.5 px-4 uppercase text-on-surface-variant">{u.role}</td>
                <td className="py-3.5 px-4">
                  <ClearanceChip clearance={u.clearance as any} size="sm" />
                </td>
                <td className="py-3.5 px-4">
                  <span className="inline-flex items-center gap-1 text-tertiary font-bold">
                    <ShieldCheck className="w-3.5 h-3.5" /> ACTIVE
                  </span>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
};
