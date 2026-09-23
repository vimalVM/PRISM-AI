import React, { useState, useRef } from 'react';
import { 
  Upload, 
  Image as ImageIcon, 
  Search, 
  Calculator, 
  FileText, 
  ArrowRight, 
  ShieldCheck, 
  Sparkles,
  X,
  FileCheck,
  Paperclip
} from 'lucide-react';

export interface AttachedFile {
  id: string;
  name: string;
  size: string;
  type: 'document' | 'image';
  rawFile?: File;
  previewUrl?: string;
}

interface CommandDeckProps {
  onExecute: (prompt: string, attachments?: AttachedFile[]) => void;
  isLoading?: boolean;
}

export const CommandDeck: React.FC<CommandDeckProps> = ({ onExecute, isLoading = false }) => {
  const [prompt, setPrompt] = useState(
    'Correlate CDU-02 desalter inlet ultrasound scan with ASTM A106 Grade B limits and formulate CAPEX containment note.'
  );
  const [attachedFiles, setAttachedFiles] = useState<AttachedFile[]>([]);
  const [isDragging, setIsDragging] = useState(false);

  const docInputRef = useRef<HTMLInputElement>(null);
  const imgInputRef = useRef<HTMLInputElement>(null);

  const formatFileSize = (bytes: number): string => {
    if (bytes < 1024) return `${bytes} B`;
    if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`;
    return `${(bytes / (1024 * 1024)).toFixed(1)} MB`;
  };

  const addFiles = (files: FileList | File[]) => {
    const newAttachments: AttachedFile[] = [];
    Array.from(files).forEach((file) => {
      const isImg = file.type.startsWith('image/');
      const previewUrl = isImg ? URL.createObjectURL(file) : undefined;
      newAttachments.push({
        id: `att-${Date.now()}-${Math.random().toString(36).substr(2, 6)}`,
        name: file.name,
        size: formatFileSize(file.size),
        type: isImg ? 'image' : 'document',
        rawFile: file,
        previewUrl,
      });
    });

    if (newAttachments.length > 0) {
      setAttachedFiles((prev) => [...prev, ...newAttachments]);
      // If prompt is empty or default, suggest inspection context
      if (!prompt.trim() || prompt.includes('ASTM A106 Grade B')) {
        const first = newAttachments[0];
        if (first.type === 'image') {
          setPrompt(`Inspect attached optical scan ${first.name} for surface corrosion, fatigue cracks, and anomalous deformation using Gemma 4 E4B.`);
        } else {
          setPrompt(`Extract NDT ultrasonic thickness measurements from ${first.name}, correlate with ASME tolerances, and prepare containment memo.`);
        }
      }
    }
  };

  const handleDocChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files && e.target.files.length > 0) {
      addFiles(e.target.files);
      e.target.value = '';
    }
  };

  const handleImgChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files && e.target.files.length > 0) {
      addFiles(e.target.files);
      e.target.value = '';
    }
  };

  const removeAttachment = (id: string) => {
    setAttachedFiles((prev) => {
      const item = prev.find((a) => a.id === id);
      if (item?.previewUrl) {
        URL.revokeObjectURL(item.previewUrl);
      }
      return prev.filter((a) => a.id !== id);
    });
  };

  const handleDrop = (e: React.DragEvent) => {
    e.preventDefault();
    setIsDragging(false);
    if (e.dataTransfer.files && e.dataTransfer.files.length > 0) {
      addFiles(e.dataTransfer.files);
    }
  };

  const handleDragOver = (e: React.DragEvent) => {
    e.preventDefault();
    setIsDragging(true);
  };

  const handleDragLeave = (e: React.DragEvent) => {
    e.preventDefault();
    setIsDragging(false);
  };

  const handleKeyDown = (e: React.KeyboardEvent<HTMLTextAreaElement>) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      if ((prompt.trim() || attachedFiles.length > 0) && !isLoading) {
        onExecute(prompt, attachedFiles);
      }
    }
  };

  return (
    <div className="relative overflow-hidden rounded-xl bg-surface-container-lowest p-6 shadow-md border border-outline-variant/30">
      {/* Hidden file inputs */}
      <input
        ref={docInputRef}
        type="file"
        multiple
        accept=".pdf,.docx,.xlsx,.txt,.csv,.log,.json"
        className="hidden"
        onChange={handleDocChange}
      />
      <input
        ref={imgInputRef}
        type="file"
        multiple
        accept="image/*"
        className="hidden"
        onChange={handleImgChange}
      />

      {/* Ambient Radial Gradient Glow */}
      <div className="pointer-events-none absolute -top-24 left-1/3 w-96 h-96 bg-primary-container/5 rounded-full blur-3xl" />

      <div className="relative z-10 flex flex-col space-y-4">
        {/* Header */}
        <div className="flex items-start justify-between">
          <div>
            <div className="flex items-center gap-2 mb-1">
              <span className="font-mono text-[10px] uppercase text-outline tracking-widest font-semibold">
                Sovereign Operator Workbench
              </span>
              <span className="w-1 h-1 rounded-full bg-outline-variant" />
              <span className="font-mono text-[10px] text-tertiary font-semibold">NODE-LOCAL CLUSTER #04</span>
            </div>
            <h1 className="font-headline text-2xl lg:text-3xl text-on-surface tracking-tight font-bold">
              What are we solving today?
            </h1>
            <p className="text-sm text-on-surface-variant max-w-2xl mt-1">
              Air-gapped telemetry, local vector embeddings, and on-prem neural pipelines ready for zero-egress autonomous execution.
            </p>
          </div>
          <div className="hidden md:flex items-center gap-1.5 px-2.5 py-1 rounded bg-surface-container text-outline font-mono text-xs border border-outline-variant/30">
            <ShieldCheck className="w-3.5 h-3.5 text-tertiary" />
            <span className="text-on-surface">L2 CLEARANCE ACTIVE</span>
          </div>
        </div>

        {/* Large Intelligent Command Prompt with Drag & Drop */}
        <div 
          onDragOver={handleDragOver}
          onDragLeave={handleDragLeave}
          onDrop={handleDrop}
          className={`mt-2 rounded-xl bg-surface-container p-3 border shadow-sm transition-all ${
            isDragging 
              ? 'border-primary-container ring-2 ring-primary-container/30 bg-surface-container-high' 
              : 'border-outline-variant/30 focus-within:border-primary-container/60 focus-within:shadow-[0_0_24px_rgba(0,229,255,0.12)]'
          }`}
        >
          <div className="flex items-start justify-between gap-3">
            <textarea
              value={prompt}
              onChange={(e) => setPrompt(e.target.value)}
              onKeyDown={handleKeyDown}
              rows={attachedFiles.length > 0 ? 2 : 3}
              placeholder="Ask PRISM-AI to analyse documents, inspect equipment, calculate, search internal knowledge, or drag & drop files here..."
              className="w-full bg-transparent resize-none border-none outline-none text-sm text-on-surface placeholder:text-outline font-normal leading-relaxed selection:bg-primary-container selection:text-on-primary-container"
            />
            {/* Auto Route Pill */}
            <div className="shrink-0 flex items-center gap-1.5 px-2.5 py-1 rounded bg-surface-container-high text-primary-container border border-primary-container/30 shadow-[0_0_12px_rgba(0,229,255,0.2)]">
              <span className="w-1.5 h-1.5 rounded-full bg-primary-container animate-pulse" />
              <span className="font-mono text-[10px] tracking-widest font-bold">AUTO ROUTE</span>
            </div>
          </div>

          {/* Attached Files List */}
          {attachedFiles.length > 0 && (
            <div className="mt-2.5 pt-2 border-t border-outline-variant/20 flex flex-wrap items-center gap-2">
              <div className="flex items-center gap-1 text-[11px] font-mono text-outline uppercase font-semibold mr-1">
                <Paperclip className="w-3.5 h-3.5 text-primary-container" />
                <span>Attached ({attachedFiles.length}):</span>
              </div>
              {attachedFiles.map((file) => (
                <div
                  key={file.id}
                  className="flex items-center gap-2 px-2.5 py-1 rounded-md bg-surface-container-highest border border-outline-variant/40 text-on-surface text-xs shadow-sm hover:border-primary-container/40 transition-colors"
                >
                  {file.type === 'image' ? (
                    <ImageIcon className="w-3.5 h-3.5 text-secondary shrink-0" />
                  ) : (
                    <FileText className="w-3.5 h-3.5 text-primary-container shrink-0" />
                  )}
                  <span className="font-medium truncate max-w-[180px]">{file.name}</span>
                  <span className="font-mono text-[10px] text-on-surface-variant">({file.size})</span>
                  <button
                    type="button"
                    onClick={() => removeAttachment(file.id)}
                    title="Remove file"
                    className="text-on-surface-variant hover:text-error transition-colors ml-0.5"
                  >
                    <X className="w-3.5 h-3.5" />
                  </button>
                </div>
              ))}
            </div>
          )}

          {/* Action Toolbar */}
          <div className="mt-3 pt-2 flex flex-wrap items-center justify-between gap-2 bg-surface-container-low px-3 py-2 rounded-lg border border-outline-variant/20">
            <div className="flex flex-wrap items-center gap-1.5">
              <button
                type="button"
                onClick={() => docInputRef.current?.click()}
                className="flex items-center gap-1.5 px-2.5 py-1 rounded bg-surface-container hover:bg-surface-container-high text-on-surface-variant hover:text-on-surface text-xs font-medium transition-colors border border-outline-variant/20"
              >
                <Upload className="w-3.5 h-3.5 text-primary-container" />
                <span>Upload Document</span>
              </button>
              <button
                type="button"
                onClick={() => imgInputRef.current?.click()}
                className="flex items-center gap-1.5 px-2.5 py-1 rounded bg-surface-container hover:bg-surface-container-high text-on-surface-variant hover:text-on-surface text-xs font-medium transition-colors border border-outline-variant/20"
              >
                <ImageIcon className="w-3.5 h-3.5 text-secondary" />
                <span>Upload Image</span>
              </button>
              <button
                type="button"
                onClick={() => setPrompt("Search knowledge base for CDU Operating SOP Section 4.3.")}
                className="flex items-center gap-1.5 px-2.5 py-1 rounded bg-surface-container hover:bg-surface-container-high text-on-surface-variant hover:text-on-surface text-xs font-medium transition-colors border border-outline-variant/20"
              >
                <Search className="w-3.5 h-3.5 text-tertiary" />
                <span>Knowledge Search</span>
              </button>
              <button
                type="button"
                onClick={() => setPrompt("Calculate general wall thinning loss, exceedance, and hydrostatic proof pressure.")}
                className="flex items-center gap-1.5 px-2.5 py-1 rounded bg-surface-container hover:bg-surface-container-high text-on-surface-variant hover:text-on-surface text-xs font-medium transition-colors border border-outline-variant/20"
              >
                <Calculator className="w-3.5 h-3.5 text-secondary-fixed" />
                <span>Run Calculation</span>
              </button>
              <button
                type="button"
                onClick={() => setPrompt("Generate Approval Note DOCX for CDU-02 inspection.")}
                className="flex items-center gap-1.5 px-2.5 py-1 rounded bg-surface-container hover:bg-surface-container-high text-on-surface-variant hover:text-on-surface text-xs font-medium transition-colors border border-outline-variant/20"
              >
                <FileText className="w-3.5 h-3.5 text-primary" />
                <span>Generate Report</span>
              </button>
            </div>

            {/* Execute Button */}
            <div className="flex items-center gap-3">
              <span className="hidden sm:inline font-mono text-[10px] text-outline">⏎ Run · ⇧⏎ Newline</span>
              <button
                type="button"
                disabled={isLoading || (!prompt.trim() && attachedFiles.length === 0)}
                onClick={() => onExecute(prompt, attachedFiles)}
                className="flex items-center gap-1.5 px-4 py-2 rounded-lg bg-primary-container text-surface font-mono text-xs font-bold hover:shadow-cyan-glow transition-all disabled:opacity-50 cursor-pointer"
              >
                <span>{isLoading ? 'Executing...' : 'Execute'}</span>
                <ArrowRight className="w-4 h-4" />
              </button>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};
