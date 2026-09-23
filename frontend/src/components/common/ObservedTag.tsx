import React from 'react';
import { Eye, HelpCircle } from 'lucide-react';

interface ObservedTagProps {
  type: 'observed' | 'inferred';
  limitation?: string;
}

export const ObservedTag: React.FC<ObservedTagProps> = ({ type, limitation }) => {
  const isObserved = type === 'observed';

  return (
    <div className="inline-flex items-center gap-1.5 group relative">
      <span
        className={`inline-flex items-center gap-1 px-2 py-0.5 rounded text-[10px] font-mono uppercase tracking-wider font-semibold border ${
          isObserved
            ? 'bg-emerald-500/10 text-tertiary-fixed border-emerald-500/30'
            : 'bg-amber-500/10 text-amber-400 border-amber-500/30'
        }`}
      >
        <Eye className="w-3 h-3" />
        {type}
      </span>
      {limitation && (
        <span
          className="text-outline hover:text-on-surface cursor-help"
          title={limitation}
        >
          <HelpCircle className="w-3 h-3" />
        </span>
      )}
    </div>
  );
};
