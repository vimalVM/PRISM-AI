import React from 'react';
import { 
  ChevronDown, 
  Search, 
  Bell, 
  Settings, 
  Sun, 
  Moon, 
  Cpu, 
  ShieldCheck, 
  Lock, 
  Zap 
} from 'lucide-react';
import { useAuth } from '../../context/AuthContext';
import { useTheme } from '../../context/ThemeContext';

export const Header: React.FC = () => {
  const { user } = useAuth();
  const { theme, toggleTheme } = useTheme();

  return (
    <header className="fixed top-0 left-72 right-0 h-16 bg-surface-container-lowest/90 backdrop-blur-md border-b border-outline-variant/30 z-40 px-6 flex items-center justify-between">
      {/* Left: Active Workspace Breadcrumb & Hardware Security Badges */}
      <div className="flex items-center gap-4">
        <div className="flex items-center gap-2 px-3 py-1.5 rounded bg-surface-container border border-outline-variant/40 hover:border-outline transition-colors cursor-pointer group">
          <span className="w-2 h-2 rounded-full bg-tertiary shadow-[0_0_6px_#a8ffd2]" />
          <span className="font-mono text-xs font-semibold text-on-surface">CDU-02 Inspection Analysis</span>
          <ChevronDown className="w-4 h-4 text-on-surface-variant group-hover:text-on-surface transition-colors" />
        </div>

        <div className="h-4 w-px bg-outline-variant/30 hidden lg:block" />

        <div className="hidden xl:flex items-center gap-2">
          <div className="flex items-center gap-1.5 px-2 py-0.5 rounded bg-surface-container-low border border-outline-variant/30 text-tertiary font-mono text-[10px] tracking-widest uppercase">
            <span className="w-1.5 h-1.5 rounded-full bg-tertiary animate-pulse" />
            AIR-GAPPED
          </div>
          <div className="flex items-center gap-1.5 px-2 py-0.5 rounded bg-surface-container-low border border-outline-variant/30 text-primary-container font-mono text-[10px] tracking-widest uppercase">
            <span className="w-1.5 h-1.5 rounded-full bg-primary-container" />
            LOCAL RTX 3050
          </div>
          <div className="flex items-center gap-1.5 px-2 py-0.5 rounded bg-surface-container-low border border-outline-variant/30 text-tertiary font-mono text-[10px] tracking-widest uppercase">
            <span className="w-1.5 h-1.5 rounded-full bg-tertiary" />
            ZERO EGRESS
          </div>
        </div>
      </div>

      {/* Right: Hardware VRAM Meter, Theme Toggle & Controls */}
      <div className="flex items-center gap-3">
        {/* VRAM Allocation Gauge */}
        <div className="hidden md:flex items-center gap-2 px-3 py-1.5 rounded bg-surface-container-low border border-outline-variant/30 text-on-surface font-mono text-xs">
          <Cpu className="w-4 h-4 text-primary-container" />
          <span className="text-on-surface-variant">VRAM</span>
          <span className="text-outline">|</span>
          <span className="text-on-surface font-mono">3.8 / 6.0 GB</span>
          <div className="w-16 h-1.5 bg-surface-container-highest rounded-full overflow-hidden">
            <div className="bg-primary-container h-full w-[63%]" />
          </div>
        </div>

        {/* Quick Search Shortcut */}
        <button
          onClick={() => {}}
          className="flex items-center gap-2 px-2.5 py-1.5 rounded bg-surface-container-low border border-outline-variant/30 text-on-surface-variant hover:text-on-surface hover:border-outline transition-colors"
        >
          <Search className="w-4 h-4" />
          <span className="font-mono text-xs hidden sm:inline text-on-surface-variant">⌘K</span>
        </button>

        {/* Theme Toggle Button */}
        <button
          onClick={toggleTheme}
          title="Toggle Dark / Light Theme"
          className="p-2 rounded bg-surface-container-low border border-outline-variant/30 text-on-surface-variant hover:text-on-surface transition-colors"
        >
          {theme === 'dark' ? <Sun className="w-4 h-4 text-amber-400" /> : <Moon className="w-4 h-4 text-sky-600" />}
        </button>

        {/* System Settings Link */}
        <a
          href="/models"
          className="p-2 rounded bg-surface-container-low border border-outline-variant/30 text-on-surface-variant hover:text-on-surface transition-colors"
        >
          <Settings className="w-4 h-4" />
        </a>
      </div>
    </header>
  );
};
