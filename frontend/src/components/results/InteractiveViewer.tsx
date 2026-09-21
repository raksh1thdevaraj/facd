import React, { useState } from 'react';
import { ZoomIn, ZoomOut, RotateCcw, Eye, Layers } from 'lucide-react';
import { OverlayAnomaly } from '../../types/report';

interface InteractiveViewerProps {
  documentImageUrl?: string | null;
  anomalies?: OverlayAnomaly[];
  gradCamUrl?: string | null;
  elaUrl?: string | null;
}

export const InteractiveViewer: React.FC<InteractiveViewerProps> = ({
  documentImageUrl,
  anomalies = [],
  gradCamUrl,
  elaUrl,
}) => {
  const [zoom, setZoom] = useState<number>(1);
  const [showOcrBoxes, setShowOcrBoxes] = useState<boolean>(true);
  const [showForensics, setShowForensics] = useState<boolean>(true);
  const [showGradCam, setShowGradCam] = useState<boolean>(false);
  const [showEla, setShowEla] = useState<boolean>(false);

  const handleZoomIn = () => setZoom((prev) => Math.min(3, prev + 0.25));
  const handleZoomOut = () => setZoom((prev) => Math.max(0.5, prev - 0.25));
  const handleResetZoom = () => setZoom(1);

  // Default synthetic certificate preview if none provided
  const fallbackPlaceholder = (
    <div className="w-full h-96 flex flex-col items-center justify-center bg-slate-950 text-slate-500 rounded-xl border border-slate-800 p-8 text-center">
      <Layers className="w-12 h-12 mb-3 text-slate-600" />
      <p className="text-sm font-semibold text-slate-400">Document Image Layer Available</p>
      <p className="text-xs text-slate-500 mt-1 max-w-sm">
        Select visual layers above to inspect detected bounding box anomalies and localized forensic artifacts.
      </p>
    </div>
  );

  const filteredAnomalies = anomalies.filter((a) => {
    if (a.layer === 'ocr' && !showOcrBoxes) return false;
    if ((a.layer === 'forensics' || a.layer === 'copy_move') && !showForensics) return false;
    return true;
  });

  return (
    <div className="glass-card rounded-2xl p-6 border border-slate-800 shadow-xl space-y-4">
      {/* Top Controls Bar */}
      <div className="flex flex-col lg:flex-row lg:items-center justify-between gap-4 border-b border-slate-800 pb-4">
        <div className="flex items-center space-x-3">
          <div className="p-2 rounded-xl bg-slate-800 text-cyan-400 border border-slate-700">
            <Eye className="w-5 h-5" />
          </div>
          <div>
            <h3 className="text-base font-bold text-slate-100">Interactive Forensic Document Viewer</h3>
            <p className="text-xs text-slate-400">Inspect multi-layer visual evidence overlays</p>
          </div>
        </div>

        {/* Layer Toggles & Zoom Controls */}
        <div className="flex flex-wrap items-center gap-2 text-xs">
          {/* Layer toggles */}
          <button
            onClick={() => setShowOcrBoxes(!showOcrBoxes)}
            className={`px-2.5 py-1.5 rounded-lg border font-medium transition-colors ${
              showOcrBoxes
                ? 'bg-cyan-950/60 text-cyan-300 border-cyan-700'
                : 'bg-slate-900 text-slate-400 border-slate-800 hover:text-slate-200'
            }`}
          >
            OCR Bounding Boxes
          </button>

          <button
            onClick={() => setShowForensics(!showForensics)}
            className={`px-2.5 py-1.5 rounded-lg border font-medium transition-colors ${
              showForensics
                ? 'bg-rose-950/60 text-rose-300 border-rose-700'
                : 'bg-slate-900 text-slate-400 border-slate-800 hover:text-slate-200'
            }`}
          >
            Forensics Anomaly Boxes
          </button>

          {gradCamUrl && (
            <button
              onClick={() => setShowGradCam(!showGradCam)}
              className={`px-2.5 py-1.5 rounded-lg border font-medium transition-colors ${
                showGradCam
                  ? 'bg-purple-950/60 text-purple-300 border-purple-700'
                  : 'bg-slate-900 text-slate-400 border-slate-800 hover:text-slate-200'
              }`}
            >
              Grad-CAM Heatmap
            </button>
          )}

          {elaUrl && (
            <button
              onClick={() => setShowEla(!showEla)}
              className={`px-2.5 py-1.5 rounded-lg border font-medium transition-colors ${
                showEla
                  ? 'bg-amber-950/60 text-amber-300 border-amber-700'
                  : 'bg-slate-900 text-slate-400 border-slate-800 hover:text-slate-200'
              }`}
            >
              ELA Difference Map
            </button>
          )}

          {/* Zoom controls */}
          <div className="flex items-center space-x-1 border-l border-slate-800 pl-2">
            <button
              onClick={handleZoomIn}
              title="Zoom In"
              className="p-1.5 rounded-lg bg-slate-900 text-slate-300 hover:bg-slate-800 border border-slate-800 transition-colors"
            >
              <ZoomIn className="w-3.5 h-3.5" />
            </button>
            <span className="font-mono text-xs text-slate-400 w-12 text-center">
              {Math.round(zoom * 100)}%
            </span>
            <button
              onClick={handleZoomOut}
              title="Zoom Out"
              className="p-1.5 rounded-lg bg-slate-900 text-slate-300 hover:bg-slate-800 border border-slate-800 transition-colors"
            >
              <ZoomOut className="w-3.5 h-3.5" />
            </button>
            <button
              onClick={handleResetZoom}
              title="Reset Zoom"
              className="p-1.5 rounded-lg bg-slate-900 text-slate-300 hover:bg-slate-800 border border-slate-800 transition-colors"
            >
              <RotateCcw className="w-3.5 h-3.5" />
            </button>
          </div>
        </div>
      </div>

      {/* Document View Area with Pan/Zoom & Overlays */}
      <div className="relative w-full h-[520px] overflow-auto bg-slate-950/90 rounded-xl border border-slate-800/80 flex items-center justify-center p-4 select-none">
        {documentImageUrl ? (
          <div
            className="relative transition-transform duration-200 ease-out origin-center inline-block max-w-full"
            style={{ transform: `scale(${zoom})` }}
          >
            {/* Base Document Image */}
            <img
              src={documentImageUrl}
              alt="Verified Certificate"
              className="rounded-lg shadow-2xl max-h-[480px] object-contain block"
            />

            {/* GradCAM Heatmap Overlay */}
            {showGradCam && gradCamUrl && (
              <img
                src={gradCamUrl}
                alt="Grad-CAM Heatmap"
                className="absolute inset-0 w-full h-full object-contain mix-blend-screen opacity-70 pointer-events-none rounded-lg"
              />
            )}

            {/* ELA Difference Overlay */}
            {showEla && elaUrl && (
              <img
                src={elaUrl}
                alt="ELA Map"
                className="absolute inset-0 w-full h-full object-contain mix-blend-screen opacity-75 pointer-events-none rounded-lg"
              />
            )}

            {/* SVG Anomaly Overlay Boxes */}
            <svg className="absolute inset-0 w-full h-full pointer-events-none">
              {filteredAnomalies.map((box, idx) => {
                const isOcr = box.layer === 'ocr';
                const strokeColor = isOcr ? '#06b6d4' : '#f43f5e';
                const fillColor = isOcr ? 'rgba(6, 182, 212, 0.15)' : 'rgba(244, 63, 94, 0.2)';

                return (
                  <g key={idx}>
                    <rect
                      x={`${box.x}%`}
                      y={`${box.y}%`}
                      width={`${box.width}%`}
                      height={`${box.height}%`}
                      fill={fillColor}
                      stroke={strokeColor}
                      strokeWidth="2"
                      strokeDasharray={isOcr ? '3,3' : 'none'}
                      rx="3"
                    />
                    {box.label && (
                      <text
                        x={`${box.x}%`}
                        y={`${Math.max(2, box.y - 1.5)}%`}
                        fill={strokeColor}
                        fontSize="10"
                        fontWeight="bold"
                        fontFamily="monospace"
                      >
                        {box.label}
                      </text>
                    )}
                  </g>
                );
              })}
            </svg>
          </div>
        ) : (
          fallbackPlaceholder
        )}
      </div>

      {/* Legend */}
      <div className="flex flex-wrap items-center gap-4 text-xs text-slate-400 pt-1">
        <span className="font-semibold text-slate-300">Evidence Legend:</span>
        <div className="flex items-center space-x-1.5">
          <span className="w-3 h-3 rounded-sm bg-cyan-500/30 border border-cyan-400 inline-block"></span>
          <span>OCR Detected Fields</span>
        </div>
        <div className="flex items-center space-x-1.5">
          <span className="w-3 h-3 rounded-sm bg-rose-500/30 border border-rose-400 inline-block"></span>
          <span>Forensics Tamper Regions</span>
        </div>
        {gradCamUrl && (
          <div className="flex items-center space-x-1.5">
            <span className="w-3 h-3 rounded-sm bg-purple-500/40 border border-purple-400 inline-block"></span>
            <span>ResNet-50 Heatmap</span>
          </div>
        )}
      </div>
    </div>
  );
};
