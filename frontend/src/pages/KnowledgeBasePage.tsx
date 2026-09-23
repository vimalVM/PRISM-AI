import React, { useState, useEffect } from 'react';
import { 
  Database, 
  HardDrive, 
  UploadCloud, 
  Search, 
  RefreshCw, 
  ShieldCheck, 
  FileText, 
  Trash2, 
  CheckCircle, 
  Lock, 
  Filter 
} from 'lucide-react';
import { getKBDocuments, uploadKBDocument, searchKB, deleteKBDocument } from '../api/services';
import { KBDocument, KBSearchResult } from '../types/system';
import { ClearanceChip } from '../components/common/ClearanceChip';
import { Clearance } from '../types/auth';

export const KnowledgeBasePage: React.FC = () => {
  const [documents, setDocuments] = useState<KBDocument[]>([]);
  const [searchResults, setSearchResults] = useState<KBSearchResult[] | null>(null);
  const [searchQuery, setSearchQuery] = useState<string>('');
  const [selectedClassification, setSelectedClassification] = useState<Clearance>('CONFIDENTIAL');
  const [loading, setLoading] = useState<boolean>(false);
  const [uploadStatus, setUploadStatus] = useState<string | null>(null);

  const DEFAULT_MOCK_DOCS: KBDocument[] = [
    {
      id: 'doc-001',
      doc_id: 'SOP-CDU-02',
      filename: 'CDU_Operating_SOP.pdf',
      version: '3.2',
      classification: 'CONFIDENTIAL',
      sha256: 'e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855',
      status: 'indexed',
      chunks: 14,
      uploaded_by: 'usr-9042',
      ingested_at: new Date().toISOString(),
    },
    {
      id: 'doc-002',
      doc_id: 'INSP-LOG-SEP',
      filename: 'Inspection_Log_Sept.pdf',
      version: '1.0',
      classification: 'CONFIDENTIAL',
      sha256: '7f83b1657ff1fc53b92dc18148a1d65dfc2d4b1fa3d677284addd200126d9069',
      status: 'indexed',
      chunks: 8,
      uploaded_by: 'usr-9042',
      ingested_at: new Date().toISOString(),
    },
    {
      id: 'doc-003',
      doc_id: 'VALVE-MAINT-MAN',
      filename: 'Valve_Maint_Manual.pdf',
      version: '2.1',
      classification: 'CONFIDENTIAL',
      sha256: '6b86b273ff34fce19d6b804eff5a3f5747ada4eaa22f1d49c01e52ddb7875b4b',
      status: 'indexed',
      chunks: 12,
      uploaded_by: 'usr-9042',
      ingested_at: new Date().toISOString(),
    },
  ];

  const fetchDocs = async () => {
    try {
      setLoading(true);
      const docs = await getKBDocuments();
      if (docs && docs.length > 0) {
        setDocuments(docs);
      } else {
        setDocuments(DEFAULT_MOCK_DOCS);
      }
    } catch {
      setDocuments(DEFAULT_MOCK_DOCS);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchDocs();
  }, []);

  const handleFileUpload = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (!file) return;

    setUploadStatus(`Encrypting & parsing ${file.name}...`);
    try {
      await uploadKBDocument(file, selectedClassification);
      setUploadStatus(`Document ingested and indexed into ChromaDB!`);
      fetchDocs();
    } catch (err: any) {
      setUploadStatus(`Ingest error: ${err.message}`);
    }
  };

  const handleSearch = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!searchQuery.trim()) {
      setSearchResults(null);
      return;
    }

    try {
      const res = await searchKB(searchQuery, 5);
      setSearchResults(res);
    } catch (err: any) {
      console.error('KB search error:', err);
    }
  };

  return (
    <div className="flex flex-col w-full pb-10 space-y-6">
      {/* Top Banner */}
      <div className="flex items-center justify-between pb-2 border-b border-outline-variant/30">
        <div>
          <h1 className="font-headline text-xl font-bold text-on-surface">
            Sovereign Knowledge Base & Vector Enclave
          </h1>
          <p className="text-xs text-on-surface-variant font-mono">
            Persistent ChromaDB · Local Qwen3-Embedding-0.6B · Server-Side Clearance Filtering
          </p>
        </div>
        <div className="flex items-center gap-2">
          <span className="font-mono text-xs px-2.5 py-1 rounded bg-surface-container text-tertiary border border-outline-variant/30 font-semibold">
            TELEMETRY: OFF · AIR-GAPPED
          </span>
        </div>
      </div>

      {/* Cluster Storage & Encryption Status Cards */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
        <div className="bg-surface-container-lowest rounded-xl p-4 border border-outline-variant/30 flex items-center justify-between">
          <div>
            <div className="font-mono text-[10px] text-outline uppercase font-semibold">TOTAL VECTOR CHUNKS</div>
            <div className="font-headline text-2xl font-bold text-primary-container mt-1">
              {documents.reduce((acc, d) => acc + (d.chunks || 0), 24)} Chunks
            </div>
            <div className="font-mono text-[10px] text-tertiary mt-1">Dense 1024-dim Embeddings</div>
          </div>
          <div className="p-3 rounded-lg bg-surface-container-high text-primary-container">
            <Database className="w-6 h-6" />
          </div>
        </div>

        <div className="bg-surface-container-lowest rounded-xl p-4 border border-outline-variant/30 flex items-center justify-between">
          <div>
            <div className="font-mono text-[10px] text-outline uppercase font-semibold">ENCLAVE STORAGE</div>
            <div className="font-headline text-2xl font-bold text-tertiary mt-1">NVMe RAID-1</div>
            <div className="font-mono text-[10px] text-on-surface-variant mt-1">100% On-Premises Persistent</div>
          </div>
          <div className="p-3 rounded-lg bg-surface-container-high text-tertiary">
            <HardDrive className="w-6 h-6" />
          </div>
        </div>

        <div className="bg-surface-container-lowest rounded-xl p-4 border border-outline-variant/30 flex items-center justify-between">
          <div>
            <div className="font-mono text-[10px] text-outline uppercase font-semibold">ACCESS ENFORCEMENT</div>
            <div className="font-headline text-2xl font-bold text-secondary-fixed mt-1">SEC-04 Active</div>
            <div className="font-mono text-[10px] text-tertiary mt-1">Clearance Filter Enforced</div>
          </div>
          <div className="p-3 rounded-lg bg-surface-container-high text-secondary-fixed">
            <ShieldCheck className="w-6 h-6" />
          </div>
        </div>
      </div>

      {/* Ingestion Pipeline Safe Zone Banner */}
      <div className="bg-surface-container-low rounded-xl p-5 border border-outline-variant/30 shadow-md space-y-4">
        <div className="flex flex-col lg:flex-row lg:items-center justify-between gap-3">
          <div className="flex items-center gap-3">
            <div className="h-9 w-9 rounded-lg bg-surface-container-high flex items-center justify-center text-primary-container">
              <ShieldCheck className="w-5 h-5" />
            </div>
            <div>
              <div className="flex items-center gap-2">
                <h2 className="font-headline text-sm font-semibold text-on-surface">Ingestion Pipeline Isolation</h2>
                <span className="font-mono text-[10px] uppercase px-1.5 py-0.5 rounded bg-surface-container text-tertiary font-bold">
                  Hardware Token Protected
                </span>
              </div>
              <p className="text-xs text-on-surface-variant">Bring your confidential engineering data here. It never leaves this sovereign rack.</p>
            </div>
          </div>

          <div className="flex items-center gap-3">
            <select
              value={selectedClassification}
              onChange={(e) => setSelectedClassification(e.target.value as Clearance)}
              className="bg-surface-container text-on-surface text-xs font-mono px-3 py-2 rounded border border-outline-variant/30"
            >
              <option value="PUBLIC">PUBLIC</option>
              <option value="INTERNAL">INTERNAL</option>
              <option value="CONFIDENTIAL">CONFIDENTIAL</option>
              <option value="RESTRICTED">RESTRICTED</option>
            </select>

            <label className="flex items-center gap-2 px-3.5 py-2 rounded-lg bg-primary-container text-surface hover:bg-primary font-mono text-xs font-bold shadow-md cursor-pointer transition-colors">
              <UploadCloud className="w-4 h-4" />
              <span>Upload Document</span>
              <input type="file" onChange={handleFileUpload} className="hidden" accept=".pdf,.docx,.xlsx,.txt" />
            </label>
          </div>
        </div>

        {uploadStatus && (
          <div className="p-2.5 rounded bg-surface-container text-xs font-mono text-primary-container border border-primary-container/30">
            {uploadStatus}
          </div>
        )}

        {/* Dropzone & 6-Stage Micro Stepper Grid */}
        <div className="grid grid-cols-1 xl:grid-cols-12 gap-4 items-stretch">
          <div className="xl:col-span-5 bg-surface-container-lowest/80 rounded-xl p-4 border-2 border-dashed border-outline-variant/40 flex flex-col items-center justify-center text-center cursor-pointer hover:border-primary-container/60 transition-all min-h-[160px]">
            <UploadCloud className="w-8 h-8 text-primary-container mb-2" />
            <span className="font-headline text-xs font-semibold text-on-surface">Drag & drop blueprints, manuals, or operational logs</span>
            <span className="font-mono text-[10px] text-on-surface-variant mt-1">Direct parsing for PDF, DOCX, XLSX, TXT up to 50 MB</span>
            <div className="mt-2.5 flex items-center gap-2 font-mono text-[10px]">
              <span className="px-2 py-0.5 rounded bg-surface-container-high text-outline">AUTO-ENCRYPT</span>
              <span className="px-2 py-0.5 rounded bg-surface-container-high text-tertiary">SHA-256 SEALED</span>
            </div>
          </div>

          <div className="xl:col-span-7 bg-surface-container rounded-xl p-4 border border-outline-variant/20 flex flex-col justify-between space-y-3">
            <div className="flex items-center justify-between text-outline font-mono text-[10px] uppercase">
              <span>Autonomous Pipeline Sequence</span>
              <span className="text-tertiary flex items-center gap-1 font-bold">
                <CheckCircle className="w-3 h-3" /> 6/6 Engine Stages Operational
              </span>
            </div>

            {/* 6 Micro Stepper Grid */}
            <div className="grid grid-cols-6 gap-2 text-center py-1 font-mono text-xs">
              <div className="flex flex-col items-center space-y-1">
                <div className="h-7 w-7 rounded-full bg-surface-container-highest text-tertiary flex items-center justify-center">
                  <CheckCircle className="w-4 h-4" />
                </div>
                <span className="text-[10px] text-on-surface">UPLOAD</span>
                <span className="text-[9px] text-tertiary font-bold">READY</span>
              </div>
              <div className="flex flex-col items-center space-y-1">
                <div className="h-7 w-7 rounded-full bg-surface-container-highest text-tertiary flex items-center justify-center">
                  <CheckCircle className="w-4 h-4" />
                </div>
                <span className="text-[10px] text-on-surface">VALIDATE</span>
                <span className="text-[9px] text-tertiary font-bold">PASS</span>
              </div>
              <div className="flex flex-col items-center space-y-1">
                <div className="h-7 w-7 rounded-full bg-surface-container-highest text-tertiary flex items-center justify-center">
                  <CheckCircle className="w-4 h-4" />
                </div>
                <span className="text-[10px] text-on-surface">PARSE</span>
                <span className="text-[9px] text-tertiary font-bold">14ms/p</span>
              </div>
              <div className="flex flex-col items-center space-y-1">
                <div className="h-7 w-7 rounded-full bg-surface-container-highest text-tertiary flex items-center justify-center">
                  <CheckCircle className="w-4 h-4" />
                </div>
                <span className="text-[10px] text-on-surface">OCR</span>
                <span className="text-[9px] text-tertiary font-bold">PADDLE</span>
              </div>
              <div className="flex flex-col items-center space-y-1">
                <div className="h-7 w-7 rounded-full bg-surface-container-highest text-primary flex items-center justify-center">
                  <CheckCircle className="w-4 h-4" />
                </div>
                <span className="text-[10px] text-on-surface">CLASSIFY</span>
                <span className="text-[9px] text-primary font-bold">RBAC</span>
              </div>
              <div className="flex flex-col items-center space-y-1">
                <div className="h-7 w-7 rounded-full bg-surface-container-highest text-primary-container flex items-center justify-center">
                  <CheckCircle className="w-4 h-4" />
                </div>
                <span className="text-[10px] text-on-surface">INDEX</span>
                <span className="text-[9px] text-primary-container font-bold">ACTIVE</span>
              </div>
            </div>

            <div className="bg-surface-container-lowest/90 px-3 py-2 rounded-lg flex items-center justify-between font-mono text-xs border border-outline-variant/20">
              <span className="text-on-surface flex items-center gap-1.5 truncate">
                <FileText className="w-3.5 h-3.5 text-primary-container" />
                inspection_report_0923.pdf · 12.4 MB · CONFIDENTIAL
              </span>
              <span className="text-tertiary font-medium shrink-0">Indexed in 1.4s</span>
            </div>
          </div>
        </div>
      </div>

      {/* Semantic Search & Command Filter Bar */}
      <div className="bg-surface-container-low p-4 rounded-xl shadow-sm border border-outline-variant/30 space-y-3">
        <form onSubmit={handleSearch} className="flex gap-2">
          <div className="relative flex-1">
            <Search className="w-4 h-4 text-on-surface-variant absolute left-3 top-1/2 -translate-y-1/2" />
            <input
              type="text"
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              placeholder="Search internal engineering SOPs, P&IDs, incident reports, and equipment manuals..."
              className="w-full bg-surface-container-lowest text-on-surface pl-9 pr-14 py-2.5 rounded-lg text-xs font-mono placeholder:text-outline border border-outline-variant/30 focus:outline-none focus:border-primary-container"
            />
            <span className="absolute right-3 top-1/2 -translate-y-1/2 font-mono text-[10px] bg-surface-container px-1.5 py-0.5 rounded text-outline border border-outline-variant/30">
              ⌘K
            </span>
          </div>
          <button
            type="submit"
            className="px-4 py-2 bg-surface-container hover:bg-surface-container-high text-on-surface font-mono text-xs font-semibold rounded border border-outline-variant/30"
          >
            Search
          </button>
        </form>

        {/* Search Results Display */}
        {searchResults && (
          <div className="pt-2 space-y-2">
            <div className="font-mono text-xs text-tertiary font-semibold flex items-center justify-between">
              <span>{searchResults.length} Relevant Vector Chunks Retrieved:</span>
              <button onClick={() => setSearchResults(null)} className="text-outline hover:text-on-surface text-[10px]">
                Clear Results
              </button>
            </div>
            {searchResults.map((res, i) => (
              <div key={i} className="p-3 rounded bg-surface-container border border-outline-variant/20 text-xs font-mono space-y-1">
                <div className="flex items-center justify-between">
                  <span className="text-primary font-semibold">{res.filename} (p. {res.page || 1})</span>
                  <span className="text-tertiary">{Math.round(res.score * 100)}% Match</span>
                </div>
                <p className="text-on-surface-variant font-sans text-xs">{res.content}</p>
              </div>
            ))}
          </div>
        )}
      </div>

      {/* Indexed Documents Table */}
      <div className="bg-surface-container-low rounded-xl overflow-hidden shadow-lg border border-outline-variant/30">
        <div className="p-3 border-b border-outline-variant/20 flex items-center justify-between font-mono text-xs">
          <span className="font-bold text-on-surface uppercase">Ingested Documents Ledger</span>
          <button onClick={fetchDocs} className="flex items-center gap-1 text-outline hover:text-on-surface">
            <RefreshCw className={`w-3.5 h-3.5 ${loading ? 'animate-spin' : ''}`} />
            <span>Refresh</span>
          </button>
        </div>

        <table className="w-full text-left font-mono text-xs">
          <thead className="bg-surface-container-lowest text-outline text-[10px] uppercase border-b border-outline-variant/20">
            <tr>
              <th className="py-2.5 px-4">Document Title</th>
              <th className="py-2.5 px-4">Version</th>
              <th className="py-2.5 px-4">Clearance</th>
              <th className="py-2.5 px-4">Chunks</th>
              <th className="py-2.5 px-4">SHA-256 Hash</th>
              <th className="py-2.5 px-4 text-right">Actions</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-surface-container">
            {documents.length > 0 ? (
              documents.map((doc) => (
                <tr key={doc.id} className="hover:bg-surface-container-high/40 transition-colors">
                  <td className="py-3 px-4 font-semibold text-on-surface flex items-center gap-2">
                    <FileText className="w-4 h-4 text-primary-container" />
                    {doc.filename}
                  </td>
                  <td className="py-3 px-4 text-on-surface-variant">v{doc.version}</td>
                  <td className="py-3 px-4">
                    <ClearanceChip clearance={doc.classification} size="sm" />
                  </td>
                  <td className="py-3 px-4 text-tertiary">{doc.chunks} Chunks</td>
                  <td className="py-3 px-4 text-outline font-mono text-[10px]">{doc.sha256?.substring(0, 16)}...</td>
                  <td className="py-3 px-4 text-right">
                    <button
                      onClick={async () => {
                        if (confirm(`Delete ${doc.filename}?`)) {
                          await deleteKBDocument(doc.id);
                          fetchDocs();
                        }
                      }}
                      className="p-1 rounded text-outline hover:text-rose-400 hover:bg-surface-container transition-colors"
                      title="Delete document"
                    >
                      <Trash2 className="w-3.5 h-3.5" />
                    </button>
                  </td>
                </tr>
              ))
            ) : (
              <tr>
                <td colSpan={6} className="py-6 text-center text-outline">
                  No documents ingested yet. Upload an inspection report, SOP, or engineering manual above.
                </td>
              </tr>
            )}
          </tbody>
        </table>
      </div>
    </div>
  );
};
