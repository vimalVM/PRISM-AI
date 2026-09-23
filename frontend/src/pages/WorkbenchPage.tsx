import React, { useState } from 'react';
import { 
  ChevronRight, 
  Lock, 
  Shuffle, 
  Activity, 
  Terminal, 
  AlertCircle 
} from 'lucide-react';
import { CommandDeck } from '../components/workbench/CommandDeck';
import { NeuralRouterStream } from '../components/workbench/NeuralRouterStream';
import { RecommendationCard } from '../components/workbench/RecommendationCard';
import { OpticalSensorsPreview } from '../components/workbench/OpticalSensorsPreview';
import { WorkflowTimeline } from '../components/workbench/WorkflowTimeline';
import { SourcesPanel } from '../components/workbench/SourcesPanel';
import { LocalEnclaveCard } from '../components/workbench/LocalEnclaveCard';
import { createTask, subscribeToTaskEvents } from '../api/tasks';
import { TaskEvent } from '../types/task';

export const WorkbenchPage: React.FC = () => {
  const [activeTask, setActiveTask] = useState<string>('PRISM-88219');
  const [isRunning, setIsRunning] = useState<boolean>(false);
  const [events, setEvents] = useState<TaskEvent[]>([]);
  const [errorMsg, setErrorMsg] = useState<string | null>(null);

  const handleExecute = async (prompt: string) => {
    setIsRunning(true);
    setErrorMsg(null);
    try {
      const res = await createTask({ message: prompt });
      setActiveTask(res.task_id.substring(0, 10));
      
      // Subscribe to real-time SSE task events
      const unsubscribe = subscribeToTaskEvents(
        res.task_id,
        (evt) => {
          setEvents((prev) => [...prev, evt]);
          if (evt.status === 'COMPLETED' || evt.status === 'FAILED') {
            setIsRunning(false);
          }
        },
        (err) => {
          console.warn('SSE stream notice:', err);
          setIsRunning(false);
        }
      );
    } catch (err: any) {
      console.info('Backend offline: running interactive UI simulation');
      // Smooth interactive UI demonstration
      setTimeout(() => {
        setIsRunning(false);
      }, 2200);
    }
  };

  return (
    <div className="flex flex-col w-full pb-10 space-y-6">
      {/* Top Workspace Micro-Header & Sovereign Clearance Bar */}
      <div className="w-full bg-surface-container-lowest rounded-xl p-4 shadow-sm border border-outline-variant/30">
        <div className="flex flex-col lg:flex-row lg:items-center lg:justify-between gap-3">
          {/* Breadcrumb + Hierarchy */}
          <div className="flex flex-wrap items-center gap-1.5 text-xs">
            <span className="text-outline hover:text-on-surface cursor-pointer transition-colors">Workspaces</span>
            <ChevronRight className="w-3.5 h-3.5 text-outline-variant" />
            <span className="text-on-surface-variant font-medium">Crude Distillation Unit (CDU-02)</span>
            <ChevronRight className="w-3.5 h-3.5 text-outline-variant" />
            <span className="text-primary font-semibold tracking-tight">Anomaly Remediation</span>
            <span className="mx-1 font-mono text-[10px] px-2 py-0.5 rounded bg-surface-container-high text-tertiary-fixed-dim border border-outline-variant/30">
              SESSION #{activeTask}
            </span>
          </div>

          {/* Autonomous Agent Status & Switchers */}
          <div className="flex flex-wrap items-center gap-2">
            {/* Live Pill */}
            <div className="flex items-center gap-2 px-3 py-1.5 rounded-full bg-surface-container-high border border-outline-variant/30 shadow-inner">
              <span className="relative flex h-2 w-2">
                <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-primary-container opacity-75" />
                <span className="relative inline-flex rounded-full h-2 w-2 bg-primary-container shadow-[0_0_8px_#00e5ff]" />
              </span>
              <span className="font-mono text-[10px] uppercase tracking-wider text-primary-container font-bold">
                {isRunning ? 'AGENT GENERATING...' : 'AUTONOMOUS REASONING ACTIVE'}
              </span>
            </div>

            {/* Quick Switcher: Router */}
            <div className="flex items-center gap-1.5 px-3 py-1.5 rounded bg-surface-container border border-outline-variant/30 text-on-surface-variant text-xs hover:text-on-surface cursor-pointer transition-colors">
              <Shuffle className="w-3.5 h-3.5 text-secondary" />
              <span className="font-mono text-[10px] text-outline font-semibold">ROUTER:</span>
              <span className="font-mono text-[10px] font-bold text-secondary-fixed">AUTO (Adaptive)</span>
            </div>

            {/* Strict Air-Gap Enforcer */}
            <div className="flex items-center gap-1.5 px-3 py-1.5 rounded bg-surface-container border border-outline-variant/30 text-tertiary font-mono text-[10px]">
              <Lock className="w-3.5 h-3.5 text-tertiary" />
              <span className="tracking-wide">AIR-GAP:</span>
              <span className="font-bold text-tertiary-fixed">STRICT</span>
            </div>
          </div>
        </div>
      </div>

      {errorMsg && (
        <div className="p-3 rounded-lg bg-rose-500/10 border border-rose-500/40 text-rose-300 flex items-center gap-2 text-xs font-mono">
          <AlertCircle className="w-4 h-4 shrink-0 text-rose-400" />
          <span>{errorMsg}</span>
        </div>
      )}

      {/* Primary Grid Canvas: 12-Column System */}
      <div className="grid grid-cols-12 gap-6 items-start">
        {/* Left + Center Stream (8 Columns) */}
        <div className="col-span-12 xl:col-span-8 flex flex-col space-y-6">
          <CommandDeck onExecute={handleExecute} isLoading={isRunning} />
          <NeuralRouterStream activeModel={isRunning ? 'qwen3.5:4b' : 'qwen3.5:4b'} />
          <RecommendationCard />
          <OpticalSensorsPreview />
        </div>

        {/* Right Side Rail: Execution Timeline & Sources (4 Columns) */}
        <div className="col-span-12 xl:col-span-4 flex flex-col space-y-6">
          <WorkflowTimeline taskId={activeTask} events={events} isRunning={isRunning} />
          <SourcesPanel />
          <LocalEnclaveCard />
        </div>
      </div>
    </div>
  );
};
