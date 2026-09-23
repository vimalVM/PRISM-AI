import React, { useEffect, useState } from 'react';
import { NavLink, useNavigate, useLocation } from 'react-router-dom';
import { 
  Terminal, 
  Database, 
  FolderOpen, 
  Eye, 
  ClipboardCheck, 
  ShieldCheck, 
  Plus, 
  LogOut,
  Clock,
  CheckCircle2,
  AlertCircle,
  Loader2,
  ChevronRight
} from 'lucide-react';
import { useAuth } from '../../context/AuthContext';
import { useSidebar } from '../../context/SidebarContext';
import { getTasks } from '../../api/tasks';
import { Task } from '../../types/task';

export const Sidebar: React.FC = () => {
  const { user, logout } = useAuth();
  const { isCollapsed } = useSidebar();
  const navigate = useNavigate();
  const location = useLocation();

  const [recentTasks, setRecentTasks] = useState<Task[]>([]);
  const [isLoadingTasks, setIsLoadingTasks] = useState(false);

  useEffect(() => {
    let mounted = true;
    const fetchRecent = async () => {
      try {
        setIsLoadingTasks(true);
        const tasks = await getTasks();
        if (mounted) {
          // Sort newest first and take top 5
          const sorted = [...tasks].sort(
            (a, b) => new Date(b.created_at).getTime() - new Date(a.created_at).getTime()
          );
          setRecentTasks(sorted.slice(0, 6));
        }
      } catch (err) {
        // Fallback for offline/standalone mode
      } finally {
        if (mounted) setIsLoadingTasks(false);
      }
    };

    fetchRecent();
    const interval = setInterval(fetchRecent, 10000);
    return () => {
      mounted = false;
      clearInterval(interval);
    };
  }, []);

  const navLinkClasses = ({ isActive }: { isActive: boolean }) =>
    `flex items-center ${isCollapsed ? 'justify-center px-2 py-2.5' : 'justify-between px-3 py-2'} rounded-lg text-xs font-medium transition-colors ${
      isActive
        ? 'bg-sky-50 dark:bg-sky-950/50 text-sky-600 dark:text-sky-400 font-semibold'
        : 'text-slate-600 dark:text-slate-400 hover:bg-slate-100 dark:hover:bg-slate-800/60 hover:text-slate-900 dark:hover:text-slate-100'
    }`;

  const handleNewSession = () => {
    navigate('/', { state: { newSession: true } });
    if (location.pathname === '/') {
      window.dispatchEvent(new CustomEvent('prism:new-task'));
    }
  };

  const handleSelectTask = (taskId: string) => {
    navigate('/', { state: { selectedTaskId: taskId } });
    window.dispatchEvent(new CustomEvent('prism:select-task', { detail: { taskId } }));
  };

  return (
    <aside 
      className={`fixed left-0 top-0 h-screen ${
        isCollapsed ? 'w-16' : 'w-64'
      } bg-white dark:bg-slate-950 border-r border-slate-200 dark:border-slate-800 z-40 flex flex-col justify-between transition-all duration-300 select-none`}
    >
      {/* Top Header & Actions */}
      <div className="flex flex-col flex-1 min-h-0">
        {/* Brand / Logo */}
        <div className={`h-14 border-b border-slate-200 dark:border-slate-800 flex items-center ${isCollapsed ? 'justify-center px-2' : 'px-4 gap-2.5'}`}>
          <div className="w-7 h-7 rounded-lg bg-sky-600 flex items-center justify-center text-white font-bold text-xs shadow-sm flex-shrink-0">
            ▲
          </div>
          {!isCollapsed && (
            <div className="flex flex-col min-w-0">
              <div className="flex items-center gap-1.5">
                <span className="font-bold text-xs tracking-tight text-slate-900 dark:text-slate-100 uppercase">
                  PRISM-AI
                </span>
                <span className="w-1.5 h-1.5 rounded-full bg-emerald-500" title="Air-gapped localhost active" />
              </div>
              <span className="font-mono text-[9px] tracking-wider text-slate-400 uppercase">
                Sovereign Workbench
              </span>
            </div>
          )}
        </div>

        {/* Action: + New Task */}
        <div className="p-3">
          <button
            type="button"
            onClick={handleNewSession}
            className={`w-full flex items-center ${isCollapsed ? 'justify-center p-2' : 'justify-between px-3 py-2'} rounded-lg bg-slate-900 hover:bg-slate-800 dark:bg-sky-600 dark:hover:bg-sky-500 text-white text-xs font-semibold shadow-sm transition-all cursor-pointer group`}
            title="Start New Task (N)"
          >
            <div className="flex items-center gap-2">
              <Plus className="w-4 h-4 transition-transform group-hover:rotate-90" />
              {!isCollapsed && <span>New Task</span>}
            </div>
            {!isCollapsed && (
              <span className="px-1.5 py-0.5 rounded bg-slate-800 dark:bg-sky-700 text-[10px] text-slate-300 dark:text-sky-200 font-mono">
                ⌘N
              </span>
            )}
          </button>
        </div>

        {/* Scrollable Navigation & Recent Sessions */}
        <div className="overflow-y-auto px-3 space-y-4 flex-1">
          {/* Main Navigation */}
          <div className="space-y-1">
            {!isCollapsed && (
              <div className="px-2 pb-1 font-mono text-[10px] font-bold text-slate-400 uppercase tracking-wider">
                Modules
              </div>
            )}
            
            <NavLink to="/" end className={navLinkClasses} title="AI Workbench">
              <div className="flex items-center gap-2.5">
                <Terminal className="w-4 h-4 text-sky-500 flex-shrink-0" />
                {!isCollapsed && <span>Workbench</span>}
              </div>
            </NavLink>

            <NavLink to="/kb" className={navLinkClasses} title="Knowledge Base">
              <div className="flex items-center gap-2.5">
                <Database className="w-4 h-4 text-slate-500 flex-shrink-0" />
                {!isCollapsed && <span>Knowledge Base</span>}
              </div>
            </NavLink>

            <NavLink to="/vision" className={navLinkClasses} title="Inspection Vision">
              <div className="flex items-center gap-2.5">
                <Eye className="w-4 h-4 text-slate-500 flex-shrink-0" />
                {!isCollapsed && <span>Inspection Vision</span>}
              </div>
            </NavLink>

            <NavLink to="/artifacts" className={navLinkClasses} title="Documents & Deliverables">
              <div className="flex items-center gap-2.5">
                <FolderOpen className="w-4 h-4 text-slate-500 flex-shrink-0" />
                {!isCollapsed && <span>Deliverables</span>}
              </div>
            </NavLink>

            <NavLink to="/review" className={navLinkClasses} title="Review Queue">
              <div className="flex items-center gap-2.5">
                <ClipboardCheck className="w-4 h-4 text-slate-500 flex-shrink-0" />
                {!isCollapsed && <span>Review Gate</span>}
              </div>
            </NavLink>

            <NavLink to="/sovereignty" className={navLinkClasses} title="Sovereignty & Security">
              <div className="flex items-center gap-2.5">
                <ShieldCheck className="w-4 h-4 text-emerald-500 flex-shrink-0" />
                {!isCollapsed && <span>Sovereignty</span>}
              </div>
            </NavLink>
          </div>

          {/* Recent Task Sessions (Codex Style) */}
          {!isCollapsed && (
            <div className="pt-2 border-t border-slate-100 dark:border-slate-800 space-y-1">
              <div className="flex items-center justify-between px-2 pb-1">
                <span className="font-mono text-[10px] font-bold text-slate-400 uppercase tracking-wider">
                  Recent Tasks
                </span>
                {isLoadingTasks && <Loader2 className="w-3 h-3 text-slate-400 animate-spin" />}
              </div>

              {recentTasks.length === 0 ? (
                <div className="px-2 py-3 text-[11px] text-slate-400 italic">
                  No recent tasks yet.
                </div>
              ) : (
                recentTasks.map((t) => (
                  <button
                    key={t.id}
                    type="button"
                    onClick={() => handleSelectTask(t.id)}
                    className="w-full text-left px-2.5 py-1.5 rounded-lg text-xs hover:bg-slate-100 dark:hover:bg-slate-800/60 transition-colors flex items-center justify-between group cursor-pointer"
                  >
                    <div className="flex items-center gap-2 min-w-0 pr-1">
                      {t.status === 'completed' && <CheckCircle2 className="w-3.5 h-3.5 text-emerald-500 flex-shrink-0" />}
                      {t.status === 'running' && <Loader2 className="w-3.5 h-3.5 text-sky-500 animate-spin flex-shrink-0" />}
                      {t.status === 'failed' && <AlertCircle className="w-3.5 h-3.5 text-rose-500 flex-shrink-0" />}
                      {t.status === 'pending' && <Clock className="w-3.5 h-3.5 text-slate-400 flex-shrink-0" />}
                      <span className="truncate text-slate-700 dark:text-slate-300 text-[11px] font-medium group-hover:text-slate-900 dark:group-hover:text-slate-100">
                        {t.request_text || `Task ${t.id.slice(0, 8)}`}
                      </span>
                    </div>
                    <ChevronRight className="w-3 h-3 text-slate-300 opacity-0 group-hover:opacity-100 transition-opacity flex-shrink-0" />
                  </button>
                ))
              )}
            </div>
          )}
        </div>

        {/* User Profile & Logout */}
        <div className="p-3 border-t border-slate-200 dark:border-slate-800 bg-slate-50/50 dark:bg-slate-900/50">
          {!isCollapsed ? (
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-2 min-w-0">
                <div className="w-7 h-7 rounded-full bg-slate-200 dark:bg-slate-700 flex items-center justify-center font-bold text-xs text-slate-700 dark:text-slate-300 flex-shrink-0">
                  {user?.username ? user.username.slice(0, 2).toUpperCase() : 'US'}
                </div>
                <div className="flex flex-col min-w-0">
                  <span className="text-xs font-semibold text-slate-800 dark:text-slate-200 truncate">
                    {user?.username || 'Local Operator'}
                  </span>
                  <span className="text-[10px] text-slate-400 font-mono uppercase">
                    {user?.role || 'engineer'}
                  </span>
                </div>
              </div>
              <button
                type="button"
                onClick={logout}
                className="p-1.5 rounded-lg text-slate-400 hover:text-rose-500 hover:bg-slate-100 dark:hover:bg-slate-800 transition-colors cursor-pointer"
                title="Log out"
              >
                <LogOut className="w-3.5 h-3.5" />
              </button>
            </div>
          ) : (
            <div className="flex justify-center">
              <button
                type="button"
                onClick={logout}
                className="p-2 rounded-lg text-slate-400 hover:text-rose-500 hover:bg-slate-100 dark:hover:bg-slate-800 transition-colors cursor-pointer"
                title="Log out"
              >
                <LogOut className="w-4 h-4" />
              </button>
            </div>
          )}
        </div>
      </div>
    </aside>
  );
};
