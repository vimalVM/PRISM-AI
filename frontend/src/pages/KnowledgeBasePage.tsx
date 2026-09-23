import React, { useState, useRef } from 'react';
import { 
  UploadCloud, 
  Search, 
  FileText, 
  ChevronDown, 
  ChevronLeft, 
  ChevronRight,
  HardDrive,
  ShieldCheck,
  Cpu
} from 'lucide-react';

interface KnowledgeDoc {
  id: string;
  name: string;
  meta: string;
  department: string;
  clearance: 'CONFIDENTIAL' | 'INTERNAL' | 'RESTRICTED';
  indexedDate: string;
}

const INITIAL_DOCS: KnowledgeDoc[] = [
  {
    id: '1',
    name: 'CDU Operations SOP (Rev 4)',
    meta: 'PDF · 18.2 MB',
    department: 'Operations',
    clearance: 'CONFIDENTIAL',
    indexedDate: 'Today, 09:15',
  },
  {
    id: '2',
    name: 'Fire & Safety Protocol 2026',
    meta: 'DOCX · 6.1 MB',
    department: 'Safety',
    clearance: 'INTERNAL',
    indexedDate: 'Yesterday',
  },
  {
    id: '3',
    name: 'Vendor Procurement Agreement (L&T)',
    meta: 'PDF · 44.5 MB',
    department: 'Procurement',
    clearance: 'RESTRICTED',
    indexedDate: 'Sep 18',
  },
  {
    id: '4',
    name: 'Furnace Tube Heat Exchanger P&ID',
    meta: 'DWG/PDF · 108.0 MB',
    department: 'Engineering',
    clearance: 'CONFIDENTIAL',
    indexedDate: 'Sep 14',
  },
  {
    id: '5',
    name: 'Compressor Bearing Vibration Baseline',
    meta: 'CSV/PDF · 3.4 MB',
    department: 'Maintenance',
    clearance: 'INTERNAL',
    indexedDate: 'Sep 10',
  },
  {
    id: '6',
    name: 'Refinery Expansion Master Plan 2030',
    meta: 'PDF · 148.9 MB',
    department: 'Executive',
    clearance: 'RESTRICTED',
    indexedDate: 'Aug 28',
  },
];

