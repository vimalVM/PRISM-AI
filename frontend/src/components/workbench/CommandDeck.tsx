import React, { useState } from 'react';
import { 
  Upload, 
  Image, 
  Search, 
  Calculator, 
  FileText, 
  ArrowRight, 
  ShieldCheck, 
  Sparkles 
} from 'lucide-react';

interface CommandDeckProps {
  onExecute: (prompt: string) => void;
  isLoading?: boolean;
}

export const CommandDeck: React.FC<CommandDeckProps> = ({ onExecute, isLoading = false }) => {
  const [prompt, setPrompt] = useState(
    'Correlate CDU-02 desalter inlet ultrasound scan with ASTM A106 Grade B limits and formulate CAPEX containment note.'
  );

  const handleKeyDown = (e: React.KeyboardEvent<HTMLTextAreaElement>) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      if (prompt.trim() && !isLoading) {
        onExecute(prompt);
      }
    }
  };

  return (
    <div className="relative overflow-hidden rounded-xl bg-surface-container-lowest p-6 shadow-md border border-outline-variant/30">
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

        {/* Large Intelligent Command Prompt */}
        <div className="mt-2 rounded-xl bg-surface-container p-3 border border-outline-variant/30 shadow-sm transition-all focus-within:border-primary-container/60 focus-within:shadow-[0_0_24px_rgba(0,229,255,0.12)]">
          <div className="flex items-start justify-between gap-3">
            <textarea
              value={prompt}
              onChange={(e) => setPrompt(e.target.value)}
              onKeyDown={handleKeyDown}
              rows={3}
              placeholder="Ask PRISM-AI to analyse documents, inspect equipment, calculate, search internal knowledge, or generate a deliverable..."
              className="w-full bg-transparent resize-none border-none outline-none text-sm text-on-surface placeholder:text-outline font-normal leading-relaxed selection:bg-primary-container selection:text-on-primary-container"
            />
            {/* Auto Route Pill */}
            <div className="shrink-0 flex items-center gap-1.5 px-2.5 py-1 rounded bg-surface-container-high text-primary-container border border-primary-container/30 shadow-[0_0_12px_rgba(0,229,255,0.2)]">
              <span className="w-1.5 h-1.5 rounded-full bg-primary-container animate-pulse" />
              <span className="font-mono text-[10px] tracking-widest font-bold">AUTO ROUTE</span>
            </div>
          </div>

          {/* Action Toolbar */}
          <div className="mt-3 pt-2 flex flex-wrap items-center justify-between gap-2 bg-surface-container-low px-3 py-2 rounded-lg border border-outline-variant/20">
            <div className="flex flex-wrap items-center gap-1.5">
              <button
                type="button"
                onClick={() => setPrompt("Upload CDU inspection report and verify against ASME code.")}
                className="flex items-center gap-1.5 px-2.5 py-1 rounded bg-surface-container hover:bg-surface-container-high text-on-surface-variant hover:text-on-surface text-xs font-medium transition-colors"
              >
                <Upload className="w-3.5 h-3.5 text-primary-container" />
                <span>Upload Document</span>
              </button>
              <button
                type="button"
                onClick={() => setPrompt("Analyse CDU-02 flange photograph with Gemma 4 E4B vision.")}
                className="flex items-center gap-1.5 px-2.5 py-1 rounded bg-surface-container hover:bg-surface-container-high text-on-surface-variant hover:text-on-surface text-xs font-medium transition-colors"
              >
                <Image className="w-3.5 h-3.5 text-secondary" />
                <span>Upload Image</span>
              </button>
              <button
                type="button"
                onClick={() => setPrompt("Search knowledge base for CDU Operating SOP Section 4.3.")}
                className="flex items-center gap-1.5 px-2.5 py-1 rounded bg-surface-container hover:bg-surface-container-high text-on-surface-variant hover:text-on-surface text-xs font-medium transition-colors"
              >
                <Search className="w-3.5 h-3.5 text-tertiary" />
                <span>Knowledge Search</span>
              </button>
              <button
                type="button"
                onClick={() => setPrompt("Calculate general wall thinning loss, exceedance, and hydrostatic proof pressure.")}
                className="flex items-center gap-1.5 px-2.5 py-1 rounded bg-surface-container hover:bg-surface-container-high text-on-surface-variant hover:text-on-surface text-xs font-medium transition-colors"
              >
                <Calculator className="w-3.5 h-3.5 text-secondary-fixed" />
                <span>Run Calculation</span>
              </button>
              <button
                type="button"
                onClick={() => setPrompt("Generate Approval Note DOCX for CDU-02 inspection.")}
                className="flex items-center gap-1.5 px-2.5 py-1 rounded bg-surface-container hover:bg-surface-container-high text-on-surface-variant hover:text-on-surface text-xs font-medium transition-colors"
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
                disabled={isLoading || !prompt.trim()}
                onClick={() => onExecute(prompt)}
                className="flex items-center gap-1.5 px-4 py-2 rounded-lg bg-primary-container text-surface font-mono text-xs font-bold hover:shadow-cyan-glow transition-all disabled:opacity-50"
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
