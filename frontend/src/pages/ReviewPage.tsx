import React, { useState } from 'react';
import { 
  CheckCircle, 
  Lock, 
  Key, 
  ArrowRight, 
  FileText, 
  AlertCircle,
  ExternalLink,
  Check
} from 'lucide-react';

interface QueueItem {
  id: string;
  title: string;
  dept: string;
  time: string;
  status: 'Pending' | 'Approved';
}

export const ReviewPage: React.FC = () => {
  const [isApproved, setIsApproved] = useState(false);
  const [queue, setQueue] = useState<QueueItem[]>([
    {
      id: 'q-1',
      title: 'Turnaround Boiler Safety Audit',
      dept: 'Safety Dept',
      time: '14 mins ago',
      status: 'Pending',
    },
    {
      id: 'q-2',
      title: 'Sulfur Recovery Unit Calculation Sheet',
      dept: 'Engineering',
      time: '1 hour ago',
      status: 'Pending',
    },
    {
      id: 'q-3',
      title: 'Desalter Valve Procurement RFP',
      dept: 'Procurement',
      time: 'Yesterday',
      status: 'Approved',
    },
  ]);

  const handleApprove = () => {
    setIsApproved(true);
  };

  return (
    <div className="flex flex-col w-full max-w-6xl mx-auto pb-12 space-y-6">
      {/* Top Header */}
      <div className="pt-2">
        <h1 className="text-2xl font-bold text-slate-900 dark:text-slate-100 tracking-tight font-headline">
          Human Review Gate
        </h1>
        <p className="text-xs text-slate-500 dark:text-slate-400 mt-0.5">
          Executive authorization required for critical operational deliverables.
        </p>
      </div>

      {/* Main Review Card */}
      <div className="rounded-xl bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 p-6 shadow-sm space-y-5">
        {/* Card Header & Requisition Total */}
        <div className="flex flex-col sm:flex-row sm:items-start justify-between gap-3">
          <div className="flex items-center gap-2">
            <span className="px-2 py-0.5 rounded border border-amber-300 dark:border-amber-700 bg-amber-50 dark:bg-amber-950/40 text-amber-700 dark:text-amber-300 font-mono text-[10px] font-bold tracking-wider uppercase">
              ACTION REQUIRED
            </span>
            <span className="font-mono text-xs text-slate-400">
              DOC-GATE-2024-088
            </span>
          </div>

          <div className="text-left sm:text-right">
            <div className="font-mono text-[10px] uppercase font-bold text-slate-400 tracking-wider">
              REQUISITION TOTAL
            </div>
            <div className="text-2xl font-bold text-slate-900 dark:text-slate-100 font-headline">
              $42,800.00
            </div>
          </div>
        </div>

        {/* Title & Scope */}
        <div>
          <h2 className="text-xl font-bold text-slate-900 dark:text-slate-100 tracking-tight font-headline">
            CAPEX Approval Note: CDU Flange Replacement
          </h2>
          <p className="text-xs text-slate-600 dark:text-slate-300 mt-1 leading-relaxed">
            Replacement of stress-corroded carbon steel components with high-nickel alloy in Crude Distillation Unit (CDU-1) overhead circuit.
          </p>
        </div>

        {/* AI Recommendation Box */}
        <div className="rounded-lg bg-slate-50 dark:bg-slate-950/50 border border-slate-200 dark:border-slate-800 p-4 space-y-1.5">
          <div className="font-mono text-[10px] uppercase font-bold text-slate-400 tracking-wider">
            AI RECOMMENDATION
          </div>
          <p className="text-xs text-slate-800 dark:text-slate-200 leading-relaxed font-normal">
            Procurement of <strong className="font-semibold text-slate-900 dark:text-white">Inconel 625 clad flange assembly</strong>. Eliminates unscheduled outage exposure projected at <strong className="font-semibold text-slate-900 dark:text-white">$320,000/day</strong> during high-throughput crude run by mitigating ultrasound-detected wall thinning.
          </p>
        </div>

        {/* 3 Verified Badges */}
        <div className="grid grid-cols-1 md:grid-cols-3 gap-3">
          <div className="p-3 rounded-lg border border-slate-200 dark:border-slate-800 bg-slate-50/50 dark:bg-slate-950/30 flex items-center gap-3">
            <div className="w-8 h-8 rounded-full bg-emerald-50 dark:bg-emerald-950/60 border border-emerald-200 dark:border-emerald-800 flex items-center justify-center text-emerald-600 shrink-0">
              <CheckCircle className="w-4 h-4" />
            </div>
            <div>
              <div className="text-xs font-semibold text-slate-900 dark:text-slate-100">8 Verified Sources</div>
              <div className="text-[10px] text-slate-400 font-mono">100% cited grounding</div>
            </div>
          </div>

          <div className="p-3 rounded-lg border border-slate-200 dark:border-slate-800 bg-slate-50/50 dark:bg-slate-950/30 flex items-center gap-3">
            <div className="w-8 h-8 rounded-full bg-sky-50 dark:bg-sky-950/60 border border-sky-200 dark:border-sky-800 flex items-center justify-center text-sky-600 shrink-0">
              <Lock className="w-4 h-4" />
            </div>
            <div>
              <div className="text-xs font-semibold text-slate-900 dark:text-slate-100">Zero Egress</div>
              <div className="text-[10px] text-slate-400 font-mono">Local model runtime</div>
            </div>
          </div>

          <div className="p-3 rounded-lg border border-slate-200 dark:border-slate-800 bg-slate-50/50 dark:bg-slate-950/30 flex items-center gap-3">
            <div className="w-8 h-8 rounded-full bg-emerald-50 dark:bg-emerald-950/60 border border-emerald-200 dark:border-emerald-800 flex items-center justify-center text-emerald-600 shrink-0">
              <Key className="w-4 h-4" />
            </div>
            <div>
              <div className="text-xs font-semibold text-slate-900 dark:text-slate-100">Local Signature</div>
              <div className="text-[10px] text-slate-400 font-mono">Operator 9042 binding</div>
            </div>
          </div>
        </div>

        {/* Action Buttons */}
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 pt-3 border-t border-slate-100 dark:border-slate-800">
          <button
            type="button"
            onClick={() => alert('Deliverable rejected and returned to drafting state.')}
            className="text-rose-600 dark:text-rose-400 hover:text-rose-700 text-xs font-semibold cursor-pointer text-left"
          >
            Reject Deliverable
          </button>

          <div className="flex items-center gap-3">
            <button
              type="button"
              onClick={() => alert('Change request dispatched to autonomous agent.')}
              className="px-4 py-2 rounded-lg border border-slate-200 dark:border-slate-700 hover:bg-slate-50 dark:hover:bg-slate-800 text-slate-700 dark:text-slate-300 text-xs font-medium transition-colors cursor-pointer"
            >
              Request Changes
            </button>

            <button
              type="button"
              onClick={handleApprove}
              className={`flex items-center gap-2 px-5 py-2 rounded-lg text-white font-medium text-xs shadow-sm transition-all cursor-pointer ${
                isApproved 
                  ? 'bg-emerald-600 hover:bg-emerald-500' 
                  : 'bg-emerald-600 hover:bg-emerald-500'
              }`}
            >
              <Check className="w-4 h-4" />
              <span>{isApproved ? 'Approved & Sealed' : 'Approve & Sign'}</span>
            </button>
          </div>
        </div>
      </div>

      {/* Queue Items */}
      <div className="space-y-3">
        <div className="flex items-center justify-between">
          <h2 className="text-sm font-bold text-slate-900 dark:text-slate-100">Queue Items</h2>
          <span className="text-xs text-slate-400 font-mono">3 items awaiting action</span>
        </div>

        <div className="rounded-xl bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 shadow-sm divide-y divide-slate-100 dark:divide-slate-800">
          {queue.map((item) => (
            <div key={item.id} className="p-4 flex items-center justify-between hover:bg-slate-50/60 dark:hover:bg-slate-800/40 transition-colors">
              <div>
                <div className="flex items-center gap-2">
                  <span className="text-xs font-semibold text-slate-900 dark:text-slate-100">
                    {item.title}
                  </span>
                  <span className={`px-2 py-0.2 rounded-full text-[10px] font-mono font-semibold ${
                    item.status === 'Approved'
                      ? 'border border-emerald-300 dark:border-emerald-700 bg-emerald-50 dark:bg-emerald-950/40 text-emerald-700 dark:text-emerald-300'
                      : 'border border-amber-300 dark:border-amber-700 bg-amber-50 dark:bg-amber-950/40 text-amber-700 dark:text-amber-300'
                  }`}>
                    {item.status}
                  </span>
                </div>
                <div className="text-[11px] text-slate-400 mt-0.5">
                  {item.dept} · {item.time}
                </div>
              </div>

              <button
                type="button"
                className="flex items-center gap-1 text-xs font-medium text-slate-500 hover:text-sky-600 dark:hover:text-sky-400 cursor-pointer"
              >
                <span>{item.status === 'Approved' ? 'View' : 'Review'}</span>
                <ArrowRight className="w-3.5 h-3.5" />
              </button>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
};
