import React, { useState } from 'react';
import { 
  CheckCircle2, 
  Loader2, 
  AlertCircle, 
  ChevronDown, 
  ChevronRight, 
  Cpu, 
  Search, 
  Calculator, 
  FileText, 
  ShieldAlert, 
  Download, 
  ExternalLink,
  Code2,
  Eye,
  CheckCheck,
  FileCheck
} from 'lucide-react';
import { TaskEvent } from '../../types/task';
import { Artifact } from '../../types/artifact';
import { getArtifactDownloadUrl } from '../../api/artifacts';
import { Link } from 'react-router-dom';

interface TaskEventStreamProps {
  prompt: string;
  attachedFiles?: string[];
  events: TaskEvent[];
  status: 'idle' | 'running' | 'completed' | 'failed';
  finalOutput?: string | null;
  error?: string | null;
  artifacts?: Artifact[];
}

export const TaskEventStream: React.FC<TaskEventStreamProps> = ({
  prompt,
  attachedFiles = [],
  events = [],
  status,
  finalOutput,
  error,
  artifacts = [],
}) => {
  const [stepsOpen, setStepsOpen] = useState(true);

  // Group events into logical steps
  const toolEvents = events.filter((e) => e.event_type === 'tool_call' || e.event_type === 'node_start' || e.event_type === 'node_finish' || e.event_type === 'model_route');

  const getToolIcon = (toolName?: string) => {
    switch (toolName) {
      case 'ocr_document':
        return <FileText className="w-3.5 h-3.5 text-amber-500" />;
      case 'search_knowledge':
        return <Search className="w-3.5 h-3.5 text-sky-500" />;
      case 'vision_analyze':
        return <Eye className="w-3.5 h-3.5 text-purple-500" />;
      case 'calculate':
        return <Calculator className="w-3.5 h-3.5 text-emerald-500" />;
      case 'run_code':
        return <Code2 className="w-3.5 h-3.5 text-indigo-500" />;
      case 'create_docx':
      case 'create_xlsx':
      case 'create_pptx':
        return <FileCheck className="w-3.5 h-3.5 text-emerald-600" />;
      case 'model_route':
        return <Cpu className="w-3.5 h-3.5 text-sky-600" />;
      default:
        return <CheckCircle2 className="w-3.5 h-3.5 text-slate-400" />;
    }
  };

  return (
    <div className="w-full space-y-6 pb-24">
      {/* 1. User Message Block */}
      <div className="flex items-start gap-3">
        <div className="w-7 h-7 rounded-full bg-slate-900 dark:bg-slate-100 text-white dark:text-slate-900 font-bold text-xs flex items-center justify-center flex-shrink-0 font-mono mt-0.5 shadow-sm">
          U
        </div>
        <div className="flex-1 space-y-2">
          <div className="text-xs font-semibold text-slate-500 dark:text-slate-400 font-mono uppercase">
            User Command
          </div>
          <div className="p-3.5 rounded-xl bg-slate-100 dark:bg-slate-900 border border-slate-200 dark:border-slate-800 text-slate-900 dark:text-slate-100 text-sm font-medium leading-relaxed">
            {prompt}
          </div>
          {attachedFiles.length > 0 && (
            <div className="flex flex-wrap items-center gap-2 pt-1">
              {attachedFiles.map((fname, idx) => (
                <span
                  key={idx}
                  className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-md bg-white dark:bg-slate-800/80 text-xs text-slate-700 dark:text-slate-300 border border-slate-200 dark:border-slate-700 font-mono shadow-xs"
                >
                  <FileText className="w-3 h-3 text-sky-500" />
                  <span>{fname}</span>
                </span>
              ))}
            </div>
          )}
        </div>
      </div>

      {/* 2. Agent Execution Steps Accordion (Codex Style) */}
      {(events.length > 0 || status === 'running') && (
        <div className="flex items-start gap-3">
          <div className="w-7 h-7 rounded-full bg-sky-600 text-white font-bold text-xs flex items-center justify-center flex-shrink-0 font-mono mt-0.5 shadow-sm">
            ▲
          </div>
          <div className="flex-1 space-y-3">
            <div className="flex items-center justify-between">
              <button
                type="button"
                onClick={() => setStepsOpen((prev) => !prev)}
                className="flex items-center gap-2 text-xs font-mono font-semibold text-slate-600 dark:text-slate-400 hover:text-slate-900 dark:hover:text-slate-200 transition-colors cursor-pointer"
              >
                {stepsOpen ? <ChevronDown className="w-3.5 h-3.5" /> : <ChevronRight className="w-3.5 h-3.5" />}
                <span>Agent Execution Trace ({toolEvents.length} steps)</span>
                {status === 'running' && (
                  <span className="flex items-center gap-1 text-sky-600 dark:text-sky-400">
                    <Loader2 className="w-3 h-3 animate-spin" />
                    <span>Processing...</span>
                  </span>
                )}
              </button>

              <span className="text-[11px] font-mono text-slate-400">
                127.0.0.1 Air-Gap
              </span>
            </div>

            {stepsOpen && (
              <div className="rounded-xl border border-slate-200 dark:border-slate-800 bg-white/60 dark:bg-slate-900/60 divide-y divide-slate-100 dark:divide-slate-800/60 overflow-hidden shadow-xs">
                {events.map((evt, idx) => (
                  <div key={idx} className="p-3 text-xs flex items-start gap-2.5">
                    <div className="mt-0.5 flex-shrink-0">
                      {evt.status === 'completed' || evt.status === 'success' ? (
                        <CheckCircle2 className="w-3.5 h-3.5 text-emerald-500" />
                      ) : evt.status === 'running' ? (
                        <Loader2 className="w-3.5 h-3.5 text-sky-500 animate-spin" />
                      ) : evt.status === 'failed' || evt.status === 'error' ? (
                        <AlertCircle className="w-3.5 h-3.5 text-rose-500" />
                      ) : (
                        getToolIcon(evt.event_type)
                      )}
                    </div>

                    <div className="flex-1 min-w-0 space-y-1">
                      <div className="flex items-center justify-between">
                        <span className="font-semibold text-slate-800 dark:text-slate-200 font-mono text-[11px]">
                          {evt.event_type === 'tool_call'
                            ? `Tool: ${evt.summary || 'Execute'}`
                            : evt.event_type === 'node_start'
                            ? `Node: ${evt.summary || 'Start'}`
                            : evt.event_type === 'model_route'
                            ? `Router: ${evt.summary || 'Model Selection'}`
                            : evt.summary || evt.event_type}
                        </span>
                        {evt.timestamp && (
                          <span className="text-[10px] text-slate-400 font-mono">
                            {new Date(evt.timestamp).toLocaleTimeString()}
                          </span>
                        )}
                      </div>

                      {evt.detail && (
                        <div className="text-slate-600 dark:text-slate-400 font-sans text-xs break-words">
                          {typeof evt.detail === 'string'
                            ? evt.detail
                            : JSON.stringify(evt.detail, null, 2)}
                        </div>
                      )}
                    </div>
                  </div>
                ))}
              </div>
            )}
          </div>
        </div>
      )}

      {/* 3. Final AI Synthesis / Deliverable Output */}
      {finalOutput && (
        <div className="flex items-start gap-3">
          <div className="w-7 h-7 rounded-full bg-emerald-600 text-white font-bold text-xs flex items-center justify-center flex-shrink-0 font-mono mt-0.5 shadow-sm">
            ✓
          </div>
          <div className="flex-1 space-y-4">
            <div className="flex items-center justify-between">
              <span className="text-xs font-semibold text-emerald-700 dark:text-emerald-400 font-mono uppercase tracking-wider">
                Synthesized Engineering Response
              </span>
              <span className="text-[10px] px-2 py-0.5 rounded-full bg-emerald-50 dark:bg-emerald-950 border border-emerald-200 dark:border-emerald-800 text-emerald-700 dark:text-emerald-300 font-mono">
                Verified Facts & RAG Grounded
              </span>
            </div>

            {/* Markdown Render Container */}
            <div className="p-5 rounded-xl bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 text-slate-800 dark:text-slate-200 text-sm leading-relaxed shadow-xs prose dark:prose-invert max-w-none">
              <div className="whitespace-pre-wrap font-sans">
                {finalOutput}
              </div>
            </div>

            {/* Generated Deliverables Cards */}
            {artifacts.length > 0 && (
              <div className="space-y-2 pt-2">
                <div className="text-xs font-mono font-bold text-slate-500 uppercase tracking-wider">
                  Generated Deliverables
                </div>
                <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
                  {artifacts.map((art) => (
                    <div
                      key={art.id}
                      className="p-3.5 rounded-xl border border-slate-200 dark:border-slate-800 bg-white dark:bg-slate-900 flex items-center justify-between gap-3 shadow-xs hover:border-sky-300 dark:hover:border-sky-700 transition-colors"
                    >
                      <div className="flex items-center gap-3 min-w-0">
                        <div className="w-9 h-9 rounded-lg bg-sky-50 dark:bg-sky-950 border border-sky-200 dark:border-sky-800 flex items-center justify-center text-sky-600 dark:text-sky-400 flex-shrink-0">
                          <FileText className="w-5 h-5" />
                        </div>
                        <div className="flex flex-col min-w-0">
                          <span className="text-xs font-semibold text-slate-900 dark:text-slate-100 truncate">
                            {art.filename}
                          </span>
                          <span className="text-[10px] text-slate-400 font-mono">
                            {(art.file_type || art.kind || 'file').toUpperCase()} · SHA: {art.sha256?.slice(0, 10)}...
                          </span>
                        </div>
                      </div>

                      <div className="flex items-center gap-1.5 flex-shrink-0">
                        <a
                          href={getArtifactDownloadUrl(art.id)}
                          download={art.filename}
                          className="flex items-center gap-1 px-2.5 py-1.5 rounded-lg bg-sky-50 hover:bg-sky-100 dark:bg-sky-950/60 dark:hover:bg-sky-900 text-sky-700 dark:text-sky-300 text-xs font-medium border border-sky-200 dark:border-sky-800 transition-colors cursor-pointer"
                        >
                          <Download className="w-3.5 h-3.5" />
                          <span>Download</span>
                        </a>

                        {art.status === 'pending_review' && (
                          <Link
                            to="/review"
                            className="flex items-center gap-1 px-2.5 py-1.5 rounded-lg bg-emerald-50 hover:bg-emerald-100 dark:bg-emerald-950/60 dark:hover:bg-emerald-900 text-emerald-700 dark:text-emerald-300 text-xs font-medium border border-emerald-200 dark:border-emerald-800 transition-colors"
                          >
                            <CheckCheck className="w-3.5 h-3.5" />
                            <span>Review</span>
                          </Link>
                        )}
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            )}
          </div>
        </div>
      )}

      {/* 4. Error Block */}
      {error && (
        <div className="flex items-start gap-3">
          <div className="w-7 h-7 rounded-full bg-rose-600 text-white font-bold text-xs flex items-center justify-center flex-shrink-0 font-mono mt-0.5">
            !
          </div>
          <div className="flex-1 p-4 rounded-xl bg-rose-50 dark:bg-rose-950/40 border border-rose-200 dark:border-rose-900/60 text-rose-800 dark:text-rose-200 text-xs space-y-1">
            <div className="font-bold flex items-center gap-1.5">
              <ShieldAlert className="w-4 h-4 text-rose-600 dark:text-rose-400" />
              <span>Execution Error</span>
            </div>
            <p className="font-mono">{error}</p>
          </div>
        </div>
      )}
    </div>
  );
};