export const KnowledgeBasePage: React.FC = () => {
  const [documents, setDocuments] = useState<KnowledgeDoc[]>(INITIAL_DOCS);
  const [searchQuery, setSearchQuery] = useState('');
  const [department, setDepartment] = useState('All Departments');
  const [isDragging, setIsDragging] = useState(false);

  const fileInputRef = useRef<HTMLInputElement>(null);

  const handleFileUpload = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files && e.target.files.length > 0) {
      const file = e.target.files[0];
      const newDoc: KnowledgeDoc = {
        id: `doc-${Date.now()}`,
        name: file.name,
        meta: `${file.name.split('.').pop()?.toUpperCase() || 'DOC'} · ${(file.size / (1024 * 1024)).toFixed(1)} MB`,
        department: 'Operations',
        clearance: 'CONFIDENTIAL',
        indexedDate: 'Just now',
      };
      setDocuments((prev) => [newDoc, ...prev]);
      e.target.value = '';
    }
  };

  const handleDrop = (e: React.DragEvent) => {
    e.preventDefault();
    setIsDragging(false);
    if (e.dataTransfer.files && e.dataTransfer.files.length > 0) {
      const file = e.dataTransfer.files[0];
      const newDoc: KnowledgeDoc = {
        id: `doc-${Date.now()}`,
        name: file.name,
        meta: `${file.name.split('.').pop()?.toUpperCase() || 'DOC'} · ${(file.size / (1024 * 1024)).toFixed(1)} MB`,
        department: 'Operations',
        clearance: 'CONFIDENTIAL',
        indexedDate: 'Just now',
      };
      setDocuments((prev) => [newDoc, ...prev]);
    }
  };

  const getClearanceBadge = (clearance: string) => {
    switch (clearance) {
      case 'CONFIDENTIAL':
        return 'border-amber-300 dark:border-amber-700 bg-amber-50 dark:bg-amber-950/40 text-amber-700 dark:text-amber-300';
      case 'INTERNAL':
        return 'border-sky-300 dark:border-sky-700 bg-sky-50 dark:bg-sky-950/40 text-sky-700 dark:text-sky-300';
      case 'RESTRICTED':
        return 'border-rose-300 dark:border-rose-700 bg-rose-50 dark:bg-rose-950/40 text-rose-700 dark:text-rose-300';
      default:
        return 'border-slate-300 dark:border-slate-700 bg-slate-50 text-slate-700';
    }
  };

  const filteredDocs = documents.filter((doc) => {
    const matchesSearch = doc.name.toLowerCase().includes(searchQuery.toLowerCase()) || doc.department.toLowerCase().includes(searchQuery.toLowerCase());
    const matchesDept = department === 'All Departments' || doc.department === department;
    return matchesSearch && matchesDept;
  });

  return (
    <div className="flex flex-col w-full max-w-6xl mx-auto pb-12 space-y-6">
      <input
        ref={fileInputRef}
        type="file"
        onChange={handleFileUpload}
        className="hidden"
        accept=".pdf,.docx,.xlsx,.txt,.dwg,.csv"
      />

      {/* Top Breadcrumb & Status */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-3 pt-2">
        <div>
          <div className="font-mono text-[10px] text-sky-600 dark:text-sky-400 font-bold uppercase tracking-wider mb-1">
            SOVEREIGN RAG DATASINK | AIR-GAPPED CLUSTER 01
          </div>
          <h1 className="text-2xl font-bold text-slate-900 dark:text-slate-100 tracking-tight font-headline">
            Sovereign Knowledge Base
          </h1>
          <p className="text-xs text-slate-500 dark:text-slate-400 mt-0.5">
            Encrypted on-premise vector embeddings. Zero telemetry egress.
          </p>
        </div>

        <div className="flex items-center gap-2">
          <div className="flex items-center gap-1.5 px-3 py-1 rounded-full border border-emerald-200 dark:border-emerald-800 bg-emerald-50 dark:bg-emerald-950/40 text-emerald-700 dark:text-emerald-300 text-xs font-mono font-semibold">
            <span className="w-1.5 h-1.5 rounded-full bg-emerald-500 animate-pulse" />
            <span>Qwen-3 Embedder Node</span>
          </div>
          <div className="px-3 py-1 rounded-full border border-slate-200 dark:border-slate-800 bg-slate-50 dark:bg-slate-900 text-slate-600 dark:text-slate-400 text-xs font-mono font-semibold">
            NVME DIRECT-IO SYNC
          </div>
        </div>
      </div>

      {/* 3 Stats Card */}
      <div className="rounded-xl bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 p-5 shadow-sm grid grid-cols-1 md:grid-cols-3 divide-y md:divide-y-0 md:divide-x divide-slate-100 dark:divide-slate-800">
        <div className="px-4 py-2 flex items-baseline gap-2">
          <span className="text-2xl font-bold text-slate-900 dark:text-slate-100 font-headline">12,483</span>
          <span className="font-mono text-xs text-slate-400 uppercase font-semibold">DOCUMENTS</span>
        </div>

        <div className="px-4 py-2 flex items-baseline gap-2">
          <span className="text-2xl font-bold text-emerald-600 dark:text-emerald-400 font-headline">100%</span>
          <span className="font-mono text-xs text-slate-400 uppercase font-semibold">ON-PREMISE LOCAL</span>
        </div>

        <div className="px-4 py-2 flex items-baseline gap-2">
          <span className="text-2xl font-bold text-sky-600 dark:text-sky-400 font-headline">AES-256</span>
          <span className="font-mono text-xs text-slate-400 uppercase font-semibold">HARDWARE ENCRYPTED</span>
        </div>
      </div>

      {/* Dropzone Card */}
      <div
        onDragOver={(e) => { e.preventDefault(); setIsDragging(true); }}
        onDragLeave={() => setIsDragging(false)}
        onDrop={handleDrop}
        onClick={() => fileInputRef.current?.click()}
        className={`rounded-xl bg-white dark:bg-slate-900 border p-5 shadow-sm flex flex-col sm:flex-row items-center justify-between gap-4 cursor-pointer transition-all ${
          isDragging 
            ? 'border-sky-500 bg-sky-50/40 dark:bg-sky-950/20 ring-2 ring-sky-500/20' 
            : 'border-slate-200 dark:border-slate-800 hover:border-sky-300 dark:hover:border-sky-700'
        }`}
      >
        <div className="flex items-center gap-3.5">
          <div className="w-10 h-10 rounded-lg bg-sky-50 dark:bg-sky-950/60 border border-sky-100 dark:border-sky-900 flex items-center justify-center text-sky-600 shrink-0">
            <UploadCloud className="w-5 h-5" />
          </div>
          <div>
            <div className="text-sm font-semibold text-slate-900 dark:text-slate-100">
              Drop confidential SOPs, drawings, or manuals here
            </div>
            <div className="text-xs text-slate-400 mt-0.5">
              Direct sovereign parsing for PDF, DOCX, DWG up to 1.5 GB
            </div>
          </div>
        </div>

        <button
          type="button"
          onClick={(e) => { e.stopPropagation(); fileInputRef.current?.click(); }}
          className="flex items-center gap-2 px-4 py-2 rounded-lg bg-sky-600 hover:bg-sky-500 text-white font-medium text-xs shadow-sm transition-colors cursor-pointer shrink-0"
        >
          <FileText className="w-4 h-4" />
          <span>Upload Document</span>
        </button>
      </div>

      {/* Search & Filter Bar */}
      <div className="flex flex-col sm:flex-row items-center gap-3">
        <div className="relative flex-1 w-full">
          <Search className="w-4 h-4 text-slate-400 absolute left-3.5 top-1/2 -translate-y-1/2" />
          <input
            type="text"
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            placeholder="Search document name, SOP ID, or keywords..."
            className="w-full bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 rounded-lg pl-10 pr-4 py-2 text-xs text-slate-800 dark:text-slate-200 placeholder:text-slate-400 outline-none focus:border-sky-400 transition-colors shadow-sm"
          />
        </div>

        <div className="relative shrink-0 w-full sm:w-auto">
          <select
            value={department}
            onChange={(e) => setDepartment(e.target.value)}
            className="w-full sm:w-44 bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 rounded-lg px-3 py-2 text-xs text-slate-700 dark:text-slate-300 font-medium outline-none appearance-none cursor-pointer shadow-sm pr-8"
          >
            <option value="All Departments">All Departments</option>
            <option value="Operations">Operations</option>
            <option value="Safety">Safety</option>
            <option value="Procurement">Procurement</option>
            <option value="Engineering">Engineering</option>
            <option value="Maintenance">Maintenance</option>
            <option value="Executive">Executive</option>
          </select>
          <ChevronDown className="w-3.5 h-3.5 text-slate-400 absolute right-3 top-1/2 -translate-y-1/2 pointer-events-none" />
        </div>
      </div>

      {/* Knowledge Repository Table Card */}
      <div className="rounded-xl bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 shadow-sm overflow-hidden">
        <div className="px-5 py-3.5 border-b border-slate-100 dark:border-slate-800 flex items-center justify-between">
          <div className="text-xs font-bold text-slate-900 dark:text-slate-100">
            Knowledge Repository <span className="text-slate-400 font-normal">({filteredDocs.length} of 12,483)</span>
          </div>
          <span className="font-mono text-[10px] text-slate-400 uppercase font-semibold">
            RBAC Active
          </span>
        </div>

        <table className="w-full text-left text-xs">
          <thead>
            <tr className="border-b border-slate-100 dark:border-slate-800 text-[10px] font-mono uppercase text-slate-400">
              <th className="py-2.5 px-5 font-semibold">DOCUMENT</th>
              <th className="py-2.5 px-5 font-semibold">DEPARTMENT</th>
              <th className="py-2.5 px-5 font-semibold">CLEARANCE</th>
              <th className="py-2.5 px-5 font-semibold">INDEXED DATE</th>
              <th className="py-2.5 px-5 font-semibold text-right"></th>
            </tr>
          </thead>
          <tbody className="divide-y divide-slate-100 dark:divide-slate-800/60">
            {filteredDocs.map((doc) => (
              <tr key={doc.id} className="hover:bg-slate-50/60 dark:hover:bg-slate-800/40 transition-colors">
                <td className="py-3 px-5 flex items-center gap-2.5">
                  <div className="w-7 h-7 rounded border border-slate-200 dark:border-slate-700 bg-slate-50 dark:bg-slate-800 flex items-center justify-center text-slate-400 shrink-0">
                    <FileText className="w-3.5 h-3.5" />
                  </div>
                  <div>
                    <div className="font-semibold text-slate-900 dark:text-slate-100">{doc.name}</div>
                    <div className="font-mono text-[10px] text-slate-400">{doc.meta}</div>
                  </div>
                </td>
                <td className="py-3 px-5 text-slate-600 dark:text-slate-400 font-medium">
                  {doc.department}
                </td>
                <td className="py-3 px-5">
                  <span className={`px-2 py-0.5 rounded border text-[10px] font-mono font-bold tracking-wider ${getClearanceBadge(doc.clearance)}`}>
                    {doc.clearance}
                  </span>
                </td>
                <td className="py-3 px-5 text-slate-500 font-mono text-[11px]">
                  {doc.indexedDate}
                </td>
                <td className="py-3 px-5 text-right">
                  <button
                    type="button"
                    onClick={() => alert(`Opening secure enclaved viewer for ${doc.name}`)}
                    className="text-slate-400 hover:text-sky-600 dark:hover:text-sky-400 text-xs font-medium cursor-pointer"
                  >
                    View
                  </button>
                </td>
              </tr>
            ))}
          </tbody>
        </table>

        {/* Pagination Footer */}
        <div className="px-5 py-3 border-t border-slate-100 dark:border-slate-800 flex items-center justify-between text-xs text-slate-400 font-mono">
          <span>Page 1 of 2,081</span>
          <div className="flex items-center gap-1">
            <button type="button" className="p-1 rounded hover:bg-slate-100 dark:hover:bg-slate-800 text-slate-400 hover:text-slate-700 cursor-pointer">
              <ChevronLeft className="w-4 h-4" />
            </button>
            <button type="button" className="p-1 rounded hover:bg-slate-100 dark:hover:bg-slate-800 text-slate-400 hover:text-slate-700 cursor-pointer">
              <ChevronRight className="w-4 h-4" />
            </button>
          </div>
        </div>
      </div>
    </div>
  );
};
