import React from 'react';
import { Check, RefreshCw, Clock } from 'lucide-react';
import { TaskEvent } from '../../types/task';

interface WorkflowTimelineProps {
  taskId?: string;
  events?: TaskEvent[];
  isRunning?: boolean;
}

export const WorkflowTimeline: React.FC<WorkflowTimelineProps> = ({
  taskId = 'PRISM-88219',
  events = [],
  isRunning = false,
}) => {
  // Static fallback steps matching Stitch design if no dynamic events yet
  const defaultSteps = [
    {
      title: 'Request received & validated',
      desc: 'Local session token verified',
      duration: '18ms',
      status: 'completed',
    },
    {
      title: 'User clearance verified',
      desc: 'CONFIDENTIAL tier match confirmed',
      duration: '42ms',
      status: 'completed',
    },
    {
      title: 'Documents parsed & text extracted',
      desc: 'CDU_SOP.pdf + Log_Sept.pdf',
      duration: '180ms',
      status: 'completed',
    },
    {
      title: 'PaddleOCR completed',
      desc: 'Extracted ultrasonic thickness gauge',
      duration: '95ms',
      status: 'completed',
    },
    {
      title: 'Secure retrieval executed',
      desc: '12 confidential chunks via ChromaDB',
      duration: '324ms',
      status: 'completed',
    },
    {
      title: 'AI reasoning & stress calc',
      desc: 'ASTM A106 Grade B limits matching',
      duration: '1.2s...',
      status: isRunning ? 'active' : 'completed',
    },
    {
      title: 'Calculation verification & integrity',
      desc: 'Euler-Bernoulli stress model',
      duration: '--',
      status: 'pending',
    },
    {
      title: 'Human review gate validation',
      desc: 'Awaiting Level-3 Officer signoff',
      duration: '--',
      status: 'pending',
    },
    {
      title: 'Deliverable generation',
      desc: 'Final CAPEX memo compile (DOCX)',
      duration: '--',
      status: 'pending',
    },
  ];

  return (
    <div className="rounded-xl bg-surface-container-lowest p-4 shadow-sm border border-outline-variant/30">
      <div className="flex items-center justify-between pb-3 mb-3 border-b border-outline-variant/20">
        <div>
          <div className="font-mono text-[10px] uppercase text-outline tracking-wider font-bold">
            EXECUTION TIMELINE
          </div>
          <div className="font-mono text-xs text-primary-container font-semibold">
            TASK #{taskId}
          </div>
        </div>
        <span className="font-mono text-[10px] px-2 py-0.5 rounded bg-surface-container text-tertiary border border-outline-variant/20">
          1.86s total
        </span>
      </div>

      {/* Vertical Pipeline Steps */}
      <div className="relative pl-6 space-y-4 before:absolute before:left-2 before:top-2 before:bottom-2 before:w-px before:bg-surface-container-highest">
        {defaultSteps.map((step, idx) => {
          const isDone = step.status === 'completed';
          const isActive = step.status === 'active';

          return (
            <div
              key={idx}
              className={`relative flex items-start justify-between text-xs transition-all ${
                isActive ? 'bg-surface-container-high/40 -ml-2 p-2 rounded-lg' : ''
              } ${step.status === 'pending' ? 'opacity-40' : ''}`}
            >
              {/* Step Marker */}
              {isDone && (
                <div className="absolute -left-6 top-0.5 w-4 h-4 rounded-full bg-surface-container flex items-center justify-center border border-tertiary/40">
                  <Check className="w-2.5 h-2.5 text-tertiary" />
                </div>
              )}
              {isActive && (
                <div className="absolute -left-4 top-2.5 w-4 h-4 rounded-full bg-surface-container-lowest flex items-center justify-center">
                  <span className="relative flex h-2.5 w-2.5">
                    <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-primary-container opacity-75" />
                    <span className="relative inline-flex rounded-full h-2.5 w-2.5 bg-primary-container shadow-[0_0_8px_#00e5ff]" />
                  </span>
                </div>
              )}
              {step.status === 'pending' && (
                <div className="absolute -left-6 top-1 w-3.5 h-3.5 rounded-full bg-surface-container-highest" />
              )}

              {/* Step Content */}
              <div className="min-w-0 pr-2">
                <div
                  className={`font-medium truncate ${
                    isActive ? 'text-primary-container font-semibold flex items-center gap-1.5' : 'text-on-surface'
                  }`}
                >
                  <span>{step.title}</span>
                  {isActive && <RefreshCw className="w-3 h-3 animate-spin text-primary-container" />}
                </div>
                <div className="font-mono text-[10px] text-on-surface-variant truncate">{step.desc}</div>
              </div>

              {/* Step Duration */}
              <span
                className={`font-mono text-[10px] shrink-0 ${
                  isActive ? 'text-primary-container animate-pulse font-bold' : isDone ? 'text-tertiary font-medium' : 'text-on-surface-variant/60'
                }`}
              >
                {step.duration}
              </span>
            </div>
          );
        })}
      </div>
    </div>
  );
};
