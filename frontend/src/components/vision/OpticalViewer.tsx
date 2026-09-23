import React, { useState, useRef } from 'react';
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
  ShieldCheck,
  Upload,
  Image as ImageIcon,
  X
} from 'lucide-react';

export const OpticalViewer: React.FC = () => {
  const [zoom, setZoom] = useState<number>(100);
  const [thermalMode, setThermalMode] = useState<boolean>(false);
  const [edgeMode, setEdgeMode] = useState<boolean>(false);
  const [showReticle, setShowReticle] = useState<boolean>(true);
  const [specimenImage, setSpecimenImage] = useState<string | null>(null);
  const [specimenName, setSpecimenName] = useState<string>('CDU-02 INLET 8" FLANGE');
  const [isDragging, setIsDragging] = useState<boolean>(false);

  const fileInputRef = useRef<HTMLInputElement>(null);

  const handleImageFile = (file: File) => {
    if (file && file.type.startsWith('image/')) {
      const url = URL.createObjectURL(file);
      setSpecimenImage(url);
      setSpecimenName(file.name);
      setZoom(100);
    }
  };

  const handleInputChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (file) {
      handleImageFile(file);
      e.target.value = '';
    }
  };

  const handleDrop = (e: React.DragEvent) => {
    e.preventDefault();
    setIsDragging(false);
    if (e.dataTransfer.files && e.dataTransfer.files.length > 0) {
      handleImageFile(e.dataTransfer.files[0]);
    }
  };

  const resetToStandard = () => {
    if (specimenImage) {
      URL.revokeObjectURL(specimenImage);
    }
    setSpecimenImage(null);
    setSpecimenName('CDU-02 INLET 8" FLANGE');
    setZoom(100);
  };

  return (
    <div className="relative rounded-xl overflow-hidden bg-surface-container-lowest border border-outline-variant/30 shadow-xl flex flex-col">
      <input
        ref={fileInputRef}
        type="file"
        accept="image/*"
        className="hidden"
        onChange={handleInputChange}
      />

      {/* Viewer Main Canvas */}
      <div 
        onDragOver={(e) => { e.preventDefault(); setIsDragging(true); }}
        onDragLeave={() => setIsDragging(false)}
        onDrop={handleDrop}
        className={`relative w-full h-[460px] bg-[#070e17] overflow-hidden flex items-center justify-center select-none transition-all ${
          isDragging ? 'ring-2 ring-primary-container bg-[#0b1726]' : ''
        }`}
      >
        {/* Inspection Canvas */}
        <div 
          className={`w-full h-full relative flex items-center justify-center transition-all duration-300 ${
            thermalMode ? 'hue-rotate-180 contrast-125' : ''
          } ${edgeMode ? 'filter invert contrast-200' : ''}`}
          style={{ transform: `scale(${zoom / 100})` }}
        >
          {/* Background Grid Lines */}
          <div className="absolute inset-0 bg-[linear-gradient(to_right,#152538_1px,transparent_1px),linear-gradient(to_bottom,#152538_1px,transparent_1px)] bg-[size:24px_24px] opacity-40" />

          {specimenImage ? (
            /* Uploaded Specimen View */
            <div className="relative max-w-[85%] max-h-[85%] flex items-center justify-center">
              <img
                src={specimenImage}
                alt="Uploaded specimen"
                className="max-h-[380px] max-w-[540px] rounded-lg shadow-2xl object-contain border border-slate-700"
              />
            </div>
          ) : (
            /* Synthetic Mechanical Flange Inspection Canvas */
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
          )}

          {/* Target Anomaly Reticle & Bounding Box (Gemma 4 E4B Detection) */}
          {showReticle && (
            <div className="absolute left-[38%] top-[34%] w-[24%] h-[28%] z-20 transition-all duration-300 pointer-events-none">
              {/* Corner Brackets */}
              <div className="absolute -top-1 -left-1 w-3.5 h-3.5 border-t-2 border-l-2 border-primary-container" />
              <div className="absolute -top-1 -right-1 w-3.5 h-3.5 border-t-2 border-r-2 border-primary-container" />
              <div className="absolute -bottom-1 -left-1 w-3.5 h-3.5 border-b-2 border-l-2 border-primary-container" />
              <div className="absolute -bottom-1 -right-1 w-3.5 h-3.5 border-b-2 border-r-2 border-primary-container" />

              {/* Box Glow & Pulse */}
              <div className="w-full h-full bg-primary-container/10 border border-primary-container/80 shadow-[0_0_15px_rgba(0,229,255,0.35)] relative flex items-center justify-center">
                <span className="w-2.5 h-2.5 rounded-full bg-error shadow-[0_0_8px_#ffb4ab] animate-pulse" />
              </div>

              {/* Reticle Meta Tag */}
              <div className="absolute -bottom-7 left-0 right-0 flex justify-center">
                <span className="bg-surface-container-lowest/90 px-2 py-0.5 rounded text-[10px] font-mono text-primary-container border border-primary-container/40 whitespace-nowrap shadow-md">
                  ANOMALY #04: SURFACE EROSION (0.92)
                </span>
              </div>
            </div>
          )}
        </div>

        {/* Top-Left Telemetry Overlay */}
        <div className="absolute top-3 left-3 flex flex-col space-y-1 z-30 font-mono text-[10px] bg-surface-container-lowest/85 backdrop-blur-md p-2 rounded-lg border border-outline-variant/30 text-on-surface">
          <div className="flex items-center gap-1.5 text-tertiary">
            <span className="w-2 h-2 rounded-full bg-tertiary animate-pulse" />
            <span className="font-bold">OPTICAL STREAM LIVE</span>
          </div>
          <div className="text-on-surface-variant truncate max-w-[200px]">{specimenName}</div>
          <div className="text-outline">ZOOM: {zoom}% · FPS: 60.0</div>
        </div>

        {/* Top-Right Upload / Reset Specimen Actions */}
        <div className="absolute top-3 right-3 flex items-center gap-2 z-30 font-mono text-xs">
          <button
            type="button"
            onClick={() => fileInputRef.current?.click()}
            className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-surface-container-lowest/90 hover:bg-surface-container backdrop-blur-md border border-outline-variant/40 text-on-surface hover:text-primary-container transition-colors shadow-lg cursor-pointer"
          >
            <Upload className="w-3.5 h-3.5 text-primary-container" />
            <span>Load Image</span>
          </button>
          {specimenImage && (
            <button
              type="button"
              onClick={resetToStandard}
              className="flex items-center gap-1 px-2.5 py-1.5 rounded-lg bg-surface-container-lowest/90 hover:bg-rose-500/20 backdrop-blur-md border border-outline-variant/40 text-on-surface-variant hover:text-rose-400 transition-colors shadow-lg cursor-pointer"
              title="Reset to default synthetic flange"
            >
              <RotateCcw className="w-3.5 h-3.5" />
              <span>Reset</span>
            </button>
          )}
        </div>

        {/* Bottom-Right Sensor Overlay */}
        <div className="absolute bottom-3 right-3 flex items-center gap-2 z-30 font-mono text-[10px] bg-surface-container-lowest/85 backdrop-blur-md px-3 py-1.5 rounded-lg border border-outline-variant/30 text-on-surface">
          <div className="flex items-center gap-1 text-primary-container">
            <Gauge className="w-3.5 h-3.5" />
            <span>EXPOSURE: AUTO</span>
          </div>
          <span className="text-outline">|</span>
          <div className="flex items-center gap-1 text-tertiary">
            <Thermometer className="w-3.5 h-3.5" />
            <span>FLANGE TEMP: 42.1°C</span>
          </div>
        </div>
      </div>

      {/* Control Strip & Calibration Toolbar */}
      <div className="p-3 bg-surface-container-low border-t border-outline-variant/30 flex flex-wrap items-center justify-between gap-3">
        {/* Pan & Zoom Controls */}
        <div className="flex items-center gap-1 bg-surface-container-lowest px-2 py-1 rounded-lg border border-outline-variant/30">
          <button
            type="button"
            onClick={() => setZoom(Math.max(50, zoom - 10))}
            className="p-1.5 rounded hover:bg-surface-container text-on-surface-variant hover:text-on-surface transition-colors cursor-pointer"
            title="Zoom Out"
          >
            <ZoomOut className="w-4 h-4" />
          </button>
          <span className="font-mono text-xs px-2 text-on-surface select-none font-semibold">{zoom}%</span>
          <button
            type="button"
            onClick={() => setZoom(Math.min(200, zoom + 10))}
            className="p-1.5 rounded hover:bg-surface-container text-on-surface-variant hover:text-on-surface transition-colors cursor-pointer"
            title="Zoom In"
          >
            <ZoomIn className="w-4 h-4" />
          </button>
          <button
            type="button"
            onClick={() => setZoom(100)}
            className="p-1.5 rounded hover:bg-surface-container text-on-surface-variant hover:text-on-surface transition-colors cursor-pointer"
            title="Reset Pan"
          >
            <RotateCcw className="w-4 h-4" />
          </button>
        </div>

        <div className="flex items-center gap-2 flex-wrap font-mono text-xs">
          {/* Thermal Toggle */}
          <button
            type="button"
            onClick={() => setThermalMode(!thermalMode)}
            className={`px-2.5 py-1 rounded border transition-colors flex items-center gap-1.5 cursor-pointer ${
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
            type="button"
            onClick={() => setEdgeMode(!edgeMode)}
            className={`px-2.5 py-1 rounded border transition-colors flex items-center gap-1.5 cursor-pointer ${
              edgeMode
                ? 'bg-tertiary/20 text-tertiary border-tertiary/50'
                : 'bg-surface-container hover:bg-surface-container-high text-on-surface border-outline-variant/30'
            }`}
          >
            <Layers className="w-3.5 h-3.5 text-tertiary" />
            <span>Edge Detect</span>
          </button>

          {/* Bounding Box Switch */}
          <button
            type="button"
            onClick={() => setShowReticle(!showReticle)}
            className={`px-2.5 py-1 rounded border transition-colors flex items-center gap-1.5 cursor-pointer ${
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
