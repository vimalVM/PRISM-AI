import React from 'react';
import { 
  Sun, 
  Moon, 
  PanelLeftClose, 
  PanelLeft, 
  ShieldCheck, 
  Cpu, 
  Lock 
} from 'lucide-react';
import { useTheme } from '../../context/ThemeContext';
import { useSidebar } from '../../context/SidebarContext';
import { useAuth } from '../../context/AuthContext';

export const Header: React.FC = () => {
  const { theme, toggleTheme } = useTheme();
  const { isCollapsed, toggleSidebar } = useSidebar();
  const { user } = useAuth();

  return (
    <header className={`fixed top-0 right-0 h-14 bg-white/95 dark:bg-slate-950/95 backdrop-blur-md border-b border-slate-200 dark:border-slate-800 z-30 px-4 sm:px-6 flex items-center justify-between transition-all duration-300 ${isCollapsed ? 'left-16' : 'left-64'}`}>
      {/* Left: Sidebar toggle + Sovereign status */}
      <div className="flex items-center gap-3">
        <button
          type="button"
          onClick={toggleSidebar}
          className="p-1.5 rounded-md text-slate-500 hover:text-slate-800 dark:hover:text-slate-200 hover:bg-slate-100 dark:hover:bg-slate-800 transition-colors cursor-pointer"
          title={isCollapsed ? "Expand sidebar" : "Collapse sidebar"}
        >
          {isCollapsed ? <PanelLeft className="w-4 h-4" /> : <PanelLeftClose className="w-4 h-4" />}
        </button>

        <div className="hidden sm:flex items-center gap-2">
          <div className="flex items-center gap-1.5 px-2.5 py-1 rounded-full bg-emerald-50 dark:bg-emerald-950/40 border border-emerald-200 dark:border-emerald-800/50 text-emerald-700 dark:text-emerald-300 font-mono text-[11px] font-medium">
            <span className="w-1.5 h-1.5 rounded-full bg-emerald-500 animate-pulse" />
            <span className="flex items-center gap-1">
              <Lock className="w-3 h-3" />
              Air-Gapped Localhost
            </span>
          </div>

          <div className="hidden md:flex items-center gap-1.5 px-2.5 py-1 rounded-full bg-sky-50 dark:bg-sky-950/40 border border-sky-200 dark:border-sky-800/50 text-sky-700 dark:text-sky-300 font-mono text-[11px] font-medium">
            <Cpu className="w-3 h-3 text-sky-500" />
            <span>Qwen 3.5 4B · Gemma 4 E4B</span>
          </div>
        </div>
      </div>

      {/* Right: Theme Toggle, User Clearance Pill */}
      <div className="flex items-center gap-3">
        {/* Clearance Badge */}
        {user && (
          <span className="hidden sm:inline-flex items-center gap-1 px-2.5 py-0.5 rounded-full border border-slate-200 dark:border-slate-700 bg-slate-100 dark:bg-slate-800 text-[10px] font-mono font-semibold text-slate-700 dark:text-slate-300 uppercase tracking-wider">
            <ShieldCheck className="w-3 h-3 text-emerald-600 dark:text-emerald-400" />
            {user.clearance}
          </span>
        )}

        {/* Theme Toggle Button */}
        <button
          type="button"
          onClick={toggleTheme}
          title="Toggle Light / Dark Theme"
          className="p-1.5 rounded-lg border border-slate-200 dark:border-slate-800 bg-slate-50 dark:bg-slate-900 text-slate-600 dark:text-slate-400 hover:text-slate-900 dark:hover:text-slate-100 transition-colors cursor-pointer"
        >
          {theme === 'dark' ? <Sun className="w-4 h-4 text-amber-500" /> : <Moon className="w-4 h-4 text-slate-700" />}
        </button>

        {/* User initials */}
        {user && (
          <div className="w-7 h-7 rounded-full bg-sky-100 dark:bg-sky-900/60 border border-sky-300 dark:border-sky-700 flex items-center justify-center font-bold text-xs text-sky-700 dark:text-sky-300 font-mono">
            {user.username.slice(0, 2).toUpperCase()}
          </div>
        )}
      </div>
    </header>
  );
};
