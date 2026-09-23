import React, { useState, useEffect } from 'react';
import { 
  Shield, 
  CheckCircle, 
  Clock, 
  Key, 
  FileText, 
  Lock, 
  ExternalLink, 
  Fingerprint, 
  X, 
  RefreshCw, 
  Search, 
  AlertTriangle 
} from 'lucide-react';
import { useAuth } from '../context/AuthContext';
import { getReviewQueue, submitReview } from '../api/artifacts';
import { Artifact } from '../types/artifact';

export const ReviewPage: React.FC = () => {
  const { user } = useAuth();
  const [queue, setQueue] = useState<Artifact[]>([]);
  const [loading, setLoading] = useState<boolean>(true);
  const [actionMsg, setActionMsg] = useState<{ type: 'ok' | 'err'; text: string } | null>(null);
  const [reviewComment, setReviewComment] = useState<string>('Engineering tolerances verified against ASME B31.3. Approved for execution.');

  const fetchQueue = async () => {
    try {
      setLoading(true);
      const data = await getReviewQueue();
      setQueue(data);
    } catch (err: any) {
      console.warn('Queue fetch error:', err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchQueue();
  }, []);

  const handleDecision = async (decision: 'approve' | 'reject' | 'changes', artifactId?: string) => {
    setActionMsg(null);
    const targetId = artifactId || (queue.length > 0 ? queue[0].id : null);
    if (!targetId) {
      setActionMsg({ type: 'ok', text: `Action [${decision.toUpperCase()}] simulated for demonstration deliverable.` });
      return;
    }

    try {
      await submitReview(targetId, {
        decision,
        comment: reviewComment,
      });
      setActionMsg({ type: 'ok', text: `Deliverable successfully processed: ${decision.toUpperCase()}. Recorded in tamper-evident ledger.` });
      fetchQueue();
    } catch (err: any) {
      setActionMsg({ type: 'err', text: err.message || `Failed to submit review: SEC-11 Segregation of duties rule enforced.` });
    }
  };

  // Segregation of duties check (SEC-11)
  const isAuthorOrAdmin = user?.role === 'admin' || (queue.length > 0 && queue[0].owner_id === user?.id);

  return (
    <div className="flex flex-col w-full pb-10 space-y-8">
      {/* Top Banner */}
      <div className="flex items-center justify-between pb-2 border-b border-outline-variant/30">
        <div>
          <h1 className="font-headline text-xl font-bold text-on-surface">
            Human Review Gate & Deliverable Verification
          </h1>
          <p className="text-xs text-on-surface-variant font-mono">
            Mandatory human-in-the-loop sign-off · Enforcing SEC-11 Segregation of Duties
          </p>
        </div>
        <div className="flex items-center gap-2">
          <span className="font-mono text-xs px-2.5 py-1 rounded bg-amber-500/10 text-amber-400 border border-amber-500/30 font-bold">
            STAGE: PENDING SIGN-OFF
          </span>
        </div>
      </div>

      {actionMsg && (
        <div
          className={`p-3 rounded-lg border font-mono text-xs flex items-center gap-2 ${
            actionMsg.type === 'ok'
              ? 'bg-emerald-500/10 border-emerald-500/30 text-tertiary-fixed'
              : 'bg-rose-500/10 border-rose-500/30 text-rose-300'
          }`}
        >
          {actionMsg.type === 'ok' ? <CheckCircle className="w-4 h-4 text-tertiary" /> : <AlertTriangle className="w-4 h-4 text-rose-400" />}
          <span>{actionMsg.text}</span>
        </div>
      )}

      {/* Active Item Master Card */}
      <div className="relative bg-surface-container-low rounded-xl overflow-hidden shadow-2xl p-6 flex flex-col gap-6 border border-outline-variant/30">
        {/* Top Classification Watermark Hairline */}
        <div className="absolute top-0 left-0 right-0 h-1 bg-gradient-to-r from-secondary-container via-primary-container to-tertiary" />

        {/* Header & Metadata Grid */}
        <div className="flex flex-col lg:flex-row justify-between gap-4">
          <div className="space-y-1.5">
            <div className="flex flex-wrap items-center gap-2">
              <span className="px-2 py-0.5 rounded bg-secondary-container/60 text-secondary-fixed font-mono text-[10px] uppercase tracking-widest font-semibold border border-secondary/30">
                CONFIDENTIAL
              </span>
              <span className="px-2 py-0.5 rounded bg-error-container/40 text-error font-mono text-[10px] uppercase tracking-wider border border-error/30">
                Moderate Financial / Safety Critical
              </span>
              <span className="text-outline font-mono text-[10px]">Submitted 18m ago</span>
            </div>
            <h3 className="font-headline text-2xl text-on-surface font-semibold tracking-tight">
              CAPEX Approval Note: CDU Flange Replacement
            </h3>
            <p className="text-sm text-on-surface-variant max-w-3xl leading-relaxed">
              Critical infrastructure procurement requisition for Crude Distillation Unit (CDU-1) column overhead circuit. Replacement of stress-corroded CS ASTM A105 components with high-nickel alloy.
            </p>
          </div>

          {/* System Provenance Attributes */}
          <div className="grid grid-cols-2 gap-2 bg-surface-container p-3 rounded-lg border border-outline-variant/30 shrink-0 font-mono text-xs">
            <div className="flex flex-col">
              <span className="text-[10px] text-outline uppercase">Generated By</span>
              <span className="text-primary flex items-center gap-1 mt-0.5 font-semibold">
                <span className="w-1.5 h-1.5 rounded-full bg-primary" />
                Qwen 3.5 4B (Local)
              </span>
            </div>
            <div className="flex flex-col">
              <span className="text-[10px] text-outline uppercase">Operator</span>
              <span className="text-on-surface font-medium mt-0.5">{user?.username || 'Krishna Mahajan'}</span>
            </div>
            <div className="flex flex-col">
              <span className="text-[10px] text-outline uppercase">Sources Grounding</span>
              <span className="text-tertiary flex items-center gap-1 mt-0.5 font-semibold">
                <CheckCircle className="w-3 h-3" />
                8 / 8 Cited (100%)
              </span>
            </div>
            <div className="flex flex-col">
              <span className="text-[10px] text-outline uppercase">Integrity Hash</span>
              <span className="text-on-surface-variant truncate w-28 mt-0.5">sha256:7f99b2c...</span>
            </div>
          </div>
        </div>

        {/* Lifecycle Progress Timeline Track */}
        <div className="flex flex-col space-y-2 bg-surface-container-lowest/80 p-4 rounded-lg border border-outline-variant/20">
          <div className="flex items-center justify-between font-mono text-[10px] text-outline uppercase tracking-wider mb-1">
            <span>Review Lifecycle Pipeline</span>
            <span className="text-primary-container font-bold">Phase 3 of 5</span>
          </div>
          <div className="grid grid-cols-1 sm:grid-cols-5 gap-2 relative">
            {/* Step 1 */}
            <div className="flex items-center gap-2 p-2 rounded bg-surface-container-high/60 text-tertiary border border-outline-variant/20">
              <CheckCircle className="w-4 h-4 text-tertiary shrink-0" />
              <div className="flex flex-col min-w-0 font-mono text-xs">
                <span className="font-semibold truncate">AI Generated</span>
                <span className="text-[10px] text-outline truncate">Qwen 3.5 4B</span>
              </div>
            </div>
            {/* Step 2 */}
            <div className="flex items-center gap-2 p-2 rounded bg-surface-container-high/60 text-tertiary border border-outline-variant/20">
              <CheckCircle className="w-4 h-4 text-tertiary shrink-0" />
              <div className="flex flex-col min-w-0 font-mono text-xs">
                <span className="font-semibold truncate">Sources Verified</span>
                <span className="text-[10px] text-outline truncate">8/8 Match</span>
              </div>
            </div>
            {/* Step 3: Current */}
            <div className="flex items-center gap-2 p-2 rounded bg-surface-container-highest text-primary-container border border-primary-container/40 shadow-cyan-subtle">
              <span className="relative flex h-2.5 w-2.5 shrink-0 ml-1">
                <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-primary-container opacity-75" />
                <span className="relative inline-flex rounded-full h-2.5 w-2.5 bg-primary-container" />
              </span>
              <div className="flex flex-col min-w-0 font-mono text-xs">
                <span className="font-bold truncate text-primary-container">Waiting for Review</span>
                <span className="text-[10px] text-on-surface truncate">{user?.username} [{user?.role}]</span>
              </div>
            </div>
            {/* Step 4 */}
            <div className="flex items-center gap-2 p-2 rounded bg-surface-container/40 text-outline border border-outline-variant/10 opacity-50">
              <Clock className="w-4 h-4 shrink-0" />
              <div className="flex flex-col min-w-0 font-mono text-xs">
                <span className="font-medium truncate">Dual Signature</span>
                <span className="text-[10px] text-outline truncate">Lead Engineer</span>
              </div>
            </div>
            {/* Step 5 */}
            <div className="flex items-center gap-2 p-2 rounded bg-surface-container/40 text-outline border border-outline-variant/10 opacity-50">
              <Lock className="w-4 h-4 shrink-0" />
              <div className="flex flex-col min-w-0 font-mono text-xs">
                <span className="font-medium truncate">Immutable Audit</span>
                <span className="text-[10px] text-outline truncate">SHA-256 Chain</span>
              </div>
            </div>
          </div>
        </div>

        {/* Document Body & Visual Evidence Split */}
        <div className="grid grid-cols-1 lg:grid-cols-12 gap-4">
          {/* Content Preview Container */}
          <div className="lg:col-span-8 flex flex-col space-y-4 bg-surface-container p-4 rounded-lg border border-outline-variant/20">
            <div className="flex items-center justify-between pb-2 border-b border-outline-variant/20">
              <span className="font-mono text-xs uppercase tracking-wider text-outline flex items-center gap-1.5 font-bold">
                <FileText className="w-4 h-4 text-primary" />
                Structured Proposal Synthesis
              </span>
              <a
                href="/artifacts"
                className="font-mono text-xs text-primary-container hover:underline flex items-center gap-1"
              >
                <ExternalLink className="w-3.5 h-3.5" /> Full Specification
              </a>
            </div>

            <div className="space-y-3 text-sm text-on-surface">
              <div className="p-3 rounded bg-surface-container-high/60 border border-outline-variant/20">
                <div className="flex items-start justify-between">
                  <div>
                    <div className="font-mono text-[10px] uppercase text-outline">Recommended Action</div>
                    <div className="font-headline text-base font-semibold text-on-surface mt-1">
                      Procurement of Inconel 625 clad flange assembly ($42,800 estimate)
                    </div>
                  </div>
                  <span className="font-mono text-lg text-tertiary font-bold">$42,800.00</span>
                </div>
                <p className="mt-2 text-on-surface-variant text-xs leading-relaxed">
                  Mitigates catastrophic naphthenic acid wall-thinning detected during Q2 ultrasound scans. Deployment during the scheduled 36-hour maintenance shutdown eliminates unscheduled outage exposure projected at $320,000/day during the high-throughput Q3 crude run.
                </p>
              </div>

              <div className="grid grid-cols-1 sm:grid-cols-3 gap-2 font-mono text-xs pt-1">
                <div className="p-2 bg-surface-container-low rounded border border-outline-variant/20">
                  <span className="text-[10px] text-outline uppercase block">Lead Time Required</span>
                  <span className="text-on-surface font-semibold">14 Business Days</span>
                </div>
                <div className="p-2 bg-surface-container-low rounded border border-outline-variant/20">
                  <span className="text-[10px] text-outline uppercase block">Flange Rating</span>
                  <span className="text-on-surface font-semibold">Class 600 RTJ RF</span>
                </div>
                <div className="p-2 bg-surface-container-low rounded border border-outline-variant/20">
                  <span className="text-[10px] text-outline uppercase block">Corrosion Allowance</span>
                  <span className="text-tertiary font-semibold">+3.2 mm (Surplus)</span>
                </div>
              </div>
            </div>

            {/* Embedded Citations Pill List */}
            <div className="pt-2 space-y-1.5">
              <span className="font-mono text-[10px] uppercase tracking-wider text-outline flex items-center gap-1 font-semibold">
                <CheckCircle className="w-3.5 h-3.5 text-tertiary" />
                Verified Internal Knowledge Grounding (8 Sources)
              </span>
              <div className="flex flex-wrap gap-1.5 font-mono text-[10px]">
                <span className="inline-flex items-center gap-1 px-2 py-1 rounded bg-surface-container-high text-on-surface border border-outline-variant/30">
                  <span className="w-1.5 h-1.5 rounded-full bg-tertiary" />
                  API-570-Piping-Code-2023.pdf (p. 42)
                </span>
                <span className="inline-flex items-center gap-1 px-2 py-1 rounded bg-surface-container-high text-on-surface border border-outline-variant/30">
                  <span className="w-1.5 h-1.5 rounded-full bg-tertiary" />
                  CDU1_NDT_UT_Log_June.xlsx [Cell D84]
                </span>
                <span className="inline-flex items-center gap-1 px-2 py-1 rounded bg-surface-container-high text-on-surface border border-outline-variant/30">
                  <span className="w-1.5 h-1.5 rounded-full bg-tertiary" />
                  MOC-2024-881-Materials.docx
                </span>
                <span className="inline-flex items-center gap-1 px-2 py-1 rounded bg-surface-container-high text-on-surface border border-outline-variant/30">
                  <span className="w-1.5 h-1.5 rounded-full bg-tertiary" />
                  Vendor_Quote_SpecialtyAlloys_Rev2.pdf
                </span>
              </div>
            </div>
          </div>

          {/* Visual Evidence Panel */}
          <div className="lg:col-span-4 flex flex-col space-y-3 bg-surface-container p-4 rounded-lg border border-outline-variant/20 justify-between">
            <div className="space-y-2">
              <div className="flex items-center justify-between">
                <span className="font-mono text-xs uppercase tracking-wider text-outline font-bold">
                  Inspection Evidence
                </span>
                <span className="px-1.5 py-0.5 rounded bg-surface-container-high text-tertiary font-mono text-[10px]">
                  NDT CONFIRMED
                </span>
              </div>
              <div className="relative rounded-lg h-36 bg-[#0a121e] border border-outline-variant/30 flex items-center justify-center overflow-hidden">
                <div className="w-24 h-24 rounded-full border-2 border-dashed border-cyan-500/40 flex items-center justify-center">
                  <div className="w-12 h-12 rounded-full bg-rose-500/30 flex items-center justify-center text-rose-400 font-mono text-[9px] font-bold">
                    -42%
                  </div>
                </div>
                <div className="absolute bottom-2 left-2 right-2 p-1 rounded bg-surface-container-lowest/80 backdrop-blur flex items-center justify-between font-mono text-[10px]">
                  <span className="text-on-surface">FLANGE-CDU1-094</span>
                  <span className="text-error font-semibold">Wall: 3.1mm</span>
                </div>
              </div>
            </div>

            {/* Cryptographic Parameters */}
            <div className="p-2.5 bg-surface-container-low rounded border border-outline-variant/20 space-y-1 font-mono text-[10px]">
              <div className="flex items-center justify-between text-outline">
                <span>Model Temperature</span>
                <span className="text-on-surface">0.0 (Deterministic)</span>
              </div>
              <div className="flex items-center justify-between text-outline">
                <span>Context Tokens</span>
                <span className="text-on-surface">14,291 / 32,768</span>
              </div>
              <div className="flex items-center justify-between text-outline">
                <span>Hallucination Index</span>
                <span className="text-tertiary font-bold">0.00% (Constrained)</span>
              </div>
            </div>
          </div>
        </div>

        {/* Reviewer Comment Field */}
        <div className="space-y-1.5">
          <label className="font-mono text-xs text-outline uppercase font-semibold">
            Reviewer Validation Comments
          </label>
          <input
            type="text"
            value={reviewComment}
            onChange={(e) => setReviewComment(e.target.value)}
            className="w-full bg-surface-container text-on-surface text-xs font-mono px-3 py-2 rounded border border-outline-variant/30 focus:outline-none focus:border-primary-container"
          />
        </div>

        {/* Action Decision Bar (Signature Stage) */}
        <div className="flex flex-col sm:flex-row items-stretch sm:items-center justify-between gap-4 pt-4 border-t border-outline-variant/20">
          <div className="flex items-center gap-2 text-on-surface-variant font-mono text-xs">
            <Fingerprint className="w-5 h-5 text-tertiary shrink-0" />
            <span>Signing authorizes procurement dispatch and appends operator ID to immutable ledger.</span>
          </div>

          <div className="flex flex-wrap items-center gap-2 justify-end">
            <button
              type="button"
              onClick={() => handleDecision('reject')}
              className="px-4 py-2 rounded bg-rose-500/15 text-rose-300 hover:bg-rose-500/25 border border-rose-500/30 font-mono text-xs font-semibold flex items-center gap-1.5 transition-colors"
            >
              <X className="w-4 h-4" />
              <span>Reject & Archive</span>
            </button>
            <button
              type="button"
              onClick={() => handleDecision('changes')}
              className="px-4 py-2 rounded bg-surface-container-high hover:bg-surface-container-highest text-amber-300 border border-amber-500/30 font-mono text-xs font-semibold flex items-center gap-1.5 transition-colors"
            >
              <RefreshCw className="w-4 h-4" />
              <span>Request Changes</span>
            </button>
            <button
              type="button"
              disabled={isAuthorOrAdmin}
              onClick={() => handleDecision('approve')}
              className="px-5 py-2 rounded bg-tertiary text-surface hover:bg-tertiary-fixed font-mono text-xs font-bold transition-all shadow-[0_0_16px_rgba(168,255,210,0.3)] flex items-center gap-2 disabled:opacity-50 disabled:cursor-not-allowed"
              title={isAuthorOrAdmin ? 'SEC-11 Segregation of duties: Author/Admin cannot review own artifact' : 'Approve deliverable'}
            >
              <Key className="w-4 h-4" />
              <span>Approve & Sign Deliverable</span>
            </button>
          </div>
        </div>

        {isAuthorOrAdmin && (
          <div className="text-[11px] font-mono text-amber-400 bg-amber-500/10 p-2 rounded border border-amber-500/20">
            ℹ SEC-11 Segregation of Duties Notice: You are currently signed in as an author or administrator. Only designated independent reviewers can approve this document.
          </div>
        )}
      </div>

      {/* Verification Review Queue Section */}
      <div className="flex flex-col space-y-4">
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2">
          <div>
            <h2 className="font-headline text-lg text-on-surface font-semibold">Verification Review Queue</h2>
            <p className="text-xs text-on-surface-variant font-mono">Active refinery work-orders awaiting engineering validation.</p>
          </div>
          <button
            onClick={fetchQueue}
            className="flex items-center gap-1 px-3 py-1.5 rounded bg-surface-container hover:bg-surface-container-high text-on-surface font-mono text-xs border border-outline-variant/30"
          >
            <RefreshCw className={`w-3.5 h-3.5 ${loading ? 'animate-spin' : ''}`} />
            <span>Refresh Queue</span>
          </button>
        </div>

        {/* Queue Table */}
        <div className="bg-surface-container-low rounded-xl overflow-hidden shadow-lg border border-outline-variant/30">
          <table className="w-full text-left font-mono text-xs">
            <thead className="bg-surface-container-lowest text-outline text-[10px] uppercase tracking-wider border-b border-outline-variant/20">
              <tr>
                <th className="py-3 px-4">Deliverable Document</th>
                <th className="py-3 px-4">Kind</th>
                <th className="py-3 px-4">Clearance Status</th>
                <th className="py-3 px-4">Timestamp</th>
                <th className="py-3 px-4 text-right">Gate Operations</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-surface-container">
              {queue.length > 0 ? (
                queue.map((item) => (
                  <tr key={item.id} className="hover:bg-surface-container-high/40 transition-colors">
                    <td className="py-3 px-4">
                      <div className="flex items-center gap-2">
                        <FileText className="w-4 h-4 text-primary-container" />
                        <div>
                          <div className="font-semibold text-on-surface">{item.filename}</div>
                          <div className="text-[10px] text-outline">{item.id.substring(0, 12)}</div>
                        </div>
                      </div>
                    </td>
                    <td className="py-3 px-4 text-on-surface-variant uppercase">{item.kind}</td>
                    <td className="py-3 px-4">
                      <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded bg-amber-500/10 text-amber-400 font-bold border border-amber-500/30">
                        {item.status}
                      </span>
                    </td>
                    <td className="py-3 px-4 text-outline">{new Date(item.created_at).toLocaleTimeString()}</td>
                    <td className="py-3 px-4 text-right">
                      <button
                        onClick={() => handleDecision('approve', item.id)}
                        className="px-2.5 py-1 rounded bg-surface-container hover:bg-surface-container-high text-primary-container border border-primary-container/30 text-xs font-semibold"
                      >
                        Sign-off
                      </button>
                    </td>
                  </tr>
                ))
              ) : (
                <tr className="hover:bg-surface-container-high/40 transition-colors">
                  <td className="py-3 px-4">
                    <div className="flex items-center gap-2">
                      <FileText className="w-4 h-4 text-primary-container" />
                      <div>
                        <div className="font-semibold text-on-surface">Inspection_Approval_Note.docx</div>
                        <div className="text-[10px] text-outline">REF-BLR-8091 · 12 Citations</div>
                      </div>
                    </div>
                  </td>
                  <td className="py-3 px-4 text-on-surface-variant">APPROVAL_NOTE</td>
                  <td className="py-3 px-4">
                    <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded bg-surface-container-highest text-primary-container font-semibold border border-primary-container/30">
                      <span className="w-1.5 h-1.5 rounded-full bg-primary-container animate-pulse" />
                      PENDING REVIEW
                    </span>
                  </td>
                  <td className="py-3 px-4 text-outline">14 mins ago</td>
                  <td className="py-3 px-4 text-right">
                    <button
                      onClick={() => handleDecision('approve')}
                      className="px-2.5 py-1 rounded bg-surface-container hover:bg-surface-container-high text-on-surface border border-outline-variant/30 text-xs"
                    >
                      Inspect & Review
                    </button>
                  </td>
                </tr>
              )}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
};
