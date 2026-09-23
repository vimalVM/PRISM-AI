import React from 'react';
import { Cpu } from 'lucide-react';

interface ModelBadgeProps {
  model: string;
  reason?: string;
  active?: boolean;
}

export const ModelBadge: React.FC<ModelBadgeProps> = ({ model, reason, active = false }) => {
  return (
    <div
      className={`inline-flex items-center gap-1.5 px-2 py-0.5 rounded font-mono text-xs border transition-all ${
        active
          ? 'bg-primary-container/15 text-primary-container border-primary-container/40 shadow-cyan-subtle'
          : 'bg-surface-container text-on-surface-variant border-outline-variant/30'
      }`}
    >
      <Cpu className={`w-3.5 h-3.5 ${active ? 'text-primary-container animate-pulse' : 'text-outline'}`} />
      <span className="font-semibold">{model}</span>
      {reason && (
        <span className="text-[10px] text-outline border-l border-outline-variant/40 pl-1.5 ml-0.5">
          {reason}
        </span>
      )}
    </div>
  );
};
