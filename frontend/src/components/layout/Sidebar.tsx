import React from 'react';
import { NavLink } from 'react-router-dom';
import { 
  Terminal, 
  Database, 
  FolderOpen, 
  Eye, 
  CheckSquare, 
  ClipboardCheck, 
  ShieldCheck, 
  Cpu, 
  ShieldAlert, 
  Activity, 
  Sliders, 
  Plus, 
  LogOut,
  User as UserIcon,
  Server
} from 'lucide-react';
import { useAuth } from '../../context/AuthContext';
import { ClearanceChip } from '../common/ClearanceChip';

export const Sidebar: React.FC = () => {
  const { user, logout } = useAuth();

  const navLinkClasses = ({ isActive }: { isActive: boolean }) =>
    `flex items-center gap-2.5 px-3 py-2 rounded-r transition-colors text-sm font-medium ${
      isActive
        ? 'bg-surface-container-high text-primary-container font-semibold border-l-2 border-primary-container'
        : 'text-on-surface-variant hover:bg-surface-container hover:text-on-surface'
    }`;

  return (
    <aside className="fixed left-0 top-0 h-screen w-72 bg-surface-container-lowest border-r border-outline-variant/30 z-50 flex flex-col justify-between select-none">
      {/* Top Header */}
      <div className="flex flex-col flex-1 min-h-0">
        <div className="h-16 px-4 border-b border-outline-variant/30 flex items-center gap-3">
          <img src="/emblem.svg" alt="PRISM-AI Sovereign Emblem" className="h-8 w-8 object-contain" />
          <div className="flex flex-col min-w-0">
            <div className="flex items-center gap-1.5">
              <span className="font-headline text-sm tracking-tight text-on-surface uppercase font-bold">
                PRISM-AI
              </span>
              <span className="inline-block w-1.5 h-1.5 rounded-full bg-primary-container shadow-[0_0_8px_#00e5ff]" />
            </div>
            <span className="font-mono text-[10px] tracking-widest text-on-surface-variant/70 uppercase truncate">
              Sovereign Intelligence
            </span>
          </div>
        </div>

        {/* Scrollable Navigation */}
        <div className="overflow-y-auto px-3 py-3 space-y-4 flex-1">
          {/* New Workspace Button */}
          <div>
            <button
              onClick={() => window.location.href = '/'}
              className="w-full flex items-center justify-between px-3 py-2 rounded bg-surface-container-high/40 hover:bg-surface-container-high border border-outline-variant/40 hover:border-primary-container/40 text-on-surface transition-colors group"
            >
              <div className="flex items-center gap-2">
                <Plus className="w-4 h-4 text-primary-container group-hover:rotate-90 transition-transform" />
                <span className="text-xs font-semibold">New Workspace</span>
              </div>
              <span className="font-mono text-[10px] px-1.5 py-0.5 rounded bg-surface-container-lowest text-on-surface-variant border border-outline-variant/40">
                ⌘N
              </span>
            </button>
          </div>

          {/* Workspace Modules */}
          <div className="space-y-1">
            <div className="px-2 pb-1">
              <span className="font-mono text-[10px] uppercase tracking-wider text-outline font-semibold">
                Workspace Modules
              </span>
            </div>
            <nav className="space-y-0.5">
              <NavLink to="/" end className={navLinkClasses}>
                <Terminal className="w-4 h-4" />
                <span>AI Workbench</span>
              </NavLink>
              <NavLink to="/kb" className={navLinkClasses}>
                <Database className="w-4 h-4" />
                <span>Knowledge Base</span>
              </NavLink>
              <NavLink to="/vision" className={navLinkClasses}>
                <Eye className="w-4 h-4" />
                <span>Inspection Vision</span>
              </NavLink>
              <NavLink to="/artifacts" className={navLinkClasses}>
                <CheckSquare className="w-4 h-4" />
                <span>Deliverables</span>
              </NavLink>
              <NavLink to="/review" className={navLinkClasses}>
                <div className="flex items-center justify-between w-full">
                  <div className="flex items-center gap-2.5">
                    <ClipboardCheck className="w-4 h-4" />
                    <span>Review Queue</span>
                  </div>
                  <span className="font-mono text-[10px] px-1.5 py-0.2 rounded bg-surface-container text-tertiary-fixed-dim border border-outline-variant/40 font-bold">
                    ACTIVE
                  </span>
                </div>
              </NavLink>
              <NavLink to="/audit" className={navLinkClasses}>
                <ShieldCheck className="w-4 h-4" />
                <span>Audit Trail</span>
              </NavLink>
            </nav>
          </div>

          {/* System Section */}
          <div className="pt-1">
            <div className="h-px bg-outline-variant/20 mx-2 mb-3" />
            <div className="px-2 pb-1">
              <span className="font-mono text-[10px] uppercase tracking-wider text-outline font-semibold">
                System
              </span>
            </div>
            <nav className="space-y-0.5">
              <NavLink to="/models" className={navLinkClasses}>
                <Cpu className="w-4 h-4" />
                <span>Model Registry</span>
              </NavLink>
              <NavLink to="/sovereignty" className={navLinkClasses}>
                <div className="flex items-center justify-between w-full">
                  <div className="flex items-center gap-2.5">
                    <Server className="w-4 h-4" />
                    <span>Sovereignty Panel</span>
                  </div>
                  <span className="w-1.5 h-1.5 rounded-full bg-tertiary shadow-[0_0_6px_#a8ffd2]" />
                </div>
              </NavLink>
              {user?.role === 'admin' && (
                <NavLink to="/users" className={navLinkClasses}>
                  <ShieldAlert className="w-4 h-4" />
                  <span>Security & RBAC</span>
                </NavLink>
              )}
            </nav>
          </div>
        </div>
      </div>

      {/* Operator User Card Footer */}
      <div className="p-3 border-t border-outline-variant/30 bg-surface-container-low/60">
        <div className="flex items-center justify-between gap-2 p-2 rounded-lg bg-surface-container border border-outline-variant/20">
          <div className="flex items-center gap-2.5 min-w-0">
            <div className="w-8 h-8 rounded-full bg-primary/20 border border-primary/30 flex items-center justify-center shrink-0">
              <UserIcon className="w-4 h-4 text-primary" />
            </div>
            <div className="flex flex-col min-w-0">
              <span className="font-headline text-xs font-semibold text-on-surface truncate">
                {user?.username || 'Operator'}
              </span>
              <span className="font-mono text-[10px] text-on-surface-variant/80 truncate">
                Role: {user?.role || 'engineer'}
              </span>
            </div>
          </div>
          <div className="flex items-center gap-1.5 shrink-0">
            {user?.clearance && <ClearanceChip clearance={user.clearance} size="sm" />}
            <button
              onClick={logout}
              title="Logout session"
              className="p-1 rounded text-outline hover:text-rose-400 hover:bg-surface-container-high transition-colors"
            >
              <LogOut className="w-3.5 h-3.5" />
            </button>
          </div>
        </div>
      </div>
    </aside>
  );
};
