import React from 'react';
import { 
  ChevronDown, 
  Search, 
  Bell, 
  Settings, 
  Sun, 
  Moon 
} from 'lucide-react';
import { useTheme } from '../../context/ThemeContext';

export const Header: React.FC = () => {
  const { theme, toggleTheme } = useTheme();

  return (
    <header className="fixed top-0 left-64 right-0 h-16 bg-white/95 dark:bg-slate-950/95 backdrop-blur-md border-b border-slate-200 dark:border-slate-800/80 z-40 px-6 flex items-center justify-between">
      {/* Left: Active Workspace Breadcrumb & Hardware Security Badges */}
      <div className="flex items-center gap-3">
        <div className="flex items-center gap-2 px-3 py-1.5 rounded-lg border border-slate-200 dark:border-slate-700 bg-slate-50 dark:bg-slate-900 hover:bg-slate-100 transition-colors cursor-pointer group">
          <span className="w-2 h-2 rounded-full bg-emerald-500" />
          <span className="font-semibold text-xs text-slate-800 dark:text-slate-200">
            CDU-02 Inspection Analysis
          </span>
          <ChevronDown className="w-3.5 h-3.5 text-slate-400 group-hover:text-slate-600 transition-colors" />
        </div>

        <span className="text-slate-300 dark:text-slate-700 font-mono text-sm hidden sm:inline">/</span>

        <div className="flex items-center gap-1.5 px-2.5 py-1 rounded-full bg-emerald-50 dark:bg-emerald-950/40 border border-emerald-200 dark:border-emerald-800/50 text-emerald-700 dark:text-emerald-300 font-mono text-[11px] font-semibold">
          <span className="w-1.5 h-1.5 rounded-full bg-emerald-500 animate-pulse" />
          <span>Air-Gapped · Local RTX 3050</span>
        </div>
      </div>

      {/* Right: Search, Notifications, Theme Toggle, Settings, Avatar */}
      <div className="flex items-center gap-2.5">
        {/* Quick Search Shortcut */}
        <button
          type="button"
          className="flex items-center gap-2 px-2.5 py-1.5 rounded-lg border border-slate-200 dark:border-slate-800 bg-slate-50 dark:bg-slate-900 text-slate-500 hover:text-slate-800 transition-colors text-xs font-mono"
        >
          <Search className="w-3.5 h-3.5" />
          <span className="text-[11px]">⌘K</span>
        </button>

        {/* Notifications */}
        <button
          type="button"
          className="p-2 rounded-lg border border-slate-200 dark:border-slate-800 bg-slate-50 dark:bg-slate-900 text-slate-500 hover:text-slate-800 transition-colors"
          title="Notifications"
        >
          <Bell className="w-4 h-4" />
        </button>

        {/* Theme Toggle Button */}
        <button
          type="button"
          onClick={toggleTheme}
          title="Toggle Light / Dark Theme"
          className="p-2 rounded-lg border border-slate-200 dark:border-slate-800 bg-slate-50 dark:bg-slate-900 text-slate-500 hover:text-slate-800 transition-colors cursor-pointer"
        >
          {theme === 'dark' ? <Sun className="w-4 h-4 text-amber-500" /> : <Moon className="w-4 h-4 text-slate-700" />}
        </button>

        {/* Settings */}
        <a
          href="/models"
          className="p-2 rounded-lg border border-slate-200 dark:border-slate-800 bg-slate-50 dark:bg-slate-900 text-slate-500 hover:text-slate-800 transition-colors"
        >
          <Settings className="w-4 h-4" />
        </a>

        {/* User avatar */}
        <div className="w-8 h-8 rounded-full bg-slate-200 dark:bg-slate-700 overflow-hidden flex items-center justify-center font-bold text-xs text-slate-700 dark:text-slate-200 ml-1 border border-slate-300 dark:border-slate-600">
          KM
        </div>
      </div>
    </header>
  );
};
