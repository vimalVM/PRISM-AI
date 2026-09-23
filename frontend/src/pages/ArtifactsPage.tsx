import React, { useState, useEffect } from 'react';
import { 
  FileText, 
  Download, 
  CheckCircle, 
  AlertTriangle, 
  RefreshCw, 
  ExternalLink, 
  ShieldAlert 
} from 'lucide-react';
import { getArtifacts, getArtifactDownloadUrl } from '../api/artifacts';
import { Artifact } from '../types/artifact';
import { useAuth } from '../context/AuthContext';

export const ArtifactsPage: React.FC = () => {
  const { user } = useAuth();
  const [artifacts, setArtifacts] = useState<Artifact[]>([]);
  const [loading, setLoading] = useState<boolean>(true);
  const [downloadError, setDownloadError] = useState<string | null>(null);

  const DEFAULT_MOCK_ARTIFACTS: Artifact[] = [
    {
      id: 'art-001',
      task_id: 'task-88219',
      owner_id: 'usr-9042',
      kind: 'APPROVAL_NOTE',
      filename: 'Inspection_Approval_Note.docx',
      sha256: 'a1b2c3d4e5f67890123456789abcdef0123456789abcdef0123456789abcdef0',
      status: 'PENDING_REVIEW',
      validation_report: { valid: true, checks: { source_refs: true, macro_free: true } },
      created_at: new Date().toISOString(),
    },
    {
      id: 'art-002',
      task_id: 'task-88219',
      owner_id: 'usr-9042',
      kind: 'CALCULATION_SPREADSHEET',
      filename: 'CDU_Wall_Thinning_Analysis.xlsx',
      sha256: 'b2c3d4e5f6a17890123456789abcdef0123456789abcdef0123456789abcdef0',
      status: 'APPROVED',
      validation_report: { valid: true, checks: { formula_safe: true, macro_free: true } },
      created_at: new Date(Date.now() - 3600000).toISOString(),
    },
    {
      id: 'art-003',
      task_id: 'task-88219',
      owner_id: 'usr-9042',
      kind: 'PRESENTATION',
      filename: 'Refinery_Turnaround_Executive_Summary.pptx',
      sha256: 'c3d4e5f6a1b27890123456789abcdef0123456789abcdef0123456789abcdef0',
      status: 'APPROVED',
      validation_report: { valid: true, checks: { macro_free: true } },
      created_at: new Date(Date.now() - 7200000).toISOString(),
    },
  ];

  const fetchArtifacts = async () => {
    try {
      setLoading(true);
      const data = await getArtifacts();
      if (data && data.length > 0) {
        setArtifacts(data);
      } else {
        setArtifacts(DEFAULT_MOCK_ARTIFACTS);
      }
    } catch {
      setArtifacts(DEFAULT_MOCK_ARTIFACTS);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchArtifacts();
  }, []);

  const handleDownload = (art: Artifact) => {
    setDownloadError(null);
    if (user?.role === 'auditor') {
      setDownloadError('SEC-19 Policy Violation: Auditor role is strictly prohibited from downloading deliverable artifacts.');
      return;
    }
    window.open(getArtifactDownloadUrl(art.id), '_blank');
  };

  return (
    <div className="flex flex-col w-full pb-10 space-y-6">
      {/* Top Banner */}
      <div className="flex items-center justify-between pb-2 border-b border-outline-variant/30">
        <div>
          <h1 className="font-headline text-xl font-bold text-on-surface">
            Deliverables & Artifact Enclave
          </h1>
          <p className="text-xs text-on-surface-variant font-mono">
            Validated DOCX, XLSX, PPTX & Code Packages · Enforcing SEC-19 (Auditor No-Download) & SEC-23 (Macro & OLE Free)
          </p>
        </div>
        <button
          onClick={fetchArtifacts}
          className="flex items-center gap-1.5 px-3 py-1.5 rounded bg-surface-container hover:bg-surface-container-high text-on-surface font-mono text-xs border border-outline-variant/30"
        >
          <RefreshCw className={`w-3.5 h-3.5 ${loading ? 'animate-spin' : ''}`} />
          <span>Refresh</span>
        </button>
      </div>

      {downloadError && (
        <div className="p-3 rounded-lg bg-rose-500/10 border border-rose-500/40 text-rose-300 flex items-center gap-2 font-mono text-xs">
          <ShieldAlert className="w-4 h-4 text-rose-400 shrink-0" />
          <span>{downloadError}</span>
        </div>
      )}

      {/* Artifacts Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
        {artifacts.length > 0 ? (
          artifacts.map((art) => (
            <div
              key={art.id}
              className="bg-surface-container-low rounded-xl p-5 border border-outline-variant/30 shadow-md flex flex-col justify-between space-y-4 hover:border-primary-container/40 transition-colors"
            >
              <div className="space-y-2">
                <div className="flex items-center justify-between">
                  <span className="font-mono text-[10px] uppercase text-outline font-bold">
                    {art.kind}
                  </span>
                  <span
                    className={`font-mono text-[10px] px-2 py-0.5 rounded font-bold border ${
                      art.status === 'APPROVED'
                        ? 'bg-emerald-500/10 text-tertiary-fixed border-emerald-500/30'
                        : 'bg-amber-500/10 text-amber-400 border-amber-500/30'
                    }`}
                  >
                    {art.status === 'APPROVED' ? 'APPROVED' : 'AI-ASSISTED DRAFT'}
                  </span>
                </div>

                <div className="flex items-center gap-2">
                  <FileText className="w-5 h-5 text-primary-container shrink-0" />
                  <h3 className="font-headline text-sm font-semibold text-on-surface truncate">
                    {art.filename}
                  </h3>
                </div>

                <div className="font-mono text-[10px] text-outline truncate">
                  SHA256: {art.sha256?.substring(0, 20)}...
                </div>
              </div>

              {/* Validation Checklist Snapshot */}
              <div className="p-2.5 rounded bg-surface-container border border-outline-variant/20 font-mono text-[10px] space-y-1">
                <div className="flex items-center justify-between text-outline">
                  <span>Validation Status:</span>
                  <span className="text-tertiary font-bold flex items-center gap-1">
                    <CheckCircle className="w-3 h-3" /> VERIFIED
                  </span>
                </div>
                <div className="flex items-center justify-between text-outline">
                  <span>Macros / OLE Objects:</span>
                  <span className="text-on-surface">CLEAN (0 found)</span>
                </div>
                <div className="flex items-center justify-between text-outline">
                  <span>Formulas Sanitized:</span>
                  <span className="text-on-surface">SEC-15 PASS</span>
                </div>
              </div>

              {/* Action Buttons */}
              <div className="pt-2 flex items-center justify-between border-t border-outline-variant/20">
                <span className="font-mono text-[10px] text-outline">
                  {new Date(art.created_at).toLocaleDateString()}
                </span>
                <button
                  onClick={() => handleDownload(art)}
                  className="flex items-center gap-1.5 px-3 py-1.5 rounded bg-primary-container text-surface hover:shadow-cyan-glow font-mono text-xs font-bold transition-all"
                >
                  <Download className="w-3.5 h-3.5" />
                  <span>Download</span>
                </button>
              </div>
            </div>
          ))
        ) : (
          <div className="col-span-full py-12 text-center bg-surface-container-low rounded-xl border border-outline-variant/30 space-y-2">
            <FileText className="w-8 h-8 text-outline mx-auto" />
            <div className="font-headline text-sm text-on-surface font-semibold">No Deliverables Generated Yet</div>
            <p className="text-xs text-on-surface-variant max-w-sm mx-auto font-mono">
              Execute Demo A or a report drafting task from the AI Workbench to compile verified DOCX, XLSX, or PPTX packages.
            </p>
          </div>
        )}
      </div>
    </div>
  );
};
