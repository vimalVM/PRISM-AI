import React from 'react';
import { 
  Sparkles, 
  AlertTriangle, 
  Clock, 
  Wrench, 
  Shield, 
  CheckCircle, 
  ArrowRight, 
  FileText, 
  Eye, 
  Database 
} from 'lucide-react';
import { useNavigate } from 'react-router-dom';

interface RecommendationCardProps {
  onSendToReview?: () => void;
  onGenerateReport?: () => void;
}

export const RecommendationCard: React.FC<RecommendationCardProps> = ({
  onSendToReview,
  onGenerateReport,
}) => {
  const navigate = useNavigate();

  return (
    <div className="rounded-xl bg-surface-container-lowest overflow-hidden shadow-lg border border-outline-variant/30">
      {/* Top Clearance Watermark Ribbon */}
      <div className="h-1 w-full bg-gradient-to-r from-amber-500 via-primary-container to-tertiary" />

      <div className="p-6 flex flex-col space-y-4">
        {/* Card Header & Metadata */}
        <div className="flex flex-wrap items-center justify-between gap-3 pb-3 border-b border-outline-variant/20">
          <div className="flex items-center gap-3">
            <div className="w-8 h-8 rounded-lg bg-primary-container/10 border border-primary-container/30 flex items-center justify-center text-primary-container">
              <Sparkles className="w-4 h-4" />
            </div>
            <div>
              <h3 className="font-headline text-base font-semibold text-on-surface">
                Synthesized Engineering Recommendation
              </h3>
              <span className="font-mono text-xs text-outline">
                Correlated from 3 telemetry datasets & ultrasound spatial log
              </span>
            </div>
          </div>

          {/* Clearance Badge */}
          <div className="flex items-center gap-1.5 px-2.5 py-1 rounded bg-surface-container text-amber-400 font-mono text-xs font-bold tracking-wider border border-amber-500/30">
            <Shield className="w-3.5 h-3.5 text-amber-400" />
            <span>CONFIDENTIAL // INTERNAL ONLY</span>
          </div>
        </div>

        {/* Rich Visual Engineering Canvas (3 Metric Cards) */}
        <div className="grid grid-cols-1 md:grid-cols-3 gap-3">
          {/* Metric 1: Wall Degradation */}
          <div className="p-4 rounded-lg bg-surface-container border border-outline-variant/30 flex flex-col justify-between">
            <div className="flex items-center justify-between">
              <span className="font-mono text-[10px] text-outline font-semibold uppercase">ANOMALY DETECTED</span>
              <AlertTriangle className="w-4 h-4 text-error" />
            </div>
            <div className="my-2">
              <div className="font-display text-2xl font-bold text-error tracking-tight">1.8 mm</div>
              <div className="text-xs text-on-surface-variant">Pitting depth on CDU-02 inlet flange</div>
            </div>
            <div className="w-full bg-surface-container-highest rounded-full h-1.5 overflow-hidden">
              <div className="bg-error h-full rounded-full" style={{ width: '81.8%' }} />
            </div>
            <div className="flex justify-between font-mono text-[10px] text-outline mt-1.5">
              <span>Threshold: 2.2mm</span>
              <span className="text-error font-medium">81.8% of limit</span>
            </div>
          </div>

          {/* Metric 2: Physics Lifespan */}
          <div className="p-4 rounded-lg bg-surface-container border border-outline-variant/30 flex flex-col justify-between">
            <div className="flex items-center justify-between">
              <span className="font-mono text-[10px] text-outline font-semibold uppercase">PHYSICS RESIDUAL</span>
              <Clock className="w-4 h-4 text-tertiary" />
            </div>
            <div className="my-2">
              <div className="font-display text-2xl font-bold text-tertiary-fixed tracking-tight">48 Days</div>
              <div className="text-xs text-on-surface-variant">Operating at 42.1 BAR @ 184.2°C</div>
            </div>
            {/* Inline Micro Sparkline SVG */}
            <div className="h-6 w-full flex items-end">
              <svg className="w-full h-full text-tertiary-fixed-dim" fill="none" preserveAspectRatio="none" viewBox="0 0 100 24">
                <path d="M0 4 C20 6, 40 10, 60 16 C80 20, 95 22, 100 24" stroke="currentColor" strokeLinecap="round" strokeWidth="2.5" />
                <path d="M0 4 C20 6, 40 10, 60 16 C80 20, 95 22, 100 24 L100 24 L0 24 Z" fill="currentColor" fillOpacity="0.12" />
              </svg>
            </div>
            <div className="flex justify-between font-mono text-[10px] text-outline mt-1.5">
              <span>Baseline: ASTM A106-B</span>
              <span className="text-tertiary font-medium">Marginal</span>
            </div>
          </div>

          {/* Metric 3: Target Action Window */}
          <div className="p-4 rounded-lg bg-surface-container border border-outline-variant/30 flex flex-col justify-between">
            <div className="flex items-center justify-between">
              <span className="font-mono text-[10px] text-outline font-semibold uppercase">INTERVENTION CLASS</span>
              <Wrench className="w-4 h-4 text-primary-container" />
            </div>
            <div className="my-2">
              <div className="font-display text-2xl font-bold text-primary tracking-tight">TURN-26</div>
              <div className="text-xs text-on-surface-variant">Hot-tapping containment sleeve</div>
            </div>
            <div className="flex items-center gap-1.5 py-1 px-2 rounded bg-surface-container-high text-primary-container text-xs font-mono">
              <CheckCircle className="w-3.5 h-3.5" />
              <span>ASME B31.3 Compliant</span>
            </div>
            <div className="flex justify-between font-mono text-[10px] text-outline mt-1.5">
              <span>CAPEX Est: $42,500</span>
              <span className="text-on-surface">No shutdown</span>
            </div>
          </div>
        </div>

        {/* Structured Finding Narrative */}
        <div className="p-4 rounded-lg bg-surface-container-low border border-outline-variant/20 text-on-surface text-sm leading-relaxed space-y-2">
          <p>
            <strong className="text-primary-container font-semibold">Corrosion Propagation Analysis: </strong>
            Desalter Inlet Flange section shows isolated ultrasonic attenuation anomalies concentrated at 6 o'clock orientation. The localized loss rate has accelerated by 0.32 mm/month following the crude slate sulfur surge recorded on Sept 14th.
          </p>
          <p>
            <strong className="text-tertiary-fixed font-semibold">Immediate Operational Remedy: </strong>
            Deploy localized bolted mechanical enclosure clamp (Rating: ANSI 300#) with sealant injection prior to the calculated 48-day window breach. This bypasses the requirement for early CDU-02 offline shutdown, maintaining crude throughput at 98.4% capacity.
          </p>
        </div>

        {/* Action Buttons Bar */}
        <div className="pt-2 flex flex-wrap items-center justify-between gap-3 border-t border-outline-variant/20">
          <div className="flex flex-wrap items-center gap-2">
            <button
              onClick={() => navigate('/review')}
              className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-primary-container text-surface font-mono text-xs font-semibold hover:shadow-cyan-glow transition-all"
            >
              <span>Send to Review Queue</span>
              <ArrowRight className="w-3.5 h-3.5" />
            </button>
            <button
              onClick={() => navigate('/artifacts')}
              className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-surface-container hover:bg-surface-container-high text-on-surface font-mono text-xs border border-outline-variant/30 transition-colors"
            >
              <FileText className="w-3.5 h-3.5 text-tertiary" />
              <span>Generate CAPEX Note</span>
            </button>
            <button
              onClick={() => navigate('/vision')}
              className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-surface-container hover:bg-surface-container-high text-on-surface-variant hover:text-on-surface font-mono text-xs border border-outline-variant/30 transition-colors"
            >
              <Eye className="w-3.5 h-3.5 text-primary" />
              <span>View Optical Feed</span>
            </button>
          </div>
          <button
            onClick={() => navigate('/kb')}
            className="flex items-center gap-1.5 px-2.5 py-1.5 rounded bg-surface-container-high text-outline hover:text-on-surface font-mono text-[10px] transition-colors"
          >
            <Database className="w-3 h-3" />
            <span>Inspect Raw Vectors (12 Chunks)</span>
          </button>
        </div>
      </div>
    </div>
  );
};
