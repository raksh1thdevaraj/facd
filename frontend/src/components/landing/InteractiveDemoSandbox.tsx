import React, { useState, useRef } from 'react';
import {
  SlidersHorizontal,
  Crosshair,
  Sparkles,
  Info,
  FileCheck2,
} from 'lucide-react';

interface Hotspot {
  id: string;
  x: number; // percentage
  y: number; // percentage
  title: string;
  category: string;
  confidence: string;
  detail: string;
  evidence: string;
}

const HOTSPOTS: Hotspot[] = [
  {
    id: 'gpa',
    x: 68,
    y: 53,
    title: 'Forged GPA Digits (3.98)',
    category: 'Font Kerning & Splicing',
    confidence: '99.4% Forged',
    detail: 'Altered from original 2.85. Baseline offset of 4.2px detected with inconsistent glyph antialiasing.',
    evidence: 'High DCT Quantization Divergence (ELA +18.4dB)',
  },
  {
    id: 'seal',
    x: 50,
    y: 19,
    title: 'Cloned University Seal',
    category: 'Copy-Move Duplication',
    confidence: '98.7% Cloned',
    detail: 'Embossed crest lifted from another alumni certificate. Keypoint cluster density matches external template source.',
    evidence: 'SIFT Keypoint Duplicate Cluster (48 pairs)',
  },
  {
    id: 'date',
    x: 78,
    y: 84,
    title: 'Conferral Date Modification',
    category: 'Layer Re-compression',
    confidence: '95.2% Suspicious',
    detail: 'Modified from 2021 to 2024. JPEG block boundary artifact detected in 8x8 DCT grid.',
    evidence: 'Quantization Matrix Inconsistency',
  },
];

