import React from 'react';
import { ShieldCheck, WifiOff } from 'lucide-react';

export const LocalEnclaveCard: React.FC = () => {
  return (
    <div className="rounded-xl bg-surface-container-lowest p-4 shadow-sm border border-outline-variant/30">
      <div className="flex items-center justify-between mb-3 pb-2 border-b border-outline-variant/20">
        <span className="font-mono text-xs uppercase font-bold text-on-surface">
          LOCAL SYSTEM ENCLAVE
        </span>
        <span className="font-mono text-[10px] text-tertiary">STABLE 32.4°C</span>
      </div>

      <div className="space-y-2 font-mono text-xs">
        <div className="flex justify-between items-center text-outline">
          <span>Inference Device</span>
          <span className="text-on-surface">NVIDIA RTX 3050 (Laptop)</span>
        </div>
        <div className="flex justify-between items-center text-outline">
          <span>Quantization Matrix</span>
          <span className="text-on-surface">GGUF Q4_K_M (Zero Drift)</span>
        </div>
        <div className="flex justify-between items-center text-outline">
          <span>Context Window</span>
          <span className="text-on-surface">14,320 / 32,768 Tokens</span>
        </div>
        <div className="flex justify-between items-center text-outline pt-1 border-t border-outline-variant/20">
          <span>Network Hardware Status</span>
          <span className="text-tertiary font-bold tracking-wider flex items-center gap-1">
            <WifiOff className="w-3 h-3" />
            DISCONNECTED
          </span>
        </div>
      </div>
    </div>
  );
};
