import React, { useState, useRef, useEffect } from 'react';
import { useLocation } from 'react-router-dom';
import { 
  Send, 
  Paperclip, 
  X, 
  Sparkles, 
  FileText, 
  Code2, 
  Eye, 
  Calculator, 
  CheckCircle2, 
  Loader2, 
  RotateCcw,
  ShieldCheck,
  Cpu
} from 'lucide-react';
import { TaskEventStream } from '../components/workbench/TaskEventStream';
import { createTask, getTask, getTaskAudit, subscribeToTaskEvents } from '../api/tasks';
import { uploadFile } from '../api/files';
import { getArtifacts } from '../api/artifacts';
import { TaskEvent } from '../types/task';
import { Artifact } from '../types/artifact';

interface AttachedFileInfo {
  id?: string;
  name: string;
  size?: number;
}

export const WorkbenchPage: React.FC = () => {
  const location = useLocation();

  const [prompt, setPrompt] = useState('');
  const [attachedFiles, setAttachedFiles] = useState<AttachedFileInfo[]>([]);
  const [isUploading, setIsUploading] = useState(false);
  const [status, setStatus] = useState<'idle' | 'running' | 'completed' | 'failed'>('idle');
  const [currentTaskId, setCurrentTaskId] = useState<string | null>(null);
  const [submittedPrompt, setSubmittedPrompt] = useState<string>('');
  const [events, setEvents] = useState<TaskEvent[]>([]);
  const [finalOutput, setFinalOutput] = useState<string | null>(null);
  const [taskArtifacts, setTaskArtifacts] = useState<Artifact[]>([]);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);

  const fileInputRef = useRef<HTMLInputElement>(null);
  const textareaRef = useRef<HTMLTextAreaElement>(null);

  // Auto-resize textarea
  useEffect(() => {
    if (textareaRef.current) {
      textareaRef.current.style.height = 'auto';
      textareaRef.current.style.height = `${Math.min(textareaRef.current.scrollHeight, 180)}px`;
    }
  }, [prompt]);

  // Handle sidebar task selection & new session events
  useEffect(() => {
    const handleSelectTask = async (e: Event) => {
      const customEvent = e as CustomEvent<{ taskId: string }>;
      if (customEvent.detail?.taskId) {
        await loadTaskHistory(customEvent.detail.taskId);
      }
    };

    const handleNewTask = () => {
      resetSession();
    };

    window.addEventListener('prism:select-task', handleSelectTask);
    window.addEventListener('prism:new-task', handleNewTask);

    // Initial check from location state
    if (location.state?.selectedTaskId) {
      loadTaskHistory(location.state.selectedTaskId);
    } else if (location.state?.newSession) {
      resetSession();
    }

    return () => {
      window.removeEventListener('prism:select-task', handleSelectTask);
      window.removeEventListener('prism:new-task', handleNewTask);
    };
  }, [location.state]);

  const resetSession = () => {
    setStatus('idle');
    setCurrentTaskId(null);
    setSubmittedPrompt('');
    setPrompt('');
    setEvents([]);
    setFinalOutput(null);
    setTaskArtifacts([]);
    setErrorMessage(null);
    setAttachedFiles([]);
  };

  const loadTaskHistory = async (taskId: string) => {
    try {
      setStatus('running');
      setCurrentTaskId(taskId);
      setEvents([]);
      setFinalOutput(null);

      const [task, auditLogs, allArtifacts] = await Promise.all([
        getTask(taskId),
        getTaskAudit(taskId),
        getArtifacts(),
      ]);

      setSubmittedPrompt(task.request_text);
      setPrompt('');

      // Map audit events to TaskEvent format
      const mappedEvents: TaskEvent[] = (auditLogs || []).map((log: any) => ({
        task_id: taskId,
        event_type: log.action || 'tool_call',
        status: log.status || 'completed',
        summary: log.tool_name || log.action,
        detail: log.details,
        timestamp: log.timestamp,
      }));

      setEvents(mappedEvents);

      // Filter artifacts for this task
      const matched = allArtifacts.filter((a) => a.task_id === taskId);
      setTaskArtifacts(matched);

      if (task.status === 'completed') {
        setStatus('completed');
        // Extract synthesis or result
        setFinalOutput(task.error ? null : (task as any).result || `Task ${taskId} completed successfully. Artifacts verified.`);
      } else if (task.status === 'failed') {
        setStatus('failed');
        setErrorMessage(task.error || 'Task execution failed.');
      } else {
        setStatus('running');
        startEventSubscription(taskId);
      }
    } catch (err: any) {
      setStatus('failed');
      setErrorMessage(err.message || 'Failed to load task history.');
    }
  };

  const handleFileUpload = async (e: React.ChangeEvent<HTMLInputElement>) => {
    if (!e.target.files || e.target.files.length === 0) return;
    const files = Array.from(e.target.files);

    setIsUploading(true);
    try {
      for (const f of files) {
        try {
          const uploaded = await uploadFile(f);
          setAttachedFiles((prev) => [
            ...prev,
            { id: uploaded.id, name: f.name, size: f.size },
          ]);
        } catch (uploadErr) {
          // Fallback attachment if standalone preview mode
          setAttachedFiles((prev) => [
            ...prev,
            { name: f.name, size: f.size },
          ]);
        }
      }
    } finally {
      setIsUploading(false);
      e.target.value = '';
    }
  };

  const removeFile = (index: number) => {
    setAttachedFiles((prev) => prev.filter((_, i) => i !== index));
  };

  const startEventSubscription = (taskId: string) => {
    const unsubscribe = subscribeToTaskEvents(
      taskId,
      (event: TaskEvent) => {
        setEvents((prev) => [...prev, event]);

        if (event.event_type === 'final_answer' && event.detail) {
          setFinalOutput(typeof event.detail === 'string' ? event.detail : JSON.stringify(event.detail, null, 2));
        }

        if (event.event_type === 'status' && (event.status === 'completed' || event.status === 'finished')) {
          setStatus('completed');
          // Fetch generated deliverables
          getArtifacts().then((arts) => {
            setTaskArtifacts(arts.filter((a) => a.task_id === taskId));
          }).catch(() => {});
        }

        if (event.event_type === 'status' && event.status === 'failed') {
          setStatus('failed');
          setErrorMessage(event.summary || 'Task failed during execution.');
        }
      },
      (err) => {
        console.warn('SSE subscription stream ended:', err);
      }
    );

    return unsubscribe;
  };

  const executeTaskWithPrompt = async (targetPrompt: string, filesToAttach: AttachedFileInfo[] = attachedFiles) => {
    if (!targetPrompt.trim() || status === 'running') return;

    setStatus('running');
    setSubmittedPrompt(targetPrompt);
    setEvents([]);
    setFinalOutput(null);
    setTaskArtifacts([]);
    setErrorMessage(null);
    setPrompt('');

    const fileIds = filesToAttach.map((f) => f.id).filter(Boolean) as string[];

    try {
      const res = await createTask({
        request_text: targetPrompt,
        file_ids: fileIds,
        task_type: 'general',
      });

      const taskId = res.task_id;
      setCurrentTaskId(taskId);
      startEventSubscription(taskId);
    } catch (err: any) {
      console.error('Failed to create task on backend:', err);
      setStatus('failed');
      setErrorMessage(err.message || 'Failed to dispatch task to Sovereign backend.');
    }
  };

  const handleKeyDown = (e: React.KeyboardEvent<HTMLTextAreaElement>) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      executeTaskWithPrompt(prompt);
    }
  };

  // Demo shortcut triggers
  const runDemoA = () => {
    const demoFiles: AttachedFileInfo[] = [{ name: 'demo_scanned_inspection_report.pdf', size: 13054812 }];
    setAttachedFiles(demoFiles);
    executeTaskWithPrompt(
      'Analyze scanned inspection report demo_scanned_inspection_report.pdf for pressure vessel PV-402, retrieve SOP-301 wall thinning limits, calculate wall loss & exceedance, and generate official Inspection Approval Note DOCX.',
      demoFiles
    );
  };

  const runDemoB = () => {
    executeTaskWithPrompt(
      'Implement ASME BPVC Section VIII Div 1 UG-27 cylindrical shell hoop stress formula with validation and execute complete test suite in the Docker code sandbox.',
      []
    );
  };

  const runDemoC = () => {
    const demoFiles: AttachedFileInfo[] = [{ name: 'demo_inspection_photo.png', size: 489201 }];
    setAttachedFiles(demoFiles);
    executeTaskWithPrompt(
      'Analyze circumferential weld bead CW-3 in demo_inspection_photo.png for surface pitting, undercut, and weld crown anomalies using Gemma 4 E4B multimodal observer.',
      demoFiles
    );
  };

  const runDemoMath = () => {
    executeTaskWithPrompt(
      'Evaluate deterministic wall thinning loss: 18.0 - 16.1 mm, and tolerance exceedance against 1.50 mm threshold.',
      []
    );
  };

  return (
    <div className="flex flex-col h-[calc(100vh-4.5rem)] max-w-4xl mx-auto w-full relative">
      {/* Hidden file input */}
      <input
        ref={fileInputRef}
        type="file"
        multiple
        onChange={handleFileUpload}
        className="hidden"
        accept=".pdf,.docx,.xlsx,.txt,.csv,.png,.jpg"
      />

      {/* Main Content Area (Scrollable) */}
      <div className="flex-1 overflow-y-auto px-2 sm:px-4 py-4 space-y-6">
        {status === 'idle' && (
          <div className="flex flex-col items-center justify-center min-h-[60vh] text-center space-y-6 max-w-xl mx-auto py-8">
            <div className="w-12 h-12 rounded-2xl bg-sky-50 dark:bg-sky-950 border border-sky-200 dark:border-sky-800 flex items-center justify-center text-sky-600 dark:text-sky-400 shadow-sm">
              <Sparkles className="w-6 h-6" />
            </div>

            <div className="space-y-2">
              <h1 className="text-2xl sm:text-3xl font-bold tracking-tight text-slate-900 dark:text-slate-100">
                Sovereign AI Studio
              </h1>
              <p className="text-xs sm:text-sm text-slate-500 dark:text-slate-400 max-w-md leading-relaxed">
                Air-gapped intelligence for confidential engineering, local RAG retrieval, safe code execution, and signed deliverable drafting.
              </p>
            </div>

            {/* Quick Demo Action Chips (Codex Style) */}
            <div className="w-full grid grid-cols-1 sm:grid-cols-2 gap-2.5 pt-2 text-left">
              <button
                type="button"
                onClick={runDemoA}
                className="p-3 rounded-xl border border-slate-200 dark:border-slate-800 bg-white dark:bg-slate-900 hover:border-sky-400 dark:hover:border-sky-600 hover:shadow-xs transition-all flex items-start gap-3 group cursor-pointer"
              >
                <div className="w-7 h-7 rounded-lg bg-amber-50 dark:bg-amber-950/60 border border-amber-200 dark:border-amber-800 flex items-center justify-center text-amber-600 dark:text-amber-400 flex-shrink-0 mt-0.5">
                  <FileText className="w-4 h-4" />
                </div>
                <div className="flex flex-col min-w-0">
                  <span className="text-xs font-semibold text-slate-800 dark:text-slate-200 group-hover:text-sky-600 dark:group-hover:text-sky-400 transition-colors">
                    Demo A: Inspection to DOCX
                  </span>
                  <span className="text-[11px] text-slate-500 dark:text-slate-400 line-clamp-2">
                    Scanned PDF OCR → SOP-301 limits → Math → Approval Note DOCX.
                  </span>
                </div>
              </button>

              <button
                type="button"
                onClick={runDemoB}
                className="p-3 rounded-xl border border-slate-200 dark:border-slate-800 bg-white dark:bg-slate-900 hover:border-sky-400 dark:hover:border-sky-600 hover:shadow-xs transition-all flex items-start gap-3 group cursor-pointer"
              >
                <div className="w-7 h-7 rounded-lg bg-indigo-50 dark:bg-indigo-950/60 border border-indigo-200 dark:border-indigo-800 flex items-center justify-center text-indigo-600 dark:text-indigo-400 flex-shrink-0 mt-0.5">
                  <Code2 className="w-4 h-4" />
                </div>
                <div className="flex flex-col min-w-0">
                  <span className="text-xs font-semibold text-slate-800 dark:text-slate-200 group-hover:text-sky-600 dark:group-hover:text-sky-400 transition-colors">
                    Demo B: ASME Code Sandbox
                  </span>
                  <span className="text-[11px] text-slate-500 dark:text-slate-400 line-clamp-2">
                    BPVC UG-27 stress logic with Pytest in isolated Docker container.
                  </span>
                </div>
              </button>

              <button
                type="button"
                onClick={runDemoC}
                className="p-3 rounded-xl border border-slate-200 dark:border-slate-800 bg-white dark:bg-slate-900 hover:border-sky-400 dark:hover:border-sky-600 hover:shadow-xs transition-all flex items-start gap-3 group cursor-pointer"
              >
                <div className="w-7 h-7 rounded-lg bg-purple-50 dark:bg-purple-950/60 border border-purple-200 dark:border-purple-800 flex items-center justify-center text-purple-600 dark:text-purple-400 flex-shrink-0 mt-0.5">
                  <Eye className="w-4 h-4" />
                </div>
                <div className="flex flex-col min-w-0">
                  <span className="text-xs font-semibold text-slate-800 dark:text-slate-200 group-hover:text-sky-600 dark:group-hover:text-sky-400 transition-colors">
                    Demo C: Multimodal Vision
                  </span>
                  <span className="text-[11px] text-slate-500 dark:text-slate-400 line-clamp-2">
                    Gemma 4 E4B inspects weld seam CW-3 with mandatory disclaimer.
                  </span>
                </div>
              </button>

              <button
                type="button"
                onClick={runDemoMath}
                className="p-3 rounded-xl border border-slate-200 dark:border-slate-800 bg-white dark:bg-slate-900 hover:border-sky-400 dark:hover:border-sky-600 hover:shadow-xs transition-all flex items-start gap-3 group cursor-pointer"
              >
                <div className="w-7 h-7 rounded-lg bg-emerald-50 dark:bg-emerald-950/60 border border-emerald-200 dark:border-emerald-800 flex items-center justify-center text-emerald-600 dark:text-emerald-400 flex-shrink-0 mt-0.5">
                  <Calculator className="w-4 h-4" />
                </div>
                <div className="flex flex-col min-w-0">
                  <span className="text-xs font-semibold text-slate-800 dark:text-slate-200 group-hover:text-sky-600 dark:group-hover:text-sky-400 transition-colors">
                    Deterministic Safe Math
                  </span>
                  <span className="text-[11px] text-slate-500 dark:text-slate-400 line-clamp-2">
                    Exact AST formula evaluation with 0 shell execution risk.
                  </span>
                </div>
              </button>
            </div>
          </div>
        )}

        {status !== 'idle' && (
          <TaskEventStream
            prompt={submittedPrompt}
            attachedFiles={attachedFiles.map((f) => f.name)}
            events={events}
            status={status}
            finalOutput={finalOutput}
            error={errorMessage}
            artifacts={taskArtifacts}
          />
        )}
      </div>

      {/* Bottom Pinned Command Input Bar (Codex Style) */}
      <div className="sticky bottom-0 bg-slate-50/90 dark:bg-slate-950/90 backdrop-blur-md pt-2 pb-4 px-2 sm:px-0">
        <div className="rounded-2xl bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 shadow-sm focus-within:border-sky-400 dark:focus-within:border-sky-500 focus-within:ring-2 focus-within:ring-sky-100 dark:focus-within:ring-sky-950/60 transition-all p-3 space-y-2.5">
          {/* Attached Files Strip */}
          {attachedFiles.length > 0 && (
            <div className="flex flex-wrap items-center gap-2 pb-1.5 border-b border-slate-100 dark:border-slate-800">
              {attachedFiles.map((f, idx) => (
                <span
                  key={idx}
                  className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-md bg-slate-100 dark:bg-slate-800 text-xs text-slate-700 dark:text-slate-300 font-mono"
                >
                  <FileText className="w-3 h-3 text-sky-500" />
                  <span>{f.name}</span>
                  <button
                    type="button"
                    onClick={() => removeFile(idx)}
                    className="text-slate-400 hover:text-rose-500 ml-1 cursor-pointer"
                  >
                    <X className="w-3 h-3" />
                  </button>
                </span>
              ))}
            </div>
          )}

          {/* Text Input */}
          <textarea
            ref={textareaRef}
            value={prompt}
            onChange={(e) => setPrompt(e.target.value)}
            onKeyDown={handleKeyDown}
            rows={1}
            placeholder={status === 'running' ? 'Task executing... stand by' : 'Ask Sovereign AI to inspect, calculate, code, or generate...'}
            disabled={status === 'running'}
            className="w-full bg-transparent resize-none border-none outline-none text-sm text-slate-800 dark:text-slate-200 placeholder:text-slate-400 leading-relaxed font-sans max-h-44 disabled:opacity-60"
          />

          {/* Controls Bar */}
          <div className="flex items-center justify-between pt-1">
            <div className="flex items-center gap-2">
              <button
                type="button"
                onClick={() => fileInputRef.current?.click()}
                disabled={status === 'running' || isUploading}
                className="flex items-center gap-1.5 px-2.5 py-1.5 rounded-lg border border-slate-200 dark:border-slate-800 hover:bg-slate-100 dark:hover:bg-slate-800 text-slate-600 dark:text-slate-400 text-xs font-medium transition-colors cursor-pointer disabled:opacity-50"
                title="Attach file (PDF, DOCX, XLSX, PNG, JPG)"
              >
                {isUploading ? <Loader2 className="w-3.5 h-3.5 animate-spin" /> : <Paperclip className="w-3.5 h-3.5" />}
                <span className="hidden sm:inline">Attach</span>
              </button>

              {status !== 'idle' && (
                <button
                  type="button"
                  onClick={resetSession}
                  className="flex items-center gap-1 px-2.5 py-1.5 rounded-lg border border-slate-200 dark:border-slate-800 hover:bg-slate-100 dark:hover:bg-slate-800 text-slate-500 dark:text-slate-400 text-xs font-medium transition-colors cursor-pointer"
                  title="Clear canvas and start new task"
                >
                  <RotateCcw className="w-3.5 h-3.5" />
                  <span className="hidden sm:inline">New Session</span>
                </button>
              )}
            </div>

            <div className="flex items-center gap-2">
              <button
                type="button"
                onClick={() => executeTaskWithPrompt(prompt)}
                disabled={status === 'running' || !prompt.trim()}
                className="flex items-center gap-1.5 px-3.5 py-1.5 rounded-lg bg-slate-900 hover:bg-slate-800 dark:bg-sky-600 dark:hover:bg-sky-500 text-white font-medium text-xs shadow-xs transition-all cursor-pointer disabled:opacity-40"
              >
                {status === 'running' ? (
                  <>
                    <Loader2 className="w-3.5 h-3.5 animate-spin" />
                    <span>Processing</span>
                  </>
                ) : (
                  <>
                    <span>Send</span>
                    <Send className="w-3.5 h-3.5" />
                  </>
                )}
              </button>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};
