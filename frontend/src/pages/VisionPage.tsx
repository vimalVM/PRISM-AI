import React from 'react';
import { 
  Cpu, 
  Brain, 
  FileText, 
  Download, 
  AlertTriangle, 
  CheckCircle, 
  Activity, 
  RotateCw,
  Camera,
  ExternalLink,
  ChevronRight,
  ShieldCheck,
  Send,
  Wrench
} from 'lucide-react';
import { OpticalViewer } from '../components/vision/OpticalViewer';
import { useNavigate } from 'react-router-dom';

export const VisionPage: React.FC = () => {
  const navigate = useNavigate();

  return (
    <div className="flex flex-col w-full max-w-7xl mx-auto pb-12 space-y-5">
      {/* Top Header & Actions */}
      <div className="flex flex-col lg:flex-row lg:items-center justify-between gap-4 pt-2">
        <div>
          <div className="font-mono text-[10px] text-sky-600 dark:text-sky-400 font-bold uppercase tracking-wider mb-1">
            DIAGNOSTIC VISION ENGINE | FLIR PROTOCOL v1.1 | SECTOR-2B
          </div>
          <h1 className="text-2xl font-bold text-slate-900 dark:text-slate-100 tracking-tight font-headline">
            Inspection Vision
          </h1>
          <p className="text-xs text-slate-500 dark:text-slate-400 mt-0.5">
            Optical & Thermal Anomaly Detection
          </p>
        </div>

        <div className="flex flex-wrap items-center gap-2">
          <button
            type="button"
            className="px-3 py-1.5 rounded-lg border border-slate-200 dark:border-slate-700 bg-white dark:bg-slate-900 text-slate-700 dark:text-slate-300 text-xs font-medium hover:bg-slate-50 dark:hover:bg-slate-800 transition-colors cursor-pointer"
          >
            Select Stream
          </button>
          <button
            type="button"
            className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg border border-slate-200 dark:border-slate-700 bg-white dark:bg-slate-900 text-slate-700 dark:text-slate-300 text-xs font-medium hover:bg-slate-50 dark:hover:bg-slate-800 transition-colors cursor-pointer"
          >
            <Camera className="w-3.5 h-3.5 text-slate-400" />
            <span>Capture Frame</span>
          </button>
          <button
            type="button"
            className="px-3 py-1.5 rounded-lg border border-slate-200 dark:border-slate-700 bg-white dark:bg-slate-900 text-slate-700 dark:text-slate-300 text-xs font-medium hover:bg-slate-50 dark:hover:bg-slate-800 transition-colors cursor-pointer"
          >
            Export Report
          </button>
          <button
            type="button"
            className="flex items-center gap-1.5 px-3.5 py-1.5 rounded-lg bg-sky-600 hover:bg-sky-500 text-white font-medium text-xs shadow-sm transition-colors cursor-pointer"
          >
            <RotateCw className="w-3.5 h-3.5" />
            <span>Re-run Model</span>
          </button>
        </div>
      </div>

      {/* Sensor Stream Sub-Status Strip */}
      <div className="rounded-xl bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 px-4 py-2 flex flex-wrap items-center justify-between gap-3 text-xs font-mono shadow-sm">
        <div className="flex items-center gap-4">
          <div className="flex items-center gap-2">
            <span className="w-2 h-2 rounded-full bg-emerald-500 animate-pulse" />
            <span className="text-slate-400">FEED:</span>
            <span className="font-semibold text-slate-900 dark:text-slate-100">CDU Unit 02 - Line 14A</span>
          </div>
          <span className="text-slate-300 dark:text-slate-700">|</span>
          <div className="flex items-center gap-2">
            <span className="text-slate-400">MODEL:</span>
            <span className="font-semibold text-slate-900 dark:text-slate-100">Gemma 4 E4B Vision</span>
          </div>
        </div>

        <div className="flex items-center gap-2 text-emerald-600 dark:text-emerald-400 font-semibold text-[11px]">
          <span className="w-1.5 h-1.5 rounded-full bg-emerald-500" />
          <span>60 FPS RAW STREAM · AIR-GAPPED</span>
        </div>
      </div>

      {/* Main Grid: Left Video & 3 Strips (8 cols) + Right Diagnostics (4 cols) */}
      <div className="grid grid-cols-1 xl:grid-cols-12 gap-6 items-start">
        {/* Left Column: Optical Canvas & Metrics */}
        <div className="xl:col-span-8 flex flex-col space-y-4">
          <OpticalViewer />

          {/* 3 Metric Strips */}
          <div className="grid grid-cols-1 sm:grid-cols-3 gap-3">
            <div className="bg-white dark:bg-slate-900 p-3.5 rounded-xl border border-slate-200 dark:border-slate-800 shadow-sm flex items-center gap-3">
              <div className="w-10 h-10 rounded-lg bg-sky-50 dark:bg-sky-950/60 border border-sky-100 dark:border-sky-900 flex items-center justify-center shrink-0 text-sky-600">
                <Activity className="w-5 h-5" />
              </div>
              <div className="min-w-0">
                <div className="font-mono text-[10px] text-slate-400 uppercase font-semibold">HISTORICAL RUNOUT</div>
                <div className="text-sm font-bold text-slate-900 dark:text-slate-100 font-mono mt-0.5">24.8mm → 21.2mm</div>
              </div>
            </div>

            <div className="bg-white dark:bg-slate-900 p-3.5 rounded-xl border border-slate-200 dark:border-slate-800 shadow-sm flex items-center gap-3">
              <div className="w-10 h-10 rounded-lg bg-emerald-50 dark:bg-emerald-950/60 border border-emerald-100 dark:border-emerald-900 flex items-center justify-center shrink-0 text-emerald-600">
                <Cpu className="w-5 h-5" />
              </div>
              <div className="min-w-0">
                <div className="font-mono text-[10px] text-slate-400 uppercase font-semibold">INGEST RESOLUTION</div>
                <div className="text-sm font-bold text-slate-900 dark:text-slate-100 font-mono mt-0.5">3840 × 2160 RAW</div>
              </div>
            </div>

            <div className="bg-white dark:bg-slate-900 p-3.5 rounded-xl border border-slate-200 dark:border-slate-800 shadow-sm flex items-center gap-3">
              <div className="w-10 h-10 rounded-lg bg-rose-50 dark:bg-rose-950/60 border border-rose-100 dark:border-rose-900 flex items-center justify-center shrink-0 text-rose-600">
                <AlertTriangle className="w-5 h-5" />
              </div>
              <div className="min-w-0">
                <div className="font-mono text-[10px] text-slate-400 uppercase font-semibold">CORROSION RATE EST.</div>
                <div className="text-sm font-bold text-rose-600 font-mono mt-0.5">0.12 mm/yr (+18%)</div>
              </div>
            </div>
          </div>
        </div>

        {/* Right Column: AI Diagnostics & Human-in-the-Loop Actions */}
        <div className="xl:col-span-4 flex flex-col space-y-4">
          {/* Inference Subsystem Tile */}
          <div className="rounded-xl bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 p-4 shadow-sm space-y-3">
            <div className="flex items-center justify-between">
              <span className="font-mono text-[10px] uppercase font-bold text-slate-400 tracking-wider">
                INFERENCE SUBSYSTEM
              </span>
              <span className="px-2 py-0.5 rounded bg-emerald-50 dark:bg-emerald-950/40 text-emerald-700 dark:text-emerald-300 font-mono text-[10px] font-bold">
                ON-PREM
              </span>
            </div>

            <div className="flex items-center gap-3">
              <div className="w-9 h-9 rounded-lg bg-sky-50 dark:bg-sky-950/60 border border-sky-200 dark:border-sky-800 flex items-center justify-center text-sky-600 shrink-0">
                <Brain className="w-5 h-5" />
              </div>
              <div>
                <div className="font-bold text-xs text-slate-900 dark:text-slate-100">Gemma 4 E4B Vision</div>
                <div className="font-mono text-[10px] text-slate-400">240t · VLLM Air-gapped Stack</div>
              </div>
            </div>

            <div className="grid grid-cols-2 gap-2 pt-2 border-t border-slate-100 dark:border-slate-800 font-mono text-xs">
              <div>
                <div className="text-[10px] text-slate-400">TOTAL TOKENS:</div>
                <div className="font-bold text-slate-900 dark:text-slate-100">1,248 T</div>
              </div>
              <div>
                <div className="text-[10px] text-slate-400">PRECISION METRIC:</div>
                <div className="font-bold text-sky-600 dark:text-sky-400">98.2% F1-SCORE</div>
              </div>
            </div>
          </div>

          {/* Diagnostic Summary */}
          <div className="rounded-xl bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 p-4 shadow-sm space-y-3">
            <div className="flex items-center justify-between">
              <span className="text-xs font-bold text-slate-900 dark:text-slate-100">Diagnostic Summary</span>
              <span className="px-2 py-0.5 rounded bg-rose-50 dark:bg-rose-950/40 text-rose-700 dark:text-rose-300 font-mono text-[10px] font-bold">
                SEV 2 - MED-HIGH
              </span>
            </div>

            <div>
              <div className="font-mono text-[10px] text-slate-400 uppercase">PRIMARY CLASSIFICATION</div>
              <div className="text-xs font-bold text-slate-900 dark:text-slate-100 mt-0.5">
                Severe localized galvanic pitting & surface oxidation
              </div>
            </div>

            <div className="space-y-1.5 text-xs">
              <div className="flex justify-between py-1 border-b border-slate-100 dark:border-slate-800">
                <span className="text-slate-400">Identified Component:</span>
                <span className="font-medium text-slate-800 dark:text-slate-200">Valve flange weld-neck</span>
              </div>
              <div className="flex justify-between py-1 border-b border-slate-100 dark:border-slate-800">
                <span className="text-slate-400">Zone & Sector:</span>
                <span className="font-medium text-sky-600 dark:text-sky-400">Sector 2-B (North CDU)</span>
              </div>
              <div className="flex justify-between py-1 border-b border-slate-100 dark:border-slate-800">
                <span className="text-slate-400">Calculated Degradation:</span>
                <span className="font-bold text-rose-600">0.12 mm/year</span>
              </div>
              <div className="flex justify-between py-1">
                <span className="text-slate-400">Safe Remaining Life:</span>
                <span className="font-medium text-slate-800 dark:text-slate-200">~14.4 Months</span>
              </div>
            </div>

            {/* AI Recommendation Box */}
            <div className="p-3 rounded-lg bg-sky-50/60 dark:bg-sky-950/40 border border-sky-100 dark:border-sky-900 space-y-1">
              <div className="font-mono text-[10px] text-sky-700 dark:text-sky-300 font-bold uppercase">
                AI ENGINEERING RECOMMENDATION
              </div>
              <p className="text-[11px] text-slate-700 dark:text-slate-300 italic leading-relaxed">
                "Schedule manual ultrasonic thickness verification during upcoming weekend maintenance window. Apply temporary anti-corrosion barrier tape."
              </p>
            </div>

            {/* Cited Source Chip */}
            <div className="p-2.5 rounded-lg border border-slate-200 dark:border-slate-800 flex items-center justify-between text-xs hover:bg-slate-50 dark:hover:bg-slate-800 transition-colors cursor-pointer">
              <div className="flex items-center gap-2">
                <CheckCircle className="w-3.5 h-3.5 text-emerald-500" />
                <span className="font-semibold text-slate-800 dark:text-slate-200">CDU_Operating_SOP.pdf §5.2</span>
              </div>
              <ExternalLink className="w-3.5 h-3.5 text-slate-400" />
            </div>
          </div>

          {/* Action Buttons */}
          <div className="space-y-2 pt-1">
            <button
              type="button"
              onClick={() => navigate('/review')}
              className="w-full flex items-center justify-center gap-2 px-4 py-2.5 rounded-lg bg-sky-600 hover:bg-sky-500 text-white font-medium text-xs shadow-sm transition-colors cursor-pointer"
            >
              <Send className="w-3.5 h-3.5" />
              <span>Submit to Human Review Gate</span>
            </button>

            <button
              type="button"
              className="w-full flex items-center justify-center gap-2 px-4 py-2 rounded-lg border border-slate-200 dark:border-slate-700 hover:bg-slate-50 dark:hover:bg-slate-800 text-slate-700 dark:text-slate-300 font-medium text-xs transition-colors cursor-pointer"
            >
              <Wrench className="w-3.5 h-3.5 text-slate-400" />
              <span>Attach to Work Order #WO-9042</span>
            </button>

            <button
              type="button"
              className="w-full flex items-center justify-center gap-2 px-4 py-2 rounded-lg border border-slate-200 dark:border-slate-700 hover:bg-slate-50 dark:hover:bg-slate-800 text-slate-700 dark:text-slate-300 font-medium text-xs transition-colors cursor-pointer"
            >
              <Download className="w-3.5 h-3.5 text-slate-400" />
              <span>Download Raw Inspection Log (J15)</span>
            </button>
          </div>
        </div>
      </div>
    </div>
  );
};
