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
  FileText
} from 'lucide-react';
import { useAuth } from '../../context/AuthContext';

export const Sidebar: React.FC = () => {
  const { user } = useAuth();

  const navLinkClasses = ({ isActive }: { isActive: boolean }) =>
    `flex items-center justify-between px-3 py-2 rounded-lg text-xs font-medium transition-colors ${
      isActive
        ? 'bg-sky-50 dark:bg-sky-950/40 text-sky-600 dark:text-sky-400 font-semibold'
        : 'text-slate-600 dark:text-slate-400 hover:bg-slate-100 dark:hover:bg-slate-800/60 hover:text-slate-900 dark:hover:text-slate-100'
    }`;

  return (
    <aside className="fixed left-0 top-0 h-screen w-64 bg-white dark:bg-slate-950 border-r border-slate-200 dark:border-slate-800/80 z-50 flex flex-col justify-between select-none">
      {/* Top Header */}
      <div className="flex flex-col flex-1 min-h-0">
        <div className="h-16 px-4 border-b border-slate-200 dark:border-slate-800/80 flex items-center gap-2.5">
          <div className="w-7 h-7 rounded-lg bg-sky-600 flex items-center justify-center text-white font-bold text-xs shadow-sm">
            ▲
          </div>
          <div className="flex flex-col min-w-0">
            <div className="flex items-center gap-1.5">
              <span className="font-bold text-xs tracking-tight text-slate-900 dark:text-slate-100 uppercase">
                PRISM-AI
              </span>
              <span className="w-1.5 h-1.5 rounded-full bg-emerald-500" />
            </div>
            <span className="font-mono text-[9px] tracking-wider text-slate-400 uppercase">
              Sovereign Intelligence
            </span>
          </div>
        </div>

        {/* Scrollable Navigation */}
        <div className="overflow-y-auto px-3 py-3 space-y-4 flex-1">
          {/* New Workspace Button */}
          <div>
            <button
              type="button"
              onClick={() => window.location.href = '/'}
              className="w-full flex items-center justify-between px-3 py-1.5 rounded-lg border border-sky-200 dark:border-sky-800/60 bg-sky-50/50 dark:bg-sky-950/20 text-sky-700 dark:text-sky-300 text-xs font-semibold hover:bg-sky-50 transition-colors"
            >
              <div className="flex items-center gap-1.5">
                <Plus className="w-3.5 h-3.5" />
                <span>New Workspace</span>
              </div>
              <span className="px-1.5 py-0.2 rounded border border-sky-300 dark:border-sky-700 text-[10px] text-sky-600 font-mono">
                N
              </span>
            </button>
          </div>

          {/* Category: WORKSPACE MODULES */}
          <div className="space-y-1">
            <div className="px-2 pb-1 font-mono text-[10px] font-bold text-slate-400 uppercase tracking-wider">
              Workspace Modules
            </div>
            
            <NavLink to="/" end className={navLinkClasses}>
              <div className="flex items-center gap-2.5">
                <Terminal className="w-4 h-4 text-sky-500" />
                <span>AI Workbench</span>
              </div>
            </NavLink>

            <NavLink to="/kb" className={navLinkClasses}>
              <div className="flex items-center gap-2.5">
                <Database className="w-4 h-4" />
                <span>Knowledge Base</span>
              </div>
            </NavLink>

            <NavLink to="/artifacts" className={navLinkClasses}>
              <div className="flex items-center gap-2.5">
                <FolderOpen className="w-4 h-4" />
                <span>Documents</span>
              </div>
            </NavLink>

            <NavLink to="/vision" className={navLinkClasses}>
              <div className="flex items-center gap-2.5">
                <Eye className="w-4 h-4" />
                <span>Inspection Vision</span>
              </div>
            </NavLink>

            <NavLink to="/artifacts" className={navLinkClasses}>
              <div className="flex items-center gap-2.5">
                <FileText className="w-4 h-4" />
                <span>Deliverables</span>
              </div>
            </NavLink>

            <NavLink to="/review" className={navLinkClasses}>
              <div className="flex items-center gap-2.5">
                <ClipboardCheck className="w-4 h-4" />
                <span>Review Queue</span>
              </div>
              <span className="px-1.5 py-0.2 rounded-full bg-emerald-100 text-emerald-700 dark:bg-emerald-950 dark:text-emerald-300 text-[10px] font-bold font-mono">
                4
              </span>
            </NavLink>

            <NavLink to="/audit" className={navLinkClasses}>
              <div className="flex items-center gap-2.5">
                <ShieldCheck className="w-4 h-4" />
                <span>Audit Trail</span>
              </div>
            </NavLink>
          </div>

          {/* Category: SYSTEM */}
          <div className="space-y-1 pt-2">
            <div className="px-2 pb-1 font-mono text-[10px] font-bold text-slate-400 uppercase tracking-wider">
              System
            </div>

            <NavLink to="/models" className={navLinkClasses}>
              <div className="flex items-center gap-2.5">
                <Cpu className="w-4 h-4" />
                <span>Model Registry</span>
              </div>
            </NavLink>

            <NavLink to="/sovereignty" className={navLinkClasses}>
              <div className="flex items-center gap-2.5">
                <ShieldAlert className="w-4 h-4" />
                <span>Security & RBAC</span>
              </div>
            </NavLink>

            <NavLink to="/system" className={navLinkClasses}>
              <div className="flex items-center gap-2.5">
                <Activity className="w-4 h-4" />
                <span>System Health</span>
              </div>
              <span className="w-1.5 h-1.5 rounded-full bg-emerald-500" />
            </NavLink>

            <NavLink to="/models" className={navLinkClasses}>
              <div className="flex items-center gap-2.5">
                <Sliders className="w-4 h-4" />
                <span>Settings</span>
              </div>
            </NavLink>
          </div>
        </div>
      </div>

      {/* Bottom Profile Bar */}
      <div className="p-3 border-t border-slate-200 dark:border-slate-800/80 bg-slate-50/60 dark:bg-slate-900/40">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-2 min-w-0">
            <div className="w-8 h-8 rounded-full bg-slate-200 dark:bg-slate-700 overflow-hidden flex items-center justify-center font-bold text-xs text-slate-700 dark:text-slate-200 shrink-0">
              KM
            </div>
            <div className="flex flex-col min-w-0">
              <span className="text-xs font-semibold text-slate-900 dark:text-slate-100 truncate">
                Krishna Mahajan
              </span>
              <span className="text-[10px] text-slate-400 font-mono truncate">
                Op Lead · ID: 9042
              </span>
            </div>
          </div>
          <span className="px-1.5 py-0.5 rounded border border-amber-300 dark:border-amber-700 bg-amber-50 dark:bg-amber-950/40 text-amber-700 dark:text-amber-300 text-[9px] font-bold font-mono tracking-wider shrink-0">
            L2 CLEAR
          </span>
        </div>
      </div>
    </aside>
  );
};
