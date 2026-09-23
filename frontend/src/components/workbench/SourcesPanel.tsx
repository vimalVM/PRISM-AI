import React from 'react';
import { FileText, Lock } from 'lucide-react';

export const SourcesPanel: React.FC = () => {
  const sources = [
    {
      filename: 'CDU_Operating_SOP.pdf',
      match: '94%',
      page: 'Page 43',
      classification: 'CONFIDENTIAL',
      snippet: 'Section 4.3: Flange joint tolerances under high sulfidic crude flow require biannual wall thickness verification...',
    },
    {
      filename: 'Valve_Maint_Manual.pdf',
      match: '89%',
      page: 'Page 18',
      classification: 'CONFIDENTIAL',
      snippet: 'Gasket replacement schedule for class 300 raised face flanges under high cyclic thermal variations...',
    },
    {
      filename: 'Inspection_Log_Sept.pdf',
      match: '82%',
      page: 'Page 7',
      classification: 'CONFIDENTIAL',
      snippet: 'UT survey recorded minimum thickness 6.2mm vs nominal 8.0mm on sector 3 with severe pitting.',
    },
  ];

  return (
    <div className="rounded-xl bg-surface-container-lowest p-4 shadow-sm border border-outline-variant/30">
      <div className="flex items-center justify-between pb-3 mb-3 border-b border-outline-variant/20">
        <div className="flex items-center gap-2">
          <FileText className="w-4 h-4 text-tertiary" />
          <span className="font-mono text-xs uppercase font-bold text-on-surface">
            SOURCES & CITATIONS
          </span>
        </div>
        <span className="font-mono text-[10px] px-2 py-0.5 rounded bg-surface-container text-tertiary-fixed-dim border border-outline-variant/20">
          3 REFS MATCHED
        </span>
      </div>

      <div className="space-y-3">
        {sources.map((src, i) => (
          <div
            key={i}
            className="p-3 rounded-lg bg-surface-container hover:bg-surface-container-high transition-colors group cursor-pointer border border-outline-variant/20"
          >
            <div className="flex items-center justify-between mb-1">
              <div className="flex items-center gap-1.5 min-w-0">
                <FileText className="w-3.5 h-3.5 text-rose-400 shrink-0" />
                <span className="font-headline text-xs font-semibold text-on-surface truncate group-hover:text-primary transition-colors">
                  {src.filename}
                </span>
              </div>
              <span className="font-mono text-[10px] text-tertiary font-bold">{src.match} MATCH</span>
            </div>
            <div className="flex items-center gap-2 font-mono text-[10px] text-outline mb-1.5">
              <span>{src.page}</span>
              <span>·</span>
              <span className="text-amber-400 font-bold">{src.classification}</span>
            </div>
            <p className="text-xs text-on-surface-variant line-clamp-2 leading-snug">
              "{src.snippet}"
            </p>
          </div>
        ))}

        {/* Restricted Block Filter Warning (Server-side clearance enforcement SEC-04) */}
        <div className="p-3 rounded-lg bg-surface-container-low border border-rose-500/30 flex items-start gap-2 text-rose-400">
          <Lock className="w-4 h-4 shrink-0 mt-0.5" />
          <div className="flex flex-col font-mono text-[10px]">
            <span className="font-bold tracking-wider uppercase">1 Restricted Chunk Masked</span>
            <span className="text-on-surface-variant leading-tight mt-0.5">
              Exceeds Operator Clearance L2. Requires Lead Cryptographer L3 validation to inspect raw text.
            </span>
          </div>
        </div>
      </div>
    </div>
  );
};