export const InteractiveDemoSandbox: React.FC = () => {
  const [sliderPosition, setSliderPosition] = useState<number>(50); // 0 to 100%
  const [activeHotspot, setActiveHotspot] = useState<Hotspot | null>(HOTSPOTS[0]);
  const [isDragging, setIsDragging] = useState<boolean>(false);
  const containerRef = useRef<HTMLDivElement>(null);

  const handleMove = (clientX: number) => {
    if (!containerRef.current) return;
    const rect = containerRef.current.getBoundingClientRect();
    const x = clientX - rect.left;
    const percentage = Math.max(0, Math.min(100, (x / rect.width) * 100));
    setSliderPosition(percentage);
  };

  const handleMouseMove = (e: React.MouseEvent) => {
    if (isDragging) {
      handleMove(e.clientX);
    }
  };

  const handleTouchMove = (e: React.TouchEvent) => {
    if (e.touches.length > 0) {
      handleMove(e.touches[0].clientX);
    }
  };

  return (
    <section id="demo-sandbox" className="space-y-8 py-8">
      {/* Header */}
      <div className="text-center space-y-3 max-w-3xl mx-auto">
        <div className="inline-flex items-center space-x-2 px-3.5 py-1.5 rounded-full bg-emerald-950/60 border border-emerald-500/30 text-emerald-300 text-xs font-mono font-medium">
          <Crosshair className="w-3.5 h-3.5 text-emerald-400" />
          <span>INTERACTIVE FORENSIC SANDBOX & ELA VIEWER</span>
        </div>

        <h2 className="text-3xl sm:text-4xl font-extrabold text-white tracking-tight">
          Inspect Tampering with the Split-Slider
        </h2>

        <p className="text-sm text-slate-400 leading-relaxed">
          Drag the forensic reveal slider to expose Error Level Analysis (ELA) heatmaps and hover over flagged suspicious anomalies to review explainable attribution dossiers.
        </p>
      </div>

      {/* Main Sandbox Grid */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-8 items-start max-w-6xl mx-auto">
        {/* Left: Interactive Split-Slider Viewer (8 cols) */}
        <div className="lg:col-span-8 space-y-4">
          <div
            ref={containerRef}
            onMouseDown={() => setIsDragging(true)}
            onMouseUp={() => setIsDragging(false)}
            onMouseLeave={() => setIsDragging(false)}
            onMouseMove={handleMouseMove}
            onTouchStart={() => setIsDragging(true)}
            onTouchEnd={() => setIsDragging(false)}
            onTouchMove={handleTouchMove}
            className="relative w-full aspect-[4/3] sm:aspect-[16/11] rounded-3xl overflow-hidden border border-slate-700/80 select-none cursor-ew-resize shadow-2xl bg-slate-950"
          >
            {/* --- BASE LAYER: FORENSIC HEATMAP (Right / Underneath) --- */}
            <div className="absolute inset-0 bg-[#090d16] p-6 flex flex-col justify-between">
              {/* Simulated ELA & Heatmap Graphics */}
              <div className="absolute inset-0 opacity-90 pointer-events-none">
                {/* Background Noise Texture */}
                <div className="w-full h-full bg-[radial-gradient(#1e293b_1px,transparent_1px)] [background-size:16px_16px] opacity-40" />

                {/* Hotspot 1 Heatmap Glow (GPA) */}
                <div
                  className="absolute w-36 h-20 rounded-full bg-gradient-to-r from-rose-600 via-fuchsia-600 to-amber-500 blur-xl opacity-80 animate-pulse"
                  style={{ left: '60%', top: '48%' }}
                />

                {/* Hotspot 2 Heatmap Glow (Seal) */}
                <div
                  className="absolute w-32 h-32 rounded-full bg-gradient-to-r from-rose-500 via-orange-600 to-yellow-500 blur-xl opacity-75 animate-pulse"
                  style={{ left: '42%', top: '12%' }}
                />

                {/* Hotspot 3 Heatmap Glow (Date) */}
                <div
                  className="absolute w-28 h-16 rounded-full bg-gradient-to-r from-pink-600 to-purple-600 blur-lg opacity-70"
                  style={{ left: '72%', top: '80%' }}
                />
              </div>

              {/* Heatmap Overlay Content */}
              <div className="relative z-10 flex items-center justify-between">
                <span className="text-xs font-mono font-bold text-fuchsia-400 bg-fuchsia-950/80 px-2.5 py-1 rounded-md border border-fuchsia-500/30">
                  HEATMAP REVEAL • ERROR LEVEL ANALYSIS (ELA)
                </span>
                <span className="text-[11px] font-mono text-slate-400 bg-slate-900/80 px-2 py-0.5 rounded">
                  ΔE &gt; 24.5 (CRITICAL)
                </span>
              </div>

              <div className="relative z-10 flex items-end justify-between text-xs text-slate-400 font-mono">
                <span>DCT Quantization Anomaly High</span>
                <span className="text-rose-400 font-bold">MANIPULATION DETECTED</span>
              </div>
            </div>

            {/* --- TOP LAYER: TAMPERED DOCUMENT (Left / Clipped) --- */}
            <div
              className="absolute inset-0 bg-[#0f172a] p-6 flex flex-col justify-between border-r border-emerald-400/80 shadow-2xl transition-none"
              style={{ clipPath: `inset(0 ${100 - sliderPosition}% 0 0)` }}
            >
              {/* Certificate Details */}
              <div className="border border-emerald-500/30 rounded-2xl p-6 h-full flex flex-col justify-between bg-gradient-to-b from-slate-900/90 to-slate-950/90 relative">
                {/* Header / Seal */}
                <div className="text-center space-y-2">
                  <div className="w-14 h-14 rounded-full border-2 border-emerald-400/80 bg-emerald-950/40 mx-auto flex items-center justify-center">
                    <Sparkles className="w-6 h-6 text-emerald-400" />
                  </div>
                  <h4 className="text-sm font-bold text-slate-100 tracking-wider">
                    OXFORD METROPOLITAN UNIVERSITY
                  </h4>
                  <p className="text-[10px] text-slate-400 uppercase tracking-widest font-mono">
                    Department of Computing & Cybernetics
                  </p>
                </div>

                {/* Candidate & Honors */}
                <div className="text-center space-y-2 my-auto">
                  <p className="text-xs text-slate-400 italic">This is to officially certify that</p>
                  <h3 className="text-lg sm:text-xl font-bold text-white tracking-tight">
                    JAMES ROBERT STERLING
                  </h3>
                  <p className="text-xs text-slate-300 max-w-sm mx-auto">
                    has been conferred the degree of Bachelor of Science in Information Systems with
                    Honors.
                  </p>
                  <div className="inline-block px-3 py-1 rounded-full bg-emerald-950/50 border border-emerald-500/30 text-emerald-300 font-mono text-xs font-bold">
                    CUMULATIVE GPA: 3.98
                  </div>
                </div>

                {/* Footer / Signatures */}
                <div className="flex items-center justify-between text-[11px] text-slate-400 border-t border-slate-800 pt-3">
                  <div>
                    <span className="block font-serif italic text-slate-300">Dr. A. Vance</span>
                    <span className="font-mono text-[9px] text-slate-500">Academic Registrar</span>
                  </div>
                  <div className="text-right">
                    <span className="block font-mono text-slate-300">Conferred: June 14, 2024</span>
                    <span className="font-mono text-[9px] text-slate-500">ID: OMU-984210</span>
                  </div>
                </div>
              </div>
            </div>

            {/* --- SLIDER DIVIDER LINE & HANDLE --- */}
            <div
              className="absolute top-0 bottom-0 w-1 bg-gradient-to-b from-cyan-400 via-emerald-400 to-teal-400 cursor-ew-resize pointer-events-none z-30"
              style={{ left: `${sliderPosition}%` }}
            >
              <div className="absolute top-1/2 -translate-y-1/2 -translate-x-1/2 w-8 h-8 rounded-full bg-slate-900 border-2 border-emerald-400 flex items-center justify-center shadow-lg shadow-emerald-500/50">
                <SlidersHorizontal className="w-3.5 h-3.5 text-emerald-400" />
              </div>
            </div>

            {/* --- INTERACTIVE HOTSPOTS --- */}
            {HOTSPOTS.map((spot) => {
              const isSelected = activeHotspot?.id === spot.id;
              return (
                <button
                  key={spot.id}
                  onClick={(e) => {
                    e.stopPropagation();
                    setActiveHotspot(spot);
                  }}
                  onMouseEnter={() => setActiveHotspot(spot)}
                  className={`absolute z-40 -translate-x-1/2 -translate-y-1/2 p-2 rounded-full transition-all group ${
                    isSelected
                      ? 'ring-4 ring-rose-500/50 scale-125'
                      : 'hover:scale-110'
                  }`}
                  style={{ left: `${spot.x}%`, top: `${spot.y}%` }}
                  title={spot.title}
                >
                  <span className="relative flex h-5 w-5">
                    <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-rose-400 opacity-75" />
                    <span className="relative inline-flex rounded-full h-5 w-5 bg-rose-600 border-2 border-white items-center justify-center text-[9px] font-bold text-white shadow-lg">
                      !
                    </span>
                  </span>
                </button>
              );
            })}
          </div>

          {/* Slider Instruction Prompt */}
          <div className="flex items-center justify-between text-xs text-slate-400 font-mono">
            <span>← Drag left/right to reveal ELA heatmap</span>
            <span>Hover / tap red markers to inspect</span>
          </div>
        </div>

        {/* Right: Explainability Forensic Dossier Card (4 cols) */}
        <div className="lg:col-span-4 space-y-4">
          <div className="glass-card rounded-3xl p-6 border border-slate-800 space-y-5">
            <div className="flex items-center justify-between pb-3 border-b border-slate-800">
              <div className="flex items-center space-x-2 text-xs font-mono font-bold text-emerald-400">
                <Info className="w-4 h-4 text-emerald-400" />
                <span>EXPLAINABILITY ENGINE</span>
              </div>
              <span className="text-[10px] font-mono text-slate-500">LIVE LOCALIZER</span>
            </div>

            {activeHotspot ? (
              <div className="space-y-4 animate-in fade-in duration-200">
                <div>
                  <span className="text-[10px] font-mono uppercase tracking-wider text-rose-400 bg-rose-950/80 px-2 py-0.5 rounded border border-rose-800/60 font-bold">
                    {activeHotspot.category}
                  </span>
                  <h3 className="text-lg font-extrabold text-white mt-2">
                    {activeHotspot.title}
                  </h3>
                  <div className="flex items-center space-x-2 mt-1">
                    <span className="text-xs font-bold text-rose-400 font-mono">
                      CONFIDENCE: {activeHotspot.confidence}
                    </span>
                  </div>
                </div>

                <div className="p-3.5 rounded-2xl bg-slate-900/80 border border-slate-800 space-y-1.5">
                  <span className="text-[10px] font-mono text-slate-400 block">
                    NEURAL ATTRIBUTION FINDING:
                  </span>
                  <p className="text-xs text-slate-300 leading-relaxed">
                    {activeHotspot.detail}
                  </p>
                </div>

                <div className="p-3.5 rounded-2xl bg-slate-900/80 border border-slate-800 space-y-1.5">
                  <span className="text-[10px] font-mono text-slate-400 block">
                    CRYPTOGRAPHIC & FORENSIC EVIDENCE:
                  </span>
                  <p className="text-xs font-mono text-emerald-400 leading-relaxed">
                    {activeHotspot.evidence}
                  </p>
                </div>

                <div className="pt-2 text-[11px] text-slate-400 space-y-1">
                  <div className="flex justify-between">
                    <span>Grad-CAM Saliency:</span>
                    <span className="text-slate-200 font-mono">0.892 (High Focus)</span>
                  </div>
                  <div className="flex justify-between">
                    <span>Recommended Action:</span>
                    <span className="text-rose-400 font-semibold">Flag for Manual Audit</span>
                  </div>
                </div>
              </div>
            ) : (
              <div className="text-center py-8 text-slate-500 text-xs">
                Hover or click any marker on the certificate to inspect forensic findings.
              </div>
            )}
          </div>

          {/* Quick Stats Pill */}
          <div className="p-4 rounded-2xl bg-emerald-950/20 border border-emerald-500/30 flex items-center space-x-3">
            <FileCheck2 className="w-5 h-5 text-emerald-400 shrink-0" />
            <div className="text-xs">
              <span className="text-slate-200 font-bold block">100% Explainable Audit Trail</span>
              <span className="text-slate-400 text-[11px]">
                Every flagged pixel is backed by mathematical ELA variance and tensor baselines.
              </span>
            </div>
          </div>
        </div>
      </div>
    </section>
  );
};
