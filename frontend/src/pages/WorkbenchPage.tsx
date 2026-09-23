import React, { useState, useRef } from 'react';
import { 
  Upload, 
  Calculator, 
  ArrowRight, 
  Send, 
  FileText, 
  Eye, 
  CheckCircle, 
  Cpu, 
  ExternalLink,
  Paperclip,
  X
} from 'lucide-react';
import { useNavigate } from 'react-router-dom';

export const WorkbenchPage: React.FC = () => {
  const navigate = useNavigate();
  const [prompt, setPrompt] = useState(
    'Correlate CDU-02 desalter inlet ultrasound scan with ASTM A106 Grade B limits and formulate CAPEX containment note.'
  );
  const [isExecuting, setIsExecuting] = useState(false);
  const [attachedFiles, setAttachedFiles] = useState<string[]>([]);

  const fileInputRef = useRef<HTMLInputElement>(null);

  const handleFileUpload = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files && e.target.files.length > 0) {
      const names = Array.from(e.target.files).map((f) => f.name);
      setAttachedFiles((prev) => [...prev, ...names]);
      e.target.value = '';
    }
  };

  const removeFile = (index: number) => {
    setAttachedFiles((prev) => prev.filter((_, i) => i !== index));
  };

  const handleExecute = () => {
    setIsExecuting(true);
    setTimeout(() => {
      setIsExecuting(false);
    }, 1200);
  };

  return (
    <div className="flex flex-col w-full max-w-6xl mx-auto pb-12 space-y-6">
      {/* Hidden file input */}
      <input
        ref={fileInputRef}
        type="file"
        multiple
        onChange={handleFileUpload}
        className="hidden"
        accept=".pdf,.docx,.xlsx,.txt,.csv,.png,.jpg"
      />

      {/* Hero Header */}
      <div className="text-center pt-4 pb-2 space-y-1.5">
        <h1 className="text-3xl font-bold text-slate-900 dark:text-slate-100 tracking-tight font-headline">
          What are we solving today?
        </h1>
        <p className="text-sm text-slate-500 dark:text-slate-400">
          Air-gapped intelligence for CDU-02 telemetry correlation and diagnostic synthesis.
        </p>
      </div>

      {/* Main Intelligent Command Deck */}
      <div className="rounded-xl bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 p-4 shadow-sm space-y-3">
        <textarea
          value={prompt}
          onChange={(e) => setPrompt(e.target.value)}
          rows={3}
          placeholder="Ask PRISM-AI to correlate telemetry, verify against engineering limits, or draft deliverables..."
          className="w-full bg-transparent resize-none border-none outline-none text-sm text-slate-800 dark:text-slate-200 placeholder:text-slate-400 leading-relaxed font-normal"
        />

        {/* Attached Files Strip */}
        {attachedFiles.length > 0 && (
          <div className="flex flex-wrap items-center gap-2 pt-2 border-t border-slate-100 dark:border-slate-800">
            {attachedFiles.map((fname, idx) => (
              <span
                key={idx}
                className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-md bg-slate-100 dark:bg-slate-800 text-xs text-slate-700 dark:text-slate-300 border border-slate-200 dark:border-slate-700 font-mono"
              >
                <Paperclip className="w-3 h-3 text-sky-500" />
                <span>{fname}</span>
                <button
                  type="button"
                  onClick={() => removeFile(idx)}
                  className="text-slate-400 hover:text-rose-500 ml-1 cursor-pointer"
                >
                  <X className="w-3 h-3" />
                </button>
              </span>
            ))}
          </div>
        )}

        {/* Toolbar */}
        <div className="flex items-center justify-between pt-1">
          <div className="flex items-center gap-2">
            <button
              type="button"
              onClick={() => fileInputRef.current?.click()}
              className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg border border-slate-200 dark:border-slate-700 hover:bg-slate-50 dark:hover:bg-slate-800/60 text-slate-700 dark:text-slate-300 text-xs font-medium transition-colors cursor-pointer"
            >
              <Upload className="w-3.5 h-3.5 text-slate-500" />
              <span>Upload File</span>
            </button>
            <button
              type="button"
              onClick={() => setPrompt("Calculate general wall thinning loss, exceedance, and hydrostatic proof pressure.")}
              className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg border border-slate-200 dark:border-slate-700 hover:bg-slate-50 dark:hover:bg-slate-800/60 text-slate-700 dark:text-slate-300 text-xs font-medium transition-colors cursor-pointer"
            >
              <Calculator className="w-3.5 h-3.5 text-slate-500" />
              <span>Run Calc</span>
            </button>
          </div>

          <button
            type="button"
            onClick={handleExecute}
            disabled={isExecuting}
            className="flex items-center gap-2 px-4 py-2 rounded-lg bg-slate-900 hover:bg-slate-800 dark:bg-sky-500 dark:hover:bg-sky-400 text-white font-medium text-xs shadow-sm transition-all cursor-pointer disabled:opacity-50"
          >
            <span>{isExecuting ? 'Executing...' : 'Execute Analysis'}</span>
            <ArrowRight className="w-3.5 h-3.5" />
          </button>
        </div>
      </div>

      {/* 2-Column Synthesis & Cited Sources Grid */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-6 items-start">
        {/* Left Column: AI Synthesis Card */}
        <div className="lg:col-span-8 rounded-xl bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 p-5 shadow-sm space-y-4">
          {/* Status Header */}
          <div className="flex items-center justify-between">
            <span className="px-2 py-0.5 rounded bg-emerald-50 dark:bg-emerald-950/40 text-emerald-700 dark:text-emerald-300 border border-emerald-200 dark:border-emerald-800/40 font-mono text-[10px] font-bold tracking-wider uppercase">
              AI SYNTHESIS READY
            </span>
            <span className="font-mono text-xs text-slate-400">1.86s runtime</span>
          </div>

          {/* Heading */}
          <div>
            <h2 className="text-xl font-bold text-slate-900 dark:text-slate-100 tracking-tight font-headline">
              Flange Corrosion Detected
            </h2>
            <p className="text-xs text-slate-500 dark:text-slate-400 font-medium mt-0.5">
              CDU-02 Desalter Inlet Flange · Sector 6 o'clock
            </p>
          </div>

          {/* 3 Metric Boxes */}
          <div className="grid grid-cols-3 gap-3">
            <div className="p-3 rounded-lg border border-slate-200 dark:border-slate-800 bg-slate-50/60 dark:bg-slate-950/40">
              <div className="font-mono text-[10px] text-slate-400 uppercase font-semibold">WALL DEGRADATION</div>
              <div className="text-xl font-bold text-rose-600 mt-1">1.8 mm</div>
              <div className="text-[11px] text-slate-500 mt-0.5">81.8% of 2.2mm limit</div>
            </div>

            <div className="p-3 rounded-lg border border-slate-200 dark:border-slate-800 bg-slate-50/60 dark:bg-slate-950/40">
              <div className="font-mono text-[10px] text-slate-400 uppercase font-semibold">PHYSICS RESIDUAL</div>
              <div className="text-xl font-bold text-slate-900 dark:text-slate-100 mt-1">48 Days</div>
              <div className="text-[11px] text-emerald-600 dark:text-emerald-400 font-semibold mt-0.5">Marginal Safe Window</div>
            </div>

            <div className="p-3 rounded-lg border border-slate-200 dark:border-slate-800 bg-slate-50/60 dark:bg-slate-950/40">
              <div className="font-mono text-[10px] text-slate-400 uppercase font-semibold">INTERVENTION</div>
              <div className="text-xl font-bold text-sky-600 dark:text-sky-400 mt-1">TURN-26</div>
              <div className="text-[11px] text-slate-500 mt-0.5">Containment Sleeve</div>
            </div>
          </div>

          {/* Paragraph */}
          <p className="text-xs text-slate-700 dark:text-slate-300 leading-relaxed">
            Ultrasonic attenuation anomalies show accelerated localized loss (0.32 mm/month) post sulfur surge. Recommend localized bolted mechanical enclosure clamp (ANSI 300#) with sealant injection prior to the 48-day threshold breach to maintain 98.4% capacity without shutdown.
          </p>

          {/* Action Buttons */}
          <div className="flex flex-wrap items-center gap-2.5 pt-2">
            <button
              type="button"
              onClick={() => navigate('/review')}
              className="flex items-center gap-2 px-4 py-2 rounded-lg bg-sky-600 hover:bg-sky-500 text-white font-medium text-xs shadow-sm transition-colors cursor-pointer"
            >
              <Send className="w-3.5 h-3.5" />
              <span>Send to Review Gate</span>
            </button>

            <button
              type="button"
              onClick={() => navigate('/artifacts')}
              className="flex items-center gap-2 px-3.5 py-2 rounded-lg border border-slate-200 dark:border-slate-700 hover:bg-slate-50 dark:hover:bg-slate-800 text-slate-700 dark:text-slate-300 text-xs font-medium transition-colors cursor-pointer"
            >
              <FileText className="w-3.5 h-3.5 text-slate-400" />
              <span>Generate Note</span>
            </button>

            <button
              type="button"
              onClick={() => navigate('/vision')}
              className="flex items-center gap-2 px-3.5 py-2 rounded-lg border border-slate-200 dark:border-slate-700 hover:bg-slate-50 dark:hover:bg-slate-800 text-slate-700 dark:text-slate-300 text-xs font-medium transition-colors cursor-pointer"
            >
              <Eye className="w-3.5 h-3.5 text-slate-400" />
              <span>View Sensor Feed</span>
            </button>
          </div>
        </div>

        {/* Right Column: Cited Sources Card */}
        <div className="lg:col-span-4 rounded-xl bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 p-5 shadow-sm space-y-4">
          <div className="flex items-center justify-between pb-2 border-b border-slate-100 dark:border-slate-800">
            <span className="font-mono text-xs uppercase font-bold text-slate-900 dark:text-slate-100 tracking-wider">
              CITED SOURCES
            </span>
            <span className="text-xs text-slate-400 font-mono">3 files</span>
          </div>

          <div className="space-y-3">
            <div className="p-3 rounded-lg border border-slate-100 dark:border-slate-800/80 bg-slate-50/50 dark:bg-slate-950/20 hover:bg-slate-50 dark:hover:bg-slate-800/40 transition-colors flex items-center justify-between">
              <div>
                <div className="text-xs font-semibold text-slate-900 dark:text-slate-100">CDU_Operating_SOP.pdf</div>
                <div className="text-[11px] text-slate-400 mt-0.5">Section 4.3 - Flange tolerances</div>
              </div>
              <span className="px-1.5 py-0.5 rounded bg-emerald-50 dark:bg-emerald-950/40 text-emerald-700 dark:text-emerald-300 text-[10px] font-mono font-bold">
                94%
              </span>
            </div>

            <div className="p-3 rounded-lg border border-slate-100 dark:border-slate-800/80 bg-slate-50/50 dark:bg-slate-950/20 hover:bg-slate-50 dark:hover:bg-slate-800/40 transition-colors flex items-center justify-between">
              <div>
                <div className="text-xs font-semibold text-slate-900 dark:text-slate-100">Inspection_Log_Sept.pdf</div>
                <div className="text-[11px] text-slate-400 mt-0.5">Sector 3 - ultrasonic survey</div>
              </div>
              <span className="px-1.5 py-0.5 rounded bg-emerald-50 dark:bg-emerald-950/40 text-emerald-700 dark:text-emerald-300 text-[10px] font-mono font-bold">
                92%
              </span>
            </div>

            <div className="p-3 rounded-lg border border-slate-100 dark:border-slate-800/80 bg-slate-50/50 dark:bg-slate-950/20 hover:bg-slate-50 dark:hover:bg-slate-800/40 transition-colors flex items-center justify-between">
              <div>
                <div className="text-xs font-semibold text-slate-900 dark:text-slate-100">Valve_Maint_Manual.pdf</div>
                <div className="text-[11px] text-slate-400 mt-0.5">Class 300 Raised Face clamps</div>
              </div>
              <span className="px-1.5 py-0.5 rounded bg-emerald-50 dark:bg-emerald-950/40 text-emerald-700 dark:text-emerald-300 text-[10px] font-mono font-bold">
                88%
              </span>
            </div>
          </div>

          <div className="pt-3 border-t border-slate-100 dark:border-slate-800 flex items-center justify-between text-xs font-mono">
            <span className="text-slate-400">Hardware State</span>
            <span className="text-emerald-600 dark:text-emerald-400 font-semibold flex items-center gap-1.5">
              <span className="w-1.5 h-1.5 rounded-full bg-emerald-500 animate-pulse" />
              Local RTX 3050
            </span>
          </div>
        </div>
      </div>
    </div>
  );
};
