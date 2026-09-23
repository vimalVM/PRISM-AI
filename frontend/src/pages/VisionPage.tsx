import React from 'react';
import { 
  Cpu, 
  Brain, 
  FileText, 
  Download, 
  AlertTriangle, 
  CheckCircle, 
  Activity, 
  Share2, 
  ShieldAlert 
} from 'lucide-react';
import { OpticalViewer } from '../components/vision/OpticalViewer';
import { useNavigate } from 'react-router-dom';

export const VisionPage: React.FC = () => {
  const navigate = useNavigate();

  return (
    <div className="flex flex-col w-full pb-10 space-y-6">
      {/* Top Banner */}
      <div className="flex items-center justify-between pb-2 border-b border-outline-variant/30">
        <div>
          <h1 className="font-headline text-xl font-bold text-on-surface">
            Optical & Vision Diagnostic Enclave
          </h1>
          <p className="text-xs text-on-surface-variant font-mono">
            Direct feed from Optical Rig A-4 & NDT Matrix · Local Gemma 4 E4B Multimodal Model
          </p>
        </div>
        <div className="flex items-center gap-2">
          <span className="font-mono text-xs px-2.5 py-1 rounded bg-surface-container text-tertiary border border-outline-variant/30 font-semibold">
            CDU-02 FLANGE #06-B
          </span>
        </div>
      </div>

      <div className="grid grid-cols-12 gap-6 items-start">
        {/* Left: Optical Inspection Canvas & Metric Strips (8 Columns) */}
        <div className="col-span-12 xl:col-span-8 flex flex-col space-y-4">
          <OpticalViewer />

          {/* Quick Timeline & Multi-spectral Telemetry Strip */}
          <div className="grid grid-cols-1 sm:grid-cols-3 gap-3">
            <div className="bg-surface-container-low p-3 rounded-lg border border-outline-variant/30 flex items-center gap-3">
              <div className="w-10 h-10 rounded-lg bg-surface-container-high flex items-center justify-center shrink-0">
                <Activity className="w-5 h-5 text-primary-container" />
              </div>
              <div className="min-w-0">
                <div className="font-mono text-[10px] text-on-surface-variant truncate uppercase">
                  HISTORICAL RUNOUT
                </div>
                <div className="font-mono text-sm font-semibold text-on-surface">24.8mm → 21.2mm</div>
              </div>
            </div>

            <div className="bg-surface-container-low p-3 rounded-lg border border-outline-variant/30 flex items-center gap-3">
              <div className="w-10 h-10 rounded-lg bg-surface-container-high flex items-center justify-center shrink-0">
                <Cpu className="w-5 h-5 text-tertiary" />
              </div>
              <div className="min-w-0">
                <div className="font-mono text-[10px] text-on-surface-variant truncate uppercase">
                  INGEST RESOLUTION
                </div>
                <div className="font-mono text-sm font-semibold text-on-surface">3840 × 2160 RAW</div>
              </div>
            </div>

            <div className="bg-surface-container-low p-3 rounded-lg border border-outline-variant/30 flex items-center gap-3">
              <div className="w-10 h-10 rounded-lg bg-surface-container-high flex items-center justify-center shrink-0">
                <AlertTriangle className="w-5 h-5 text-error" />
              </div>
              <div className="min-w-0">
                <div className="font-mono text-[10px] text-on-surface-variant truncate uppercase">
                  CORROSION RATE EST.
                </div>
                <div className="font-mono text-sm font-semibold text-error">0.12 mm/yr (+18%)</div>
              </div>
            </div>
          </div>
        </div>

        {/* Right: AI Inspection Findings & Diagnostics (4 Columns) */}
        <div className="col-span-12 xl:col-span-4 flex flex-col space-y-4">
          {/* Model Card Info */}
          <div className="bg-surface-container-low p-4 rounded-xl shadow-lg border border-outline-variant/30 space-y-3">
            <div className="flex items-center justify-between">
              <span className="font-mono text-[10px] text-outline tracking-wider uppercase font-semibold">
                INFERENCE SUBSYSTEM
              </span>
              <span className="px-2 py-0.5 rounded bg-surface-container-highest text-tertiary font-mono text-[10px] border border-outline-variant/20">
                OPTIMIZED ON-PREM
              </span>
            </div>
            <div className="flex items-center gap-3">
              <div className="w-9 h-9 rounded-lg bg-primary-container/15 border border-primary-container/30 flex items-center justify-center">
                <Brain className="w-5 h-5 text-primary-container" />
              </div>
              <div>
                <h2 className="font-headline text-sm text-on-surface font-semibold leading-tight">
                  Gemma 4 E4B Vision
                </h2>
                <div className="font-mono text-[10px] text-on-surface-variant">
                  TAG: gemma4:e4b · LOCAL OLLAMA
                </div>
              </div>
            </div>
            <div className="grid grid-cols-2 gap-2 pt-1 font-mono text-xs">
              <div className="bg-surface-container p-2 rounded border border-outline-variant/20">
                <span className="text-on-surface-variant text-[10px] block">TOTAL TOKENS:</span>
                <span className="text-on-surface font-semibold">1,248 T</span>
              </div>
              <div className="bg-surface-container p-2 rounded border border-outline-variant/20">
                <span className="text-on-surface-variant text-[10px] block">CONFIDENCE:</span>
                <span className="text-primary-container font-semibold">91.4%</span>
              </div>
            </div>
          </div>

          {/* Diagnostic Summary Details */}
          <div className="bg-surface-container-low p-4 rounded-xl shadow-lg border border-outline-variant/30 space-y-3">
            <div className="flex items-center justify-between">
              <h2 className="font-headline text-sm text-on-surface font-semibold">Diagnostic Summary</h2>
              <span className="text-tertiary font-mono text-[10px] font-bold">L2 VALIDATED</span>
            </div>

            <div className="p-3 rounded-lg bg-surface-container border border-outline-variant/20 text-xs leading-relaxed space-y-2">
              <div className="font-semibold text-primary">Surface Pitting Observations:</div>
              <p className="text-on-surface-variant text-xs">
                Micro-cavitations observed across the bottom sector of the raised face weld joint. Attenuation correlates with 1.8mm localized loss against 2.2mm retirement boundary.
              </p>
            </div>

            {/* MANDATORY Engineering Safety Notice (AGENTS.md & 02_DESIGN_DOC.md §9.6) */}
            <div className="p-3 rounded-lg bg-amber-500/10 border border-amber-500/30 text-amber-300 flex items-start gap-2 text-xs">
              <ShieldAlert className="w-4 h-4 shrink-0 text-amber-400 mt-0.5" />
              <div className="flex flex-col font-mono text-[10px] leading-tight">
                <span className="font-bold uppercase tracking-wider text-amber-400">
                  Engineering Safety Boundary Notice
                </span>
                <span className="text-on-surface-variant mt-0.5">
                  Visual observation — not a dimensional measurement. Output is uncertified guidance and requires human inspection sign-off before safety-critical decisions.
                </span>
              </div>
            </div>

            {/* Action Buttons */}
            <div className="pt-2 flex flex-col gap-2">
              <button
                onClick={() => navigate('/artifacts')}
                className="w-full flex items-center justify-center gap-2 px-3 py-2 rounded-lg bg-primary-container text-surface font-mono text-xs font-bold hover:shadow-cyan-glow transition-all"
              >
                <FileText className="w-4 h-4" />
                <span>Add to Engineering Memo</span>
              </button>
              <button
                onClick={() => navigate('/review')}
                className="w-full flex items-center justify-center gap-2 px-3 py-2 rounded-lg bg-surface-container hover:bg-surface-container-high text-on-surface font-mono text-xs border border-outline-variant/30 transition-colors"
              >
                <CheckCircle className="w-4 h-4 text-tertiary" />
                <span>Submit to Human Review Gate</span>
              </button>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};
