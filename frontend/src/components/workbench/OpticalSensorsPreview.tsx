import React from 'react';
import { Camera, Radio, ZoomIn } from 'lucide-react';
import { useNavigate } from 'react-router-dom';

export const OpticalSensorsPreview: React.FC = () => {
  const navigate = useNavigate();

  return (
    <div className="rounded-xl bg-surface-container-lowest p-4 shadow-sm border border-outline-variant/30">
      <div className="flex items-center justify-between mb-3 pb-2 border-b border-outline-variant/20">
        <div className="flex items-center gap-2">
          <Camera className="w-4 h-4 text-secondary-fixed" />
          <span className="font-mono text-xs uppercase font-bold text-on-surface">
            Inspection Sensor Imagery
          </span>
        </div>
        <span className="font-mono text-[10px] text-outline">
          STATION: FLG-CDU-02-B · HIGH-RES OPTICAL / NDT
        </span>
      </div>

      <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
        {/* Sensor 1: NDT Ultrasonic Matrix */}
        <div 
          onClick={() => navigate('/vision')}
          className="relative rounded-lg overflow-hidden h-44 bg-surface-container border border-outline-variant/30 group cursor-pointer"
        >
          {/* Simulated Ultrasonic Matrix Canvas Graphic */}
          <div className="w-full h-full bg-[#0a121d] flex items-center justify-center relative overflow-hidden">
            {/* Grid Lines */}
            <div className="absolute inset-0 bg-[linear-gradient(to_right,#162436_1px,transparent_1px),linear-gradient(to_bottom,#162436_1px,transparent_1px)] bg-[size:16px_16px] opacity-40" />
            
            {/* Ultrasound Beam Sweep & Heatmap Anomaly */}
            <div className="w-32 h-32 rounded-full border border-cyan-500/30 flex items-center justify-center relative">
              <div className="w-24 h-24 rounded-full border border-cyan-400/50 flex items-center justify-center animate-pulse" />
              <div className="w-16 h-16 rounded-full bg-rose-500/20 border border-rose-500/80 shadow-[0_0_20px_rgba(239,68,68,0.5)] flex items-center justify-center">
                <span className="w-2 h-2 rounded-full bg-rose-500 animate-ping" />
              </div>
            </div>

            {/* Reticle Callout */}
            <div className="absolute top-3 left-3 bg-surface-container-lowest/80 backdrop-blur px-2 py-0.5 rounded text-[10px] font-mono text-primary-container border border-primary-container/30">
              SECTOR 6 o'clock: PITTING
            </div>
            
            <div className="absolute bottom-2 left-2 right-2 flex items-center justify-between font-mono text-[10px] z-10">
              <span className="bg-surface-container-lowest/90 backdrop-blur px-2 py-0.5 rounded text-tertiary border border-outline-variant/20">
                NDT ULTRASONIC MATRIX
              </span>
              <span className="text-on-surface-variant bg-surface-container-lowest/80 px-1.5 py-0.5 rounded">
                FREQ 5.0 MHz
              </span>
            </div>
          </div>
        </div>

        {/* Sensor 2: Optical Rig A-4 */}
        <div 
          onClick={() => navigate('/vision')}
          className="relative rounded-lg overflow-hidden h-44 bg-surface-container border border-outline-variant/30 group cursor-pointer"
        >
          {/* Simulated High-Res Pipe Joint & Bolt Assembly Graphic */}
          <div className="w-full h-full bg-[#0d1622] flex items-center justify-center relative overflow-hidden">
            {/* Mechanical Pipeline Geometry */}
            <div className="w-48 h-28 border-2 border-slate-700 rounded-sm relative flex items-center justify-center">
              <div className="w-full h-8 bg-slate-800/80 border-y border-slate-600 flex justify-around items-center px-4">
                <div className="w-3 h-3 rounded-full bg-slate-500 border border-slate-400" />
                <div className="w-3 h-3 rounded-full bg-slate-500 border border-slate-400" />
                <div className="w-3 h-3 rounded-full bg-amber-500/80 border border-amber-400 shadow-[0_0_8px_rgba(245,158,11,0.5)]" />
                <div className="w-3 h-3 rounded-full bg-slate-500 border border-slate-400" />
              </div>
              <div className="absolute right-6 top-3 text-[9px] font-mono text-amber-400 bg-surface-container-lowest/90 px-1.5 py-0.5 rounded border border-amber-500/40">
                FLG-BOLT-03 CORROSION
              </div>
            </div>

            <div className="absolute bottom-2 left-2 right-2 flex items-center justify-between font-mono text-[10px] z-10">
              <span className="bg-surface-container-lowest/90 backdrop-blur px-2 py-0.5 rounded text-primary border border-outline-variant/20">
                OPTICAL RIG A-4
              </span>
              <span className="text-on-surface-variant bg-surface-container-lowest/80 px-1.5 py-0.5 rounded">
                24.1 MP RAW
              </span>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};
