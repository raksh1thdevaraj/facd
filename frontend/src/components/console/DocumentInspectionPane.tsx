import React, { useState, useRef } from 'react';
import {
  UploadCloud,
  AlertTriangle,
  ZoomIn,
  ZoomOut,
  RotateCcw,
  Eye,
  Layers,
  Scan,
  CheckCircle2,
  X,
} from 'lucide-react';

export interface BoundingBoxROI {
  id: string;
  label: string;
  category: 'metadata' | 'grades' | 'seal' | 'tampering';
  x: number; // percentage
  y: number; // percentage
  width: number; // percentage
  height: number; // percentage
  status?: 'verified' | 'suspicious' | 'tampered';
  annotation?: string;
}

interface DocumentInspectionPaneProps {
  file: File | null;
  filePreview: string | null;
  isProcessing: boolean;
  onFileSelect: (file: File) => void;
  onClearFile: () => void;
  onLoadSample: (sampleKey: 'authentic' | 'altered_sgpa' | 'spliced_usn') => void;
  selectedRoiId?: string | null;
  onSelectRoi?: (roiId: string | null) => void;
  boundingBoxes?: BoundingBoxROI[];
  processingStep?: string;
}

export const DocumentInspectionPane: React.FC<DocumentInspectionPaneProps> = ({
  file,
  filePreview,
  isProcessing,
  onFileSelect,
  onClearFile,
  onLoadSample,
  selectedRoiId,
  onSelectRoi,
  boundingBoxes = [],
  processingStep,
}) => {
  const [isDragOver, setIsDragOver] = useState(false);
  const [zoomLevel, setZoomLevel] = useState(1);
  const [showBoundingBoxes, setShowBoundingBoxes] = useState(true);
  const [showTypographyHeatmap, setShowTypographyHeatmap] = useState(false);
  const fileInputRef = useRef<HTMLInputElement>(null);

  const handleDragEnter = (e: React.DragEvent) => {
    e.preventDefault();
    setIsDragOver(true);
  };

  const handleDragLeave = (e: React.DragEvent) => {
    e.preventDefault();
    setIsDragOver(false);
  };

  const handleDrop = (e: React.DragEvent) => {
    e.preventDefault();
    setIsDragOver(false);
    if (e.dataTransfer.files && e.dataTransfer.files[0]) {
      onFileSelect(e.dataTransfer.files[0]);
    }
  };

  const handleFileInputChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files && e.target.files[0]) {
      onFileSelect(e.target.files[0]);
    }
  };

  const handleZoomIn = () => setZoomLevel((prev) => Math.min(prev + 0.25, 2.5));
  const handleZoomOut = () => setZoomLevel((prev) => Math.max(prev - 0.25, 0.75));
  const handleResetZoom = () => setZoomLevel(1);

  return (
    <div className="flex flex-col h-full bg-white border border-slate-200 rounded-xl shadow-xs overflow-hidden">
      {/* Pane Top Bar: Status, Zoom, Layer Controls */}
      <div className="px-4 py-3 border-b border-slate-200 bg-slate-50 flex items-center justify-between gap-3 shrink-0">
        <div className="flex items-center space-x-2">
          <Scan className="w-4 h-4 text-indigo-700" />
          <span className="font-semibold text-xs text-slate-800">
            Document Ingestion & Live Spatial Inspection
          </span>
          {file && (
            <span className="text-[11px] font-mono text-slate-500 truncate max-w-[180px] bg-white px-2 py-0.5 rounded border border-slate-200">
              {file.name}
            </span>
          )}
        </div>

        {/* View & Layer Toggles */}
        {filePreview && (
          <div className="flex items-center space-x-1.5">
            <button
              type="button"
              onClick={() => setShowBoundingBoxes(!showBoundingBoxes)}
              className={`px-2 py-1 rounded text-[11px] font-medium border flex items-center space-x-1 transition-colors ${
                showBoundingBoxes
                  ? 'bg-indigo-50 border-indigo-200 text-indigo-900'
                  : 'bg-white border-slate-200 text-slate-500 hover:text-slate-800'
              }`}
              title="Toggle Layout ROI Bounding Boxes"
            >
              <Layers className="w-3 h-3" />
              <span>ROIs</span>
            </button>

            <button
              type="button"
              onClick={() => setShowTypographyHeatmap(!showTypographyHeatmap)}
              className={`px-2 py-1 rounded text-[11px] font-medium border flex items-center space-x-1 transition-colors ${
                showTypographyHeatmap
                  ? 'bg-amber-50 border-amber-200 text-amber-900'
                  : 'bg-white border-slate-200 text-slate-500 hover:text-slate-800'
              }`}
              title="Toggle Font Inconsistency & Baseline Shift Heatmap"
            >
              <Eye className="w-3 h-3" />
              <span>Font Anomalies</span>
            </button>

            {/* Zoom Controls */}
            <div className="flex items-center space-x-0.5 pl-1 border-l border-slate-200">
              <button
                type="button"
                onClick={handleZoomOut}
                className="p-1 rounded hover:bg-slate-200 text-slate-600 transition-colors"
                title="Zoom Out"
              >
                <ZoomOut className="w-3.5 h-3.5" />
              </button>
              <span className="text-[10px] font-mono text-slate-500 w-9 text-center">
                {Math.round(zoomLevel * 100)}%
              </span>
              <button
                type="button"
                onClick={handleZoomIn}
                className="p-1 rounded hover:bg-slate-200 text-slate-600 transition-colors"
                title="Zoom In"
              >
                <ZoomIn className="w-3.5 h-3.5" />
              </button>
              <button
                type="button"
                onClick={handleResetZoom}
                className="p-1 rounded hover:bg-slate-200 text-slate-600 transition-colors"
                title="Reset Zoom"
              >
                <RotateCcw className="w-3.5 h-3.5" />
              </button>
            </div>

            <button
              type="button"
              onClick={onClearFile}
              className="p-1 rounded hover:bg-rose-50 text-slate-400 hover:text-rose-600 transition-colors ml-1"
              title="Clear current scan"
            >
              <X className="w-4 h-4" />
            </button>
          </div>
        )}
      </div>

      {/* Main Inspection Viewport */}
      <div className="flex-1 relative overflow-auto bg-slate-100 flex items-center justify-center p-4 min-h-[460px]">
        {filePreview ? (
          <div
            className="relative transition-transform duration-150 ease-out shadow-md rounded border border-slate-300 bg-white inline-block max-w-full"
            style={{ transform: `scale(${zoomLevel})`, transformOrigin: 'center center' }}
          >
            {/* Marks Sheet Raster Image */}
            <img
              src={filePreview}
              alt="Uploaded Academic Marks Card Scan"
              className="max-h-[640px] w-auto object-contain block select-none"
            />

            {/* Scanning line indicator during processing */}
            {isProcessing && <div className="scan-laser-line" />}

            {/* Overlaid Bounding Boxes (Tier 1 & Tier 3 Document Layout Understanding) */}
            {showBoundingBoxes &&
              boundingBoxes.map((roi) => {
                const isSelected = selectedRoiId === roi.id;
                const borderColor =
                  roi.status === 'tampered'
                    ? 'border-rose-500 bg-rose-500/10 text-rose-700'
                    : roi.status === 'suspicious'
                    ? 'border-amber-500 bg-amber-500/10 text-amber-700'
                    : 'border-indigo-600 bg-indigo-600/10 text-indigo-700';

                return (
                  <div
                    key={roi.id}
                    onClick={() => onSelectRoi && onSelectRoi(roi.id)}
                    className={`absolute border-2 rounded transition-all cursor-pointer group ${borderColor} ${
                      isSelected ? 'ring-2 ring-indigo-500 shadow-md scale-[1.01]' : ''
                    }`}
                    style={{
                      left: `${roi.x}%`,
                      top: `${roi.y}%`,
                      width: `${roi.width}%`,
                      height: `${roi.height}%`,
                    }}
                    title={`${roi.label} (${roi.status || 'audited'})`}
                  >
                    <span className="absolute -top-5 left-0 px-1 py-0.2 text-[9px] font-mono font-bold bg-white border border-slate-300 rounded shadow-xs whitespace-nowrap">
                      {roi.label}
                    </span>
                    {roi.annotation && (
                      <div className="opacity-0 group-hover:opacity-100 absolute bottom-full left-1/2 -translate-x-1/2 mb-1 px-2 py-1 bg-slate-900 text-white text-[10px] rounded shadow-lg pointer-events-none transition-opacity duration-150 whitespace-nowrap z-30">
                        {roi.annotation}
                      </div>
                    )}
                  </div>
                );
              })}

            {/* Font Anomaly Heatmap Layer */}
            {showTypographyHeatmap && (
              <div className="absolute inset-0 pointer-events-none bg-radial from-amber-500/15 via-transparent to-transparent mix-blend-multiply" />
            )}
          </div>
        ) : (
          /* Empty / Drag & Drop Upload State */
          <div
            onDragEnter={handleDragEnter}
            onDragOver={handleDragEnter}
            onDragLeave={handleDragLeave}
            onDrop={handleDrop}
            className={`w-full max-w-lg p-8 border-2 border-dashed rounded-xl flex flex-col items-center justify-center text-center transition-colors cursor-pointer bg-white ${
              isDragOver
                ? 'border-indigo-600 bg-indigo-50/50'
                : 'border-slate-300 hover:border-slate-400'
            }`}
            onClick={() => fileInputRef.current?.click()}
          >
            <input
              ref={fileInputRef}
              type="file"
              accept="image/png,image/jpeg,image/webp,application/pdf"
              className="hidden"
              onChange={handleFileInputChange}
            />

            <div className="w-14 h-14 rounded-2xl bg-indigo-50 border border-indigo-100 text-indigo-900 flex items-center justify-center mb-4 shadow-xs">
              <UploadCloud className="w-7 h-7 text-indigo-800" />
            </div>

            <h3 className="text-base font-bold text-slate-900 mb-1">
              Drop University Marks Card Here
            </h3>
            <p className="text-xs text-slate-500 max-w-sm mb-4 leading-relaxed">
              Upload official VTU semester grade sheets, marks cards, or transcript scans (PNG, JPG, PDF up to 50MB)
            </p>

            <button
              type="button"
              className="px-4 py-2 bg-indigo-900 hover:bg-indigo-800 text-white text-xs font-semibold rounded-lg shadow-sm transition-all"
            >
              Select Scan File
            </button>

            {/* Fast Pre-Loaded Institutional Samples */}
            <div
              className="mt-6 pt-5 border-t border-slate-200 w-full"
              onClick={(e) => e.stopPropagation()}
            >
              <div className="text-[11px] font-semibold text-slate-500 uppercase tracking-wider mb-2.5">
                Load Fast Test Samples (Instant Demonstration)
              </div>
              <div className="grid grid-cols-1 sm:grid-cols-3 gap-2">
                <button
                  type="button"
                  onClick={() => onLoadSample('authentic')}
                  className="px-2.5 py-2 text-left rounded-lg border border-emerald-200 bg-emerald-50 hover:bg-emerald-100/80 transition-colors group"
                >
                  <div className="text-[11px] font-bold text-emerald-900 flex items-center space-x-1">
                    <CheckCircle2 className="w-3 h-3 text-emerald-700" />
                    <span>Sample 1</span>
                  </div>
                  <div className="text-[10px] text-emerald-700 leading-tight">
                    Authentic VTU Marks Card (Clean 8.52 SGPA)
                  </div>
                </button>

                <button
                  type="button"
                  onClick={() => onLoadSample('altered_sgpa')}
                  className="px-2.5 py-2 text-left rounded-lg border border-rose-200 bg-rose-50 hover:bg-rose-100/80 transition-colors group"
                >
                  <div className="text-[11px] font-bold text-rose-900 flex items-center space-x-1">
                    <AlertTriangle className="w-3 h-3 text-rose-700" />
                    <span>Sample 2</span>
                  </div>
                  <div className="text-[10px] text-rose-700 leading-tight">
                    Altered SGPA Fraud (Math Δ = 0.84)
                  </div>
                </button>

                <button
                  type="button"
                  onClick={() => onLoadSample('spliced_usn')}
                  className="px-2.5 py-2 text-left rounded-lg border border-amber-200 bg-amber-50 hover:bg-amber-100/80 transition-colors group"
                >
                  <div className="text-[11px] font-bold text-amber-900 flex items-center space-x-1">
                    <AlertTriangle className="w-3 h-3 text-amber-700" />
                    <span>Sample 3</span>
                  </div>
                  <div className="text-[10px] text-amber-700 leading-tight">
                    Spliced USN & Font Inconsistency
                  </div>
                </button>
              </div>
            </div>
          </div>
        )}
      </div>

      {/* Interactive Detected Region Chips */}
      {filePreview && boundingBoxes.length > 0 && (
        <div className="px-3 py-2 border-t border-slate-200 bg-slate-50 flex items-center space-x-1.5 overflow-x-auto shrink-0 text-xs">
          <span className="text-[10px] uppercase font-bold text-slate-500 whitespace-nowrap mr-1">
            Detected ROIs:
          </span>
          {boundingBoxes.map((roi) => {
            const isSelected = selectedRoiId === roi.id;
            const badgeBg =
              roi.status === 'tampered'
                ? isSelected
                  ? 'bg-rose-600 text-white border-rose-600'
                  : 'bg-rose-50 text-rose-800 border-rose-300 hover:bg-rose-100'
                : roi.status === 'suspicious'
                ? isSelected
                  ? 'bg-amber-600 text-white border-amber-600'
                  : 'bg-amber-50 text-amber-800 border-amber-300 hover:bg-amber-100'
                : isSelected
                ? 'bg-indigo-900 text-white border-indigo-900'
                : 'bg-white text-slate-700 border-slate-200 hover:bg-slate-100';

            return (
              <button
                key={roi.id}
                type="button"
                onClick={() => {
                  onSelectRoi && onSelectRoi(roi.id);
                  setZoomLevel(1.5);
                }}
                className={`px-2 py-0.5 rounded-full border text-[10px] font-mono font-medium whitespace-nowrap transition-all flex items-center space-x-1 cursor-pointer ${badgeBg}`}
              >
                <span>{roi.label}</span>
                {roi.status === 'tampered' && (
                  <span className="w-1.5 h-1.5 rounded-full bg-rose-500 inline-block animate-pulse" />
                )}
              </button>
            );
          })}
        </div>
      )}

      {/* Processing Status Banner */}
      {isProcessing && (
        <div className="px-4 py-2.5 bg-indigo-50 border-t border-indigo-200 flex items-center justify-between text-xs text-indigo-900">
          <div className="flex items-center space-x-2">
            <span className="relative flex h-2 w-2">
              <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-indigo-400 opacity-75" />
              <span className="relative inline-flex rounded-full h-2 w-2 bg-indigo-600" />
            </span>
            <span className="font-semibold">
              {processingStep || 'Executing Multimodal OCR-Free Inspection & Gemini Vision Forensics...'}
            </span>
          </div>
          <span className="font-mono text-[10px] text-indigo-700">Tier 1 &rarr; Tier 2 &rarr; Tier 3</span>
        </div>
      )}
    </div>
  );
};
