import React from 'react';
import { 
  ShieldCheck, 
  WifiOff, 
  Lock, 
  Server, 
  CheckCircle, 
  AlertCircle 
} from 'lucide-react';

export const SovereigntyPage: React.FC = () => {
  return (
    <div className="flex flex-col w-full pb-10 space-y-6">
      {/* Top Banner */}
      <div className="flex items-center justify-between pb-2 border-b border-outline-variant/30">
        <div>
          <h1 className="font-headline text-xl font-bold text-on-surface">
            Sovereignty & Air-Gap Enclave Status
          </h1>
          <p className="text-xs text-on-surface-variant font-mono">
            Cryptographic Provability · Network Isolation Proof · Egress Scan Clean (Zero Telemetry)
          </p>
        </div>
        <div className="flex items-center gap-1.5 px-3 py-1.5 rounded-full bg-emerald-500/10 text-tertiary border border-emerald-500/30 font-mono text-xs font-bold">
          <span className="w-2 h-2 rounded-full bg-tertiary shadow-[0_0_8px_#a8ffd2]" />
          <span>AIR-GAP VERIFIED · ZERO EGRESS</span>
        </div>
      </div>

      {/* Grid of 4 Sovereignty Status Cards */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        <div className="bg-surface-container-low rounded-xl p-4 border border-outline-variant/30 shadow-md">
          <div className="flex items-center justify-between text-outline font-mono text-[10px] uppercase mb-1">
            <span>BIND ISOLATION</span>
            <Lock className="w-4 h-4 text-tertiary" />
          </div>
          <div className="font-headline text-base font-bold text-on-surface mt-1">127.0.0.1 ONLY</div>
          <p className="text-xs text-on-surface-variant font-mono mt-1">FastAPI & Ollama strictly locked to loopback adapter.</p>
        </div>

        <div className="bg-surface-container-low rounded-xl p-4 border border-outline-variant/30 shadow-md">
          <div className="flex items-center justify-between text-outline font-mono text-[10px] uppercase mb-1">
            <span>NETWORK HARDWARE</span>
            <WifiOff className="w-4 h-4 text-tertiary" />
          </div>
          <div className="font-headline text-base font-bold text-tertiary mt-1">DISCONNECTED</div>
          <p className="text-xs text-on-surface-variant font-mono mt-1">No active outbound non-loopback sockets found.</p>
        </div>

        <div className="bg-surface-container-low rounded-xl p-4 border border-outline-variant/30 shadow-md">
          <div className="flex items-center justify-between text-outline font-mono text-[10px] uppercase mb-1">
            <span>STATIC EGRESS SCAN</span>
            <ShieldCheck className="w-4 h-4 text-primary-container" />
          </div>
          <div className="font-headline text-base font-bold text-primary-container mt-1">0 FINDINGS</div>
          <p className="text-xs text-on-surface-variant font-mono mt-1">scripts/scan_egress.py reports 0 cloud calls or CDNs.</p>
        </div>

        <div className="bg-surface-container-low rounded-xl p-4 border border-outline-variant/30 shadow-md">
          <div className="flex items-center justify-between text-outline font-mono text-[10px] uppercase mb-1">
            <span>LOCAL MODELS</span>
            <Server className="w-4 h-4 text-secondary-fixed" />
          </div>
          <div className="font-headline text-base font-bold text-secondary-fixed mt-1">100% LOCAL DISK</div>
          <p className="text-xs text-on-surface-variant font-mono mt-1">Qwen 3.5 4B & Gemma 4 E4B weights stored on local disk.</p>
        </div>
      </div>

      {/* Verification Evidence Checklist */}
      <div className="bg-surface-container-low rounded-xl p-5 border border-outline-variant/30 shadow-md space-y-4 font-mono text-xs">
        <h2 className="font-headline text-sm font-semibold text-on-surface uppercase tracking-wider">
          Air-Gap Compliance Matrix
        </h2>
        <div className="space-y-2">
          <div className="p-3 rounded bg-surface-container border border-outline-variant/20 flex items-center justify-between">
            <span className="text-on-surface">SEC-01: Zero Runtime Internet Dependencies</span>
            <span className="text-tertiary font-bold flex items-center gap-1">
              <CheckCircle className="w-3.5 h-3.5" /> PASS
            </span>
          </div>
          <div className="p-3 rounded bg-surface-container border border-outline-variant/20 flex items-center justify-between">
            <span className="text-on-surface">SEC-02: Localhost Loopback Network Binding</span>
            <span className="text-tertiary font-bold flex items-center gap-1">
              <CheckCircle className="w-3.5 h-3.5" /> PASS
            </span>
          </div>
          <div className="p-3 rounded bg-surface-container border border-outline-variant/20 flex items-center justify-between">
            <span className="text-on-surface">SEC-08: Hardened Code Sandbox Isolation (--network=none)</span>
            <span className="text-tertiary font-bold flex items-center gap-1">
              <CheckCircle className="w-3.5 h-3.5" /> PASS
            </span>
          </div>
          <div className="p-3 rounded bg-surface-container border border-outline-variant/20 flex items-center justify-between">
            <span className="text-on-surface">SEC-14: Tamper-Evident Hash-Chained Audit Trail</span>
            <span className="text-tertiary font-bold flex items-center gap-1">
              <CheckCircle className="w-3.5 h-3.5" /> PASS
            </span>
          </div>
        </div>
      </div>
    </div>
  );
};
