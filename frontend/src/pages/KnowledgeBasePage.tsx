import React, { useState, useEffect, useRef } from 'react';
import { 
  Search, 
  FileText, 
  ShieldCheck, 
  Database, 
  Loader2, 
  BookOpen, 
  Lock, 
  Plus,
  Upload,
  X,
  CheckCircle2,
  AlertCircle,
  FileUp,
  Sparkles
} from 'lucide-react';
import { getKBDocuments, uploadKBDocument, searchKB, KBDocumentResponse } from '../api/kb';
import { useAuth } from '../context/AuthContext';

export const KnowledgeBasePage: React.FC = () => {
  const { user } = useAuth();

  const [documents, setDocuments] = useState<KBDocumentResponse[]>([]);
  const [isLoadingDocs, setIsLoadingDocs] = useState(true);
  const [searchQuery, setSearchQuery] = useState('');
  const [isSearching, setIsSearching] = useState(false);
  const [searchResults, setSearchResults] = useState<any[]>([]);
  const [hasSearched, setHasSearched] = useState(false);

  // Upload modal state
  const [showUploadModal, setShowUploadModal] = useState(false);
  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const [docIdInput, setDocIdInput] = useState('');
  const [classificationInput, setClassificationInput] = useState<number>(2); // Default CONFIDENTIAL (2)
  const [isUploading, setIsUploading] = useState(false);
  const [uploadStatus, setUploadStatus] = useState<{ success: boolean; message: string } | null>(null);

  const fileInputRef = useRef<HTMLInputElement>(null);

  useEffect(() => {
    loadDocuments();
  }, []);

  const loadDocuments = async () => {
    setIsLoadingDocs(true);
    try {
      const docs = await getKBDocuments();
      setDocuments(docs || []);
    } catch (err) {
      console.error('Failed to load documents:', err);
      setDocuments([]);
    } finally {
      setIsLoadingDocs(false);
    }
  };

  const handleSearch = async (e?: React.FormEvent) => {
    if (e) e.preventDefault();
    if (!searchQuery.trim()) return;

    setIsSearching(true);
    setHasSearched(true);
    try {
      const results = await searchKB(searchQuery, 5);
      setSearchResults(results || []);
    } catch (err) {
      console.error('Search failed:', err);
      setSearchResults([]);
    } finally {
      setIsSearching(false);
    }
  };

  const clearSearch = () => {
    setSearchQuery('');
    setSearchResults([]);
    setHasSearched(false);
  };

  const handleFileSelect = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files && e.target.files.length > 0) {
      const file = e.target.files[0];
      setSelectedFile(file);
      // Pre-fill doc ID from filename if empty
      if (!docIdInput) {
        const base = file.name.split('.')[0].replace(/[^a-zA-Z0-9_-]/g, '_');
        setDocIdInput(base.toUpperCase());
      }
    }
  };

  const handleIngestSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!selectedFile || !docIdInput.trim()) return;

    setIsUploading(true);
    setUploadStatus(null);
    try {
      const result = await uploadKBDocument(selectedFile, docIdInput.trim(), classificationInput);
      setUploadStatus({
        success: true,
        message: result.message || `Successfully ingested ${selectedFile.name} as ${docIdInput} into ChromaDB.`,
      });
      // Refresh documents list
      await loadDocuments();
      // Reset form
      setTimeout(() => {
        setSelectedFile(null);
        setDocIdInput('');
        setShowUploadModal(false);
        setUploadStatus(null);
      }, 1500);
    } catch (err: any) {
      setUploadStatus({
        success: false,
        message: err.message || 'Failed to ingest document into knowledge base.',
      });
    } finally {
      setIsUploading(false);
    }
  };

  const getClearanceBadge = (cls?: any) => {
    const cStr = String(cls ?? '2').toUpperCase();
    if (cStr === 'RESTRICTED' || cStr === '3') {
      return (
        <span className="px-2 py-0.5 rounded-full bg-rose-50 dark:bg-rose-950/40 text-rose-700 dark:text-rose-300 border border-rose-200 dark:border-rose-800 text-[10px] font-mono font-bold">
          RESTRICTED
        </span>
      );
    }
    if (cStr === 'CONFIDENTIAL' || cStr === '2') {
      return (
        <span className="px-2 py-0.5 rounded-full bg-amber-50 dark:bg-amber-950/40 text-amber-700 dark:text-amber-300 border border-amber-200 dark:border-amber-800 text-[10px] font-mono font-bold">
          CONFIDENTIAL
        </span>
      );
    }
    if (cStr === 'INTERNAL' || cStr === '1') {
      return (
        <span className="px-2 py-0.5 rounded-full bg-sky-50 dark:bg-sky-950/40 text-sky-700 dark:text-sky-300 border border-sky-200 dark:border-sky-800 text-[10px] font-mono font-bold">
          INTERNAL
        </span>
      );
    }
    return (
      <span className="px-2 py-0.5 rounded-full bg-slate-100 dark:bg-slate-800 text-slate-700 dark:text-slate-300 border border-slate-200 dark:border-slate-700 text-[10px] font-mono font-bold">
        PUBLIC
      </span>
    );
  };

  return (
    <div className="flex flex-col w-full max-w-5xl mx-auto space-y-6 pb-16">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4 pt-2">
        <div className="space-y-1">
          <div className="flex items-center gap-2">
            <h1 className="text-2xl font-bold tracking-tight text-slate-900 dark:text-slate-100 font-headline">
              Sovereign Knowledge Base
            </h1>
            <span className="px-2 py-0.5 rounded bg-emerald-50 dark:bg-emerald-950/40 text-emerald-700 dark:text-emerald-300 border border-emerald-200 dark:border-emerald-800 text-[10px] font-mono font-semibold">
              ChromaDB Local
            </span>
          </div>
          <p className="text-xs text-slate-500 dark:text-slate-400">
            Real persistent vector store running SentenceTransformer embeddings on local CPU. All access is clearance-filtered.
          </p>
        </div>

        <div className="flex items-center gap-2">
          <button
            type="button"
            onClick={() => setShowUploadModal(true)}
            className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-slate-900 hover:bg-slate-800 dark:bg-sky-600 dark:hover:bg-sky-500 text-white text-xs font-semibold shadow-xs transition-colors cursor-pointer"
          >
            <Plus className="w-3.5 h-3.5" />
            <span>Upload &amp; Ingest SOP</span>
          </button>
        </div>
      </div>

      {/* Manual Upload & Ingest Modal */}
      {showUploadModal && (
        <div className="fixed inset-0 z-50 bg-slate-900/40 backdrop-blur-xs flex items-center justify-center p-4">
          <div className="bg-white dark:bg-slate-900 rounded-2xl border border-slate-200 dark:border-slate-800 max-w-md w-full p-5 space-y-4 shadow-xl">
            <div className="flex items-center justify-between border-b border-slate-100 dark:border-slate-800 pb-3">
              <div className="flex items-center gap-2">
                <FileUp className="w-4 h-4 text-sky-500" />
                <h3 className="text-sm font-bold text-slate-900 dark:text-slate-100">
                  Ingest New Document into ChromaDB
                </h3>
              </div>
              <button
                type="button"
                onClick={() => setShowUploadModal(false)}
                className="text-slate-400 hover:text-slate-600 dark:hover:text-slate-200 cursor-pointer"
              >
                <X className="w-4 h-4" />
              </button>
            </div>

            <form onSubmit={handleIngestSubmit} className="space-y-3.5 text-xs">
              {/* File Input */}
              <div className="space-y-1">
                <label className="font-semibold text-slate-700 dark:text-slate-300">
                  Select File (.txt, .pdf, .docx, .md)
                </label>
                <div 
                  onClick={() => fileInputRef.current?.click()}
                  className="p-3.5 rounded-xl border border-dashed border-slate-300 dark:border-slate-700 bg-slate-50 dark:bg-slate-950/60 hover:border-sky-400 text-center cursor-pointer transition-colors"
                >
                  <input
                    ref={fileInputRef}
                    type="file"
                    onChange={handleFileSelect}
                    accept=".txt,.pdf,.docx,.md"
                    className="hidden"
                  />
                  {selectedFile ? (
                    <div className="flex items-center justify-center gap-2 text-slate-900 dark:text-slate-100 font-mono">
                      <FileText className="w-4 h-4 text-sky-500" />
                      <span className="font-bold">{selectedFile.name}</span>
                      <span className="text-slate-400">({(selectedFile.size / 1024).toFixed(1)} KB)</span>
                    </div>
                  ) : (
                    <div className="space-y-1 text-slate-500">
                      <Upload className="w-5 h-5 mx-auto text-slate-400" />
                      <p>Click to choose file for local vector indexing</p>
                    </div>
                  )}
                </div>
              </div>

              {/* Doc ID */}
              <div className="space-y-1">
                <label className="font-semibold text-slate-700 dark:text-slate-300">
                  Document ID (e.g. SOP-301, SOP-PV402)
                </label>
                <input
                  type="text"
                  value={docIdInput}
                  onChange={(e) => setDocIdInput(e.target.value)}
                  placeholder="SOP-301"
                  required
                  className="w-full px-3 py-2 rounded-lg border border-slate-200 dark:border-slate-700 bg-white dark:bg-slate-950 text-slate-900 dark:text-slate-100 font-mono text-xs outline-none focus:border-sky-500"
                />
              </div>

              {/* Clearance Tier */}
              <div className="space-y-1">
                <label className="font-semibold text-slate-700 dark:text-slate-300">
                  Clearance Level (SEC-04 Access Control)
                </label>
                <select
                  value={classificationInput}
                  onChange={(e) => setClassificationInput(Number(e.target.value))}
                  className="w-full px-3 py-2 rounded-lg border border-slate-200 dark:border-slate-700 bg-white dark:bg-slate-950 text-slate-900 dark:text-slate-100 font-mono text-xs outline-none focus:border-sky-500"
                >
                  <option value={0}>0 — PUBLIC (All users)</option>
                  <option value={1}>1 — INTERNAL (Staff/Internal only)</option>
                  <option value={2}>2 — CONFIDENTIAL (Engineers &amp; Reviewers)</option>
                  <option value={3}>3 — RESTRICTED (Top Secret / Senior Staff)</option>
                </select>
              </div>

              {/* Status Notice */}
              {uploadStatus && (
                <div className={`p-2.5 rounded-lg text-xs flex items-center gap-2 ${
                  uploadStatus.success 
                    ? 'bg-emerald-50 dark:bg-emerald-950/40 text-emerald-800 dark:text-emerald-300 border border-emerald-200 dark:border-emerald-800'
                    : 'bg-rose-50 dark:bg-rose-950/40 text-rose-800 dark:text-rose-300 border border-rose-200 dark:border-rose-800'
                }`}>
                  {uploadStatus.success ? <CheckCircle2 className="w-4 h-4 flex-shrink-0" /> : <AlertCircle className="w-4 h-4 flex-shrink-0" />}
                  <span>{uploadStatus.message}</span>
                </div>
              )}

              {/* Action Buttons */}
              <div className="flex items-center justify-end gap-2 pt-2 border-t border-slate-100 dark:border-slate-800">
                <button
                  type="button"
                  onClick={() => setShowUploadModal(false)}
                  disabled={isUploading}
                  className="px-3 py-1.5 rounded-lg border border-slate-200 dark:border-slate-700 text-slate-600 dark:text-slate-400 hover:bg-slate-100 dark:hover:bg-slate-800 transition-colors"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  disabled={isUploading || !selectedFile || !docIdInput.trim()}
                  className="flex items-center gap-1.5 px-4 py-1.5 rounded-lg bg-slate-900 hover:bg-slate-800 dark:bg-sky-600 dark:hover:bg-sky-500 text-white font-medium shadow-xs transition-colors disabled:opacity-50"
                >
                  {isUploading ? (
                    <>
                      <Loader2 className="w-3.5 h-3.5 animate-spin" />
                      <span>Embedding Chunks...</span>
                    </>
                  ) : (
                    <span>Ingest Document</span>
                  )}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* Search Input Deck */}
      <div className="rounded-2xl bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 p-3 shadow-xs">
        <form onSubmit={handleSearch} className="flex items-center gap-2">
          <Search className="w-4 h-4 text-slate-400 ml-2 flex-shrink-0" />
          <input
            type="text"
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            placeholder="Search ingested documents (e.g. 'wall thinning tolerance SOP-301' or 'ultrasonic calibration')..."
            className="w-full bg-transparent border-none outline-none text-sm text-slate-900 dark:text-slate-100 placeholder:text-slate-400 font-sans"
          />
          {searchQuery && (
            <button
              type="button"
              onClick={clearSearch}
              className="text-xs text-slate-400 hover:text-slate-600 dark:hover:text-slate-200 px-2 cursor-pointer"
            >
              Clear
            </button>
          )}
          <button
            type="submit"
            disabled={isSearching || !searchQuery.trim()}
            className="flex items-center gap-1.5 px-4 py-2 rounded-xl bg-slate-900 hover:bg-slate-800 dark:bg-sky-600 dark:hover:bg-sky-500 text-white text-xs font-semibold shadow-xs transition-colors cursor-pointer disabled:opacity-50 flex-shrink-0"
          >
            {isSearching ? <Loader2 className="w-3.5 h-3.5 animate-spin" /> : <Sparkles className="w-3.5 h-3.5" />}
            <span>Search Vector DB</span>
          </button>
        </form>
      </div>

      {/* Real Search Results */}
      {hasSearched && (
        <div className="space-y-3">
          <div className="flex items-center justify-between">
            <span className="font-mono text-xs font-bold text-slate-500 uppercase tracking-wider">
              Retrieved Grounded Chunks ({searchResults.length})
            </span>
            <span className="text-[11px] font-mono text-slate-400">
              Clearance Filter: &le; {user?.clearance || 'CONFIDENTIAL'}
            </span>
          </div>

          {searchResults.length === 0 ? (
            <div className="p-8 rounded-xl border border-slate-200 dark:border-slate-800 bg-white dark:bg-slate-900 text-center space-y-2">
              <Lock className="w-8 h-8 text-slate-300 mx-auto" />
              <p className="text-xs text-slate-500">
                No matching chunks found within your clearance tier ({user?.clearance || 'CONFIDENTIAL'}).
              </p>
            </div>
          ) : (
            <div className="space-y-3">
              {searchResults.map((chunk, idx) => (
                <div
                  key={idx}
                  className="p-4 rounded-xl border border-slate-200 dark:border-slate-800 bg-white dark:bg-slate-900 space-y-2.5 shadow-2xs hover:border-sky-300 dark:hover:border-sky-700 transition-colors"
                >
                  <div className="flex items-center justify-between flex-wrap gap-2">
                    <div className="flex items-center gap-2">
                      <span className="px-2 py-0.5 rounded bg-sky-50 dark:bg-sky-950 text-sky-700 dark:text-sky-300 font-mono text-xs font-bold border border-sky-200 dark:border-sky-800">
                        {chunk.doc_id || 'SOP'}
                      </span>
                      <span className="text-xs font-medium text-slate-700 dark:text-slate-300 font-mono">
                        {chunk.citation_str || `Section: ${chunk.section || 'General'}`}
                      </span>
                    </div>

                    <div className="flex items-center gap-2">
                      {getClearanceBadge(chunk.classification)}
                      {chunk.distance !== undefined && (
                        <span className="text-[10px] font-mono text-slate-400">
                          dist: {Number(chunk.distance).toFixed(3)}
                        </span>
                      )}
                    </div>
                  </div>

                  <div className="text-xs text-slate-700 dark:text-slate-300 font-sans leading-relaxed whitespace-pre-wrap bg-slate-50 dark:bg-slate-950/60 p-3 rounded-lg border border-slate-100 dark:border-slate-800/80">
                    {chunk.text || chunk.content}
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>
      )}

      {/* Real Indexed Documents Catalog */}
      <div className="space-y-3 pt-2">
        <div className="flex items-center justify-between">
          <span className="font-mono text-xs font-bold text-slate-500 uppercase tracking-wider">
            Indexed Engineering Documents ({documents.length})
          </span>
          <button
            type="button"
            onClick={loadDocuments}
            className="text-[11px] text-sky-600 dark:text-sky-400 font-mono hover:underline cursor-pointer"
          >
            Refresh List
          </button>
        </div>

        <div className="rounded-xl border border-slate-200 dark:border-slate-800 bg-white dark:bg-slate-900 overflow-hidden shadow-2xs">
          {isLoadingDocs ? (
            <div className="p-8 text-center text-xs text-slate-400 flex items-center justify-center gap-2">
              <Loader2 className="w-4 h-4 animate-spin" />
              <span>Loading documents from database...</span>
            </div>
          ) : documents.length === 0 ? (
            <div className="p-8 text-center text-xs text-slate-400 space-y-1">
              <Database className="w-6 h-6 mx-auto text-slate-300 mb-2" />
              <p>No documents found in knowledge base.</p>
              <p className="text-[11px] text-slate-400">Click &quot;Upload &amp; Ingest SOP&quot; above to add your first document.</p>
            </div>
          ) : (
            <table className="w-full text-left border-collapse">
              <thead>
                <tr className="border-b border-slate-100 dark:border-slate-800 bg-slate-50/70 dark:bg-slate-950/50 font-mono text-[10px] text-slate-400 uppercase tracking-wider">
                  <th className="py-2.5 px-4 font-bold">Document ID</th>
                  <th className="py-2.5 px-4 font-bold">Filename</th>
                  <th className="py-2.5 px-4 font-bold">Clearance</th>
                  <th className="py-2.5 px-4 font-bold">Chunks</th>
                  <th className="py-2.5 px-4 font-bold text-right">Status</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-100 dark:divide-slate-800 text-xs">
                {documents.map((doc) => (
                  <tr key={doc.id} className="hover:bg-slate-50/80 dark:hover:bg-slate-800/40 transition-colors">
                    <td className="py-3 px-4 font-mono font-bold text-slate-900 dark:text-slate-100">
                      {doc.doc_id}
                    </td>
                    <td className="py-3 px-4 text-slate-700 dark:text-slate-300 font-mono text-[11px]">
                      <div className="flex items-center gap-2">
                        <FileText className="w-3.5 h-3.5 text-slate-400" />
                        <span>{doc.filename}</span>
                      </div>
                    </td>
                    <td className="py-3 px-4">
                      {getClearanceBadge(doc.classification)}
                    </td>
                    <td className="py-3 px-4 font-mono text-slate-500">
                      {doc.chunks} chunk(s)
                    </td>
                    <td className="py-3 px-4 text-right">
                      <span className="inline-flex items-center gap-1 text-[11px] font-mono text-emerald-600 dark:text-emerald-400 font-medium">
                        <span className="w-1.5 h-1.5 rounded-full bg-emerald-500" />
                        {doc.status || 'Active'}
                      </span>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          )}
        </div>
      </div>
    </div>
  );
};
