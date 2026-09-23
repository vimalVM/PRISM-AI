import React from 'react';
import { Network, CheckCircle, Brain, ArrowRight, Zap, Check } from 'lucide-react';

interface NeuralRouterStreamProps {
  activeModel?: string;
  taskClassification?: string;
}

export const NeuralRouterStream: React.FC<NeuralRouterStreamProps> = ({
  activeModel = 'qwen3.5:4b',
  taskClassification = 'Flange Stress & Corrosion Analysis',
}) => {
  const isQwenActive = activeModel.includes('qwen') || activeModel.includes('primary');
  const isGemmaActive = activeModel.includes('gemma') || activeModel.includes('vision');

  return (
    <div className="rounded-xl bg-surface-container-lowest p-4 shadow-sm border border-outline-variant/30">
      {/* Pipeline Flow Indicator */}
      <div className="flex flex-col lg:flex-row lg:items-center justify-between pb-3 gap-2 mb-3 border-b border-outline-variant/20">
        <div className="flex items-center gap-2">
          <Network className="w-4 h-4 text-primary-container" />
          <span className="font-mono text-xs tracking-wider text-on-surface font-bold uppercase">
            Dynamic Neural Routing Stream
          </span>
        </div>
        <div className="flex items-center gap-2">
          <span className="w-2 h-2 rounded-full bg-tertiary shadow-[0_0_6px_#a8ffd2]" />
          <span className="font-mono text-[10px] text-tertiary font-semibold uppercase tracking-wider">
            Zero Egress Confirmed · RTX Enclave
          </span>
        </div>
      </div>

      {/* Pipeline Breadcrumb Steps */}
      <div className="bg-surface-container-low px-4 py-2.5 rounded-lg flex flex-wrap items-center gap-3 font-mono text-xs mb-4 border border-outline-variant/20">
        <div className="flex items-center gap-1.5 text-on-surface-variant">
          <CheckCircle className="w-3.5 h-3.5 text-tertiary" />
          <span>Query Analysis</span>
        </div>
        <ArrowRight className="w-3.5 h-3.5 text-outline" />
        <div className="flex items-center gap-1.5 text-primary-container bg-surface-container px-2 py-0.5 rounded border border-primary-container/20">
          <Brain className="w-3.5 h-3.5" />
          <span>Task Classification: {taskClassification}</span>
        </div>
        <ArrowRight className="w-3.5 h-3.5 text-outline" />
        <div className="flex items-center gap-1.5 text-tertiary-fixed font-semibold">
          <span className="w-1.5 h-1.5 rounded-full bg-tertiary animate-pulse" />
          <span>Active: {isGemmaActive ? 'Gemma 4 E4B (Vision)' : 'Qwen 3.5 4B (Reasoning)'}</span>
        </div>
      </div>

      {/* 4 Model Hardware Tiles */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-3">
        {/* Model 1: Qwen 3.5 4B */}
        <div
          className={`p-3 rounded-lg bg-surface-container relative overflow-hidden border transition-all ${
            isQwenActive
              ? 'border-primary-container/60 shadow-cyan-subtle'
              : 'border-outline-variant/30 hover:border-outline-variant/60'
          }`}
        >
          {isQwenActive && <div className="absolute top-0 left-0 right-0 h-0.5 bg-primary-container" />}
          <div className="flex items-center justify-between font-mono text-[10px] text-outline mb-1">
            <span>REASONING / DOCS</span>
            <span className={isQwenActive ? 'text-primary-container font-semibold' : 'text-outline'}>
              {isQwenActive ? 'ACTIVE' : 'STANDBY'}
            </span>
          </div>
          <div className="font-headline text-sm font-semibold text-on-surface mb-1">Qwen 3.5 4B</div>
          <div className="flex items-center justify-between font-mono text-[10px]">
            <span className={isQwenActive ? 'text-tertiary' : 'text-outline'}>
              {isQwenActive ? 'RUNNING' : 'CACHED'}
            </span>
            <span className="text-on-surface-variant font-mono">3.4 GB VRAM</span>
          </div>
        </div>

        {/* Model 2: Gemma 4 E4B */}
        <div
          className={`p-3 rounded-lg bg-surface-container relative overflow-hidden border transition-all ${
            isGemmaActive
              ? 'border-primary-container/60 shadow-cyan-subtle'
              : 'border-outline-variant/30 hover:border-outline-variant/60'
          }`}
        >
          {isGemmaActive && <div className="absolute top-0 left-0 right-0 h-0.5 bg-primary-container" />}
          <div className="flex items-center justify-between font-mono text-[10px] text-outline mb-1">
            <span>VISION / INSPECT</span>
            <span className={isGemmaActive ? 'text-primary-container font-semibold' : 'text-outline'}>
              {isGemmaActive ? 'ACTIVE' : 'READY'}
            </span>
          </div>
          <div className="font-headline text-sm font-semibold text-on-surface mb-1">Gemma 4 E4B</div>
          <div className="flex items-center justify-between font-mono text-[10px]">
            <span className={isGemmaActive ? 'text-tertiary' : 'text-outline'}>
              {isGemmaActive ? 'RUNNING' : 'STANDBY'}
            </span>
            <span className="text-on-surface-variant font-mono">2.1 GB VRAM</span>
          </div>
        </div>

        {/* Model 3: PaddleOCR v4 */}
        <div className="p-3 rounded-lg bg-surface-container border border-outline-variant/30 hover:border-outline-variant/60 transition-colors">
          <div className="flex items-center justify-between font-mono text-[10px] text-outline mb-1">
            <span>OCR ENGINE</span>
            <span className="text-tertiary">CACHED</span>
          </div>
          <div className="font-headline text-sm font-semibold text-on-surface mb-1">PaddleOCR v4</div>
          <div className="flex items-center justify-between font-mono text-[10px]">
            <span className="text-outline">CPU READY</span>
            <span className="text-on-surface-variant font-mono">0.4 GB RAM</span>
          </div>
        </div>

        {/* Model 4: Qwen3 Embed */}
        <div className="p-3 rounded-lg bg-surface-container border border-outline-variant/30 hover:border-outline-variant/60 transition-colors">
          <div className="flex items-center justify-between font-mono text-[10px] text-outline mb-1">
            <span>EMBEDDING / SEARCH</span>
            <span className="text-secondary-fixed">PERSIST</span>
          </div>
          <div className="font-headline text-sm font-semibold text-on-surface mb-1">Qwen3 Embed</div>
          <div className="flex items-center justify-between font-mono text-[10px]">
            <span className="text-secondary-fixed">INDEXED</span>
            <span className="text-on-surface-variant font-mono">0.8 GB VRAM</span>
          </div>
        </div>
      </div>
    </div>
  );
};
