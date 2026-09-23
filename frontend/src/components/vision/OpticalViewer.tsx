import React, { useState } from 'react';
import { 
  ZoomIn, 
  ZoomOut, 
  RotateCcw, 
  Flame, 
  Layers, 
  Ruler, 
  Crop, 
  Thermometer, 
  Gauge, 
  Video, 
  ShieldCheck 
} from 'lucide-react';

export const OpticalViewer: React.FC = () => {
  const [zoom, setZoom] = useState<number>(100);
  const [thermalMode, setThermalMode] = useState<boolean>(false);
  const [edgeMode, setEdgeMode] = useState<boolean>(false);
  const [showReticle, setShowReticle] = useState<boolean>(true);

  return (
    <div className="relative rounded-xl overflow-hidden bg-surface-container-lowest border border-outline-variant/30 shadow-xl flex flex-col">
      {/* Viewer Main Canvas */}
      <div className="relative w-full h-[460px] bg-[#070e17] overflow-hidden flex items-center justify-center select-none">
        {/* Synthetic Mechanical Flange Inspection Canvas */}
        <div 
          className={`w-full h-full relative flex items-center justify-center transition-all duration-300 ${
            thermalMode ? 'hue-rotate-180 contrast-125' : ''
          } ${edgeMode ? 'filter invert contrast-200' : ''}`}
          style={{ transform: `scale(${zoom / 100})` }}
        >
          {/* Background Grid Lines */}
          <div className="absolute inset-0 bg-[linear-gradient(to_right,#152538_1px,transparent_1px),linear-gradient(to_bottom,#152538_1px,transparent_1px)] bg-[size:24px_24px] opacity-40" />

          {/* Central Flange Silhouette Graphic */}
          <div className="relative w-[340px] h-[340px] rounded-full border-4 border-slate-700 bg-slate-900/90 shadow-2xl flex items-center justify-center">
            {/* Flange Bolt Ring */}
            <div className="absolute inset-4 rounded-full border border-dashed border-slate-600 flex items-center justify-center">
              {[0, 45, 90, 135, 180, 225, 270, 315].map((deg) => (
                <div
                  key={deg}
                  className="absolute w-4 h-4 rounded-full bg-slate-600 border border-slate-400"
                  style={{
                    transform: `rotate(${deg}deg) translate(130px) rotate(-${deg}deg)`,
                  }}
                />
              ))}
            </div>

            {/* Inner Bore */}
            <div className="w-40 h-40 rounded-full border-4 border-slate-600 bg-slate-950 flex items-center justify-center">
              <span className="font-mono text-[10px] text-slate-500">CDU-02 INLET 8"</span>
            </div>
          </div>

          {/* Target Anomaly Reticle & Bounding Box (Gemma 4 E4B Detection) */}
          {showReticle && (
            <div className="absolute left-[38%] top-[34%] w-[24%] h-[28%] z-20 transition-all duration-300">
              {/* Corner Brackets */}
              <div className="absolute -top-1 -left-1 w-3.5 h-3.5 border-t-2 border-l-2 border-primary-container" />
              <div className="absolute -top-1 -right-1 w-3.5 h-3.5 border-t-2 border-r-2 border-primary-container" />
              <div className="absolute -bottom-1 -left-1 w-3.5 h-3.5 border-b-2 border-l-2 border-primary-container" />
              <div className="absolute -bottom-1 -right-1 w-3.5 h-3.5 border-b-2 border-r-2 border-primary-container" />

              {/* Box Glow & Pulse */}
              <div className="w-full h-full bg-primary-container/10 border border-primary-container/80 shadow-[0_0_15px_rgba(0,229,255,0.35)] relative flex items-center justify-center">
                <span className="w-2.5 h-2.5 rounded-full bg-error shadow-[0_0_8px_#ffb4ab] animate-pulse" />
              </div>

              {/* Floated Tag Callout */}
              <div className="absolute -top-16 left-0 whitespace-nowrap bg-surface-container-high/95 backdrop-blur-md px-3 py-1.5 rounded-lg shadow-xl flex flex-col gap-0.5 border border-outline-variant/40 z-30 pointer-events-auto">
                <div className="flex items-center gap-1.5">
                  <span className="w-2 h-2 rounded-full bg-error" />
                  <span className="font-mono text-xs text-error font-bold tracking-wide">
                    ANOMALY: Surface Corrosion & Flange Pitting
                  </span>
                </div>
                <div className="flex items-center gap-2 text-on-surface-variant font-mono text-[10px]">
                  <span className="text-tertiary-fixed font-bold">91.4% CONFIDENCE (Gemma 4 E4B)</span>
                  <span>•</span>
                  <span>[X:230 Y:235 W:110 H:70]</span>
                </div>
              </div>
            </div>
          )}
        </div>

        {/* Telemetry HUD Ribbon inside Canvas */}
        <div className="absolute bottom-3 left-3 right-3 bg-surface-container-lowest/85 backdrop-blur-md rounded-lg p-2.5 flex items-center justify-between text-on-surface font-mono text-xs z-20 border border-outline-variant/30 shadow-md">
          <div className="flex items-center gap-4">
            <span className="flex items-center gap-1.5 text-primary-container">
              <Thermometer className="w-3.5 h-3.5" />
              Temp: <strong className="text-on-surface">+184.2°C</strong>
            </span>
            <span className="text-outline-variant">/</span>
            <span className="flex items-center gap-1.5 text-tertiary">
              <Gauge className="w-3.5 h-3.5" />
              Pressure: <strong className="text-on-surface">42.1 BAR</strong>
            </span>
            <span className="hidden md:inline text-outline-variant">/</span>
            <span className="hidden md:flex items-center gap-1.5 text-on-surface-variant">
              <Video className="w-3.5 h-3.5" />
              Sensor ID: <strong className="text-on-surface">FLIR-CAM-A04</strong>
            </span>
          </div>
          <div className="flex items-center gap-2">
            <span className="px-2 py-0.5 rounded bg-tertiary/15 text-tertiary font-medium flex items-center gap-1">
              <ShieldCheck className="w-3.5 h-3.5" />
              Air-Gap Verified
            </span>
          </div>
        </div>
      </div>

      {/* Viewer Diagnostic Toolbar */}
      <div className="bg-surface-container-low px-4 py-2.5 flex items-center justify-between flex-wrap gap-2 text-on-surface border-t border-outline-variant/30">
        <div className="flex items-center gap-1">
          <button
            onClick={() => setZoom(Math.max(50, zoom - 10))}
            className="p-1.5 rounded hover:bg-surface-container text-on-surface-variant hover:text-on-surface transition-colors"
            title="Zoom Out"
          >
            <ZoomOut className="w-4 h-4" />
          </button>
          <span className="font-mono text-xs px-2 text-on-surface select-none font-semibold">{zoom}%</span>
          <button
            onClick={() => setZoom(Math.min(200, zoom + 10))}
            className="p-1.5 rounded hover:bg-surface-container text-on-surface-variant hover:text-on-surface transition-colors"
            title="Zoom In"
          >
            <ZoomIn className="w-4 h-4" />
          </button>
          <button
            onClick={() => setZoom(100)}
            className="p-1.5 rounded hover:bg-surface-container text-on-surface-variant hover:text-on-surface transition-colors"
            title="Reset Pan"
          >
            <RotateCcw className="w-4 h-4" />
          </button>
        </div>

        <div className="flex items-center gap-2 flex-wrap font-mono text-xs">
          {/* Thermal Toggle */}
          <button
            onClick={() => setThermalMode(!thermalMode)}
            className={`px-2.5 py-1 rounded border transition-colors flex items-center gap-1.5 ${
              thermalMode
                ? 'bg-amber-500/20 text-amber-300 border-amber-500/50'
                : 'bg-surface-container hover:bg-surface-container-high text-on-surface border-outline-variant/30'
            }`}
          >
            <Flame className="w-3.5 h-3.5 text-error" />
            <span>Thermal: <strong>{thermalMode ? 'IRONBOW' : 'OFF'}</strong></span>
          </button>

          {/* Edge Detection Mode */}
          <button
            onClick={() => setEdgeMode(!edgeMode)}
            className={`px-2.5 py-1 rounded border transition-colors flex items-center gap-1.5 ${
              edgeMode
                ? 'bg-tertiary/20 text-tertiary border-tertiary/50'
                : 'bg-surface-container hover:bg-surface-container-high text-on-surface border-outline-variant/30'
            }`}
          >
            <Layers className="w-3.5 h-3.5 text-tertiary" />
            <span>Edge Detect</span>
          </button>

          {/* Caliper */}
          <button className="px-2.5 py-1 rounded bg-surface-container hover:bg-surface-container-high text-on-surface border border-outline-variant/30 flex items-center gap-1.5 transition-colors">
            <Ruler className="w-3.5 h-3.5 text-secondary" />
            <span>Caliper (mm)</span>
          </button>

          {/* Bounding Box Switch */}
          <button
            onClick={() => setShowReticle(!showReticle)}
            className={`px-2.5 py-1 rounded border transition-colors flex items-center gap-1.5 ${
              showReticle
                ? 'bg-primary-container/20 text-primary-container border-primary-container/50'
                : 'bg-surface-container text-outline border-outline-variant/30'
            }`}
          >
            <Crop className="w-3.5 h-3.5" />
            <span>Bounding Box: {showReticle ? 'ON' : 'OFF'}</span>
          </button>
        </div>
      </div>
    </div>
  );
};
