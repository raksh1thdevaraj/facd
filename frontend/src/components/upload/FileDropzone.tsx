import React, { useState, useRef, DragEvent, ChangeEvent } from 'react';
import { UploadCloud, FileUp, AlertCircle, Sparkles } from 'lucide-react';

const MAX_FILE_SIZE_BYTES = 10 * 1024 * 1024; // 10 MB
const ACCEPTED_EXTENSIONS = ['.pdf', '.png', '.jpg', '.jpeg'];
const ACCEPTED_MIME_TYPES = ['application/pdf', 'image/png', 'image/jpeg', 'image/jpg'];

interface FileDropzoneProps {
  onFileSelected: (file: File) => void;
  disabled?: boolean;
}

export const FileDropzone: React.FC<FileDropzoneProps> = ({ onFileSelected, disabled = false }) => {
  const [isDragOver, setIsDragOver] = useState<boolean>(false);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);
  const fileInputRef = useRef<HTMLInputElement>(null);

  const validateAndSelectFile = (file: File) => {
    setErrorMessage(null);

    // Validate size
    if (file.size > MAX_FILE_SIZE_BYTES) {
      setErrorMessage(`File size ${(file.size / (1024 * 1024)).toFixed(1)} MB exceeds the maximum 10 MB limit.`);
      return;
    }

    // Validate type
    const lowerName = file.name.toLowerCase();
    const hasValidExt = ACCEPTED_EXTENSIONS.some((ext) => lowerName.endsWith(ext));
    const hasValidMime = ACCEPTED_MIME_TYPES.includes(file.type);

    if (!hasValidExt && !hasValidMime) {
      setErrorMessage('Unsupported format. Please upload a PDF, PNG, or JPEG certificate document.');
      return;
    }

    onFileSelected(file);
  };

  const handleDragOver = (e: DragEvent<HTMLDivElement>) => {
    e.preventDefault();
    e.stopPropagation();
    if (!disabled) {
      setIsDragOver(true);
    }
  };

  const handleDragLeave = (e: DragEvent<HTMLDivElement>) => {
    e.preventDefault();
    e.stopPropagation();
    setIsDragOver(false);
  };

  const handleDrop = (e: DragEvent<HTMLDivElement>) => {
    e.preventDefault();
    e.stopPropagation();
    setIsDragOver(false);
    if (disabled) return;

    if (e.dataTransfer.files && e.dataTransfer.files.length > 0) {
      validateAndSelectFile(e.dataTransfer.files[0]);
    }
  };

  const handleFileInputChange = (e: ChangeEvent<HTMLInputElement>) => {
    if (e.target.files && e.target.files.length > 0) {
      validateAndSelectFile(e.target.files[0]);
    }
  };

  // One-click demo sample generator
  const handleLoadSample = (sampleType: 'authentic' | 'manipulated') => {
    // Generate a quick synthetic image blob for demonstration testing
    const canvas = document.createElement('canvas');
    canvas.width = 1000;
    canvas.height = 700;
    const ctx = canvas.getContext('2d');
    if (!ctx) return;

    // Background
    ctx.fillStyle = sampleType === 'authentic' ? '#fbfbfa' : '#f0efe9';
    ctx.fillRect(0, 0, 1000, 700);

    // Border
    ctx.lineWidth = 12;
    ctx.strokeStyle = sampleType === 'authentic' ? '#0f4c81' : '#8b0000';
    ctx.strokeRect(30, 30, 940, 640);

    // Seal
    ctx.beginPath();
    ctx.arc(850, 560, 60, 0, 2 * Math.PI);
    ctx.fillStyle = sampleType === 'authentic' ? '#d4af37' : '#c0392b';
    ctx.fill();

    // Text
    ctx.fillStyle = '#111827';
    ctx.font = 'bold 32px serif';
    ctx.textAlign = 'center';
    ctx.fillText('NATIONAL TECHNICAL UNIVERSITY', 500, 140);

    ctx.font = 'italic 20px serif';
    ctx.fillText('This certifies that', 500, 220);

    ctx.font = 'bold 28px serif';
    ctx.fillText(sampleType === 'authentic' ? 'ALEXANDER M. MERCER' : 'VICTOR K. VANCE', 500, 280);

    ctx.font = '18px sans-serif';
    ctx.fillText('has successfully fulfilled all requirements for the degree of', 500, 350);

    ctx.font = 'bold 24px serif';
    ctx.fillText('BACHELOR OF SCIENCE IN COMPUTER ENGINEERING', 500, 410);

    if (sampleType === 'manipulated') {
      // Add visible splice / tampering artifact
      ctx.fillStyle = 'rgba(255, 0, 0, 0.2)';
      ctx.fillRect(400, 385, 220, 35);
      ctx.font = 'bold 22px Courier';
      ctx.fillStyle = '#b91c1c';
      ctx.fillText('FIRST CLASS HONORS', 500, 470);
    } else {
      ctx.font = '18px serif';
      ctx.fillText('Awarded with Distinction on June 18, 2023', 500, 470);
    }

    canvas.toBlob((blob) => {
      if (blob) {
        const fileName =
          sampleType === 'authentic' ? 'authentic_mercer_degree.png' : 'tampered_vance_degree.png';
        const file = new File([blob], fileName, { type: 'image/png' });
        validateAndSelectFile(file);
      }
    }, 'image/png');
  };

  return (
    <div className="w-full space-y-4">
      <div
        onDragOver={handleDragOver}
        onDragLeave={handleDragLeave}
        onDrop={handleDrop}
        onClick={() => !disabled && fileInputRef.current?.click()}
        className={`relative flex flex-col items-center justify-center p-8 sm:p-12 border-2 border-dashed rounded-2xl transition-all cursor-pointer ${
          isDragOver
            ? 'border-emerald-400 bg-emerald-950/20 scale-[1.01]'
            : 'border-slate-700/80 bg-slate-900/40 hover:border-slate-600 hover:bg-slate-900/60'
        } ${disabled ? 'opacity-50 cursor-not-allowed pointer-events-none' : ''}`}
      >
        <input
          ref={fileInputRef}
          type="file"
          accept=".pdf,.png,.jpg,.jpeg"
          onChange={handleFileInputChange}
          className="hidden"
          disabled={disabled}
        />

        <div className="p-4 rounded-2xl bg-slate-800/80 border border-slate-700/60 text-emerald-400 mb-4 shadow-inner">
          <UploadCloud className="w-10 h-10 animate-pulse" />
        </div>

        <h3 className="text-base sm:text-lg font-semibold text-slate-200 text-center">
          Drag and drop academic certificate here
        </h3>
        <p className="text-xs sm:text-sm text-slate-400 mt-1.5 text-center max-w-md">
          Supports official university transcripts, diplomas, and degree certificates in{' '}
          <span className="text-slate-200 font-medium">PDF, PNG, JPG</span> format up to 10 MB.
        </p>

        <button
          type="button"
          onClick={(e) => {
            e.stopPropagation();
            fileInputRef.current?.click();
          }}
          disabled={disabled}
          className="mt-6 inline-flex items-center space-x-2 px-5 py-2.5 rounded-xl bg-emerald-600 hover:bg-emerald-500 text-white text-sm font-medium shadow-lg shadow-emerald-600/20 transition-all hover:scale-105 active:scale-95"
        >
          <FileUp className="w-4 h-4" />
          <span>Browse File from Device</span>
        </button>
      </div>

      {errorMessage && (
        <div className="flex items-center space-x-3 p-3.5 rounded-xl bg-rose-950/40 border border-rose-800/60 text-rose-300 text-sm">
          <AlertCircle className="w-5 h-5 text-rose-400 shrink-0" />
          <span>{errorMessage}</span>
        </div>
      )}

      {/* Quick Demo Preloads */}
      <div className="flex flex-wrap items-center justify-between gap-2 pt-2 px-1 text-xs text-slate-400">
        <div className="flex items-center space-x-1.5">
          <Sparkles className="w-3.5 h-3.5 text-amber-400" />
          <span>Need a quick test sample?</span>
        </div>
        <div className="flex items-center space-x-2">
          <button
            type="button"
            onClick={() => handleLoadSample('authentic')}
            disabled={disabled}
            className="px-2.5 py-1 rounded bg-slate-800 hover:bg-slate-700 text-emerald-300 border border-emerald-500/20 transition-colors"
          >
            Load Authentic Sample
          </button>
          <button
            type="button"
            onClick={() => handleLoadSample('manipulated')}
            disabled={disabled}
            className="px-2.5 py-1 rounded bg-slate-800 hover:bg-slate-700 text-rose-300 border border-rose-500/20 transition-colors"
          >
            Load Manipulated Sample
          </button>
        </div>
      </div>
    </div>
  );
};
