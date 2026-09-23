import React from 'react';
import { Clearance } from '../../types/auth';

interface ClearanceChipProps {
  clearance: Clearance;
  size?: 'sm' | 'md';
}

export const ClearanceChip: React.FC<ClearanceChipProps> = ({ clearance, size = 'sm' }) => {
  const styles: Record<Clearance, string> = {
    PUBLIC: 'bg-slate-500/10 text-slate-400 border-slate-500/20',
    INTERNAL: 'bg-indigo-500/10 text-indigo-400 border-indigo-500/30',
    CONFIDENTIAL: 'bg-amber-500/10 text-amber-400 border-amber-500/30',
    RESTRICTED: 'bg-rose-500/15 text-rose-400 border-rose-500/40 shadow-[0_0_8px_rgba(239,68,68,0.2)]',
  };

  const sizeClass = size === 'sm' 
    ? 'text-[10px] px-1.5 py-0.5' 
    : 'text-xs px-2.5 py-1';

  return (
    <span
      className={`inline-flex items-center uppercase font-mono tracking-wider font-semibold rounded border ${sizeClass} ${styles[clearance] || styles.PUBLIC}`}
    >
      {clearance}
    </span>
  );
};
