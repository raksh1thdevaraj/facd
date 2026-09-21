import React, { useState, useEffect } from 'react';
import { FileText, Image as ImageIcon, X, ArrowRight, Loader2 } from 'lucide-react';

interface FilePreviewProps {
  file: File;
  onRemove: () => void;
  onVerify: () => void;
  isUploading?: boolean;
}

export const FilePreview: React.FC<FilePreviewProps> = ({
  file,
  onRemove,
  onVerify,
  isUploading = false,
}) => {
  const [previewUrl, setPreviewUrl] = useState<string | null>(null);

  useEffect(() => {
    if (file.type.startsWith('image/')) {
      const url = URL.createObjectURL(file);
      setPreviewUrl(url);
      return () => URL.revokeObjectURL(url);
    } else {
      setPreviewUrl(null);
    }
  }, [file]);

  const formatFileSize = (bytes: number): string => {
    if (bytes < 1024) return `${bytes} B`;
    if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`;
    return `${(bytes / (1024 * 1024)).toFixed(2)} MB`;
  };

  const isPdf = file.type === 'application/pdf' || file.name.toLowerCase().endsWith('.pdf');

  return (
    <div className="glass-card rounded-2xl p-5 border border-slate-700/70 shadow-xl space-y-4">
      <div className="flex items-start justify-between gap-4">
        <div className="flex items-center space-x-4 min-w-0">
          {previewUrl ? (
            <div className="w-16 h-16 rounded-xl overflow-hidden border border-slate-700 bg-slate-900 shrink-0">
              <img src={previewUrl} alt="Certificate thumbnail" className="w-full h-full object-cover" />
            </div>
          ) : (
            <div className="w-16 h-16 rounded-xl bg-slate-800 flex items-center justify-center border border-slate-700 text-emerald-400 shrink-0">
              {isPdf ? <FileText className="w-8 h-8" /> : <ImageIcon className="w-8 h-8" />}
            </div>
          )}

          <div className="min-w-0">
            <h4 className="text-sm sm:text-base font-semibold text-slate-100 truncate" title={file.name}>
              {file.name}
            </h4>
            <div className="flex items-center space-x-2 text-xs text-slate-400 mt-1">
              <span className="uppercase px-1.5 py-0.5 rounded bg-slate-800 border border-slate-700 font-mono">
                {file.name.split('.').pop() || 'FILE'}
              </span>
              <span>•</span>
              <span>{formatFileSize(file.size)}</span>
              <span>•</span>
              <span className="text-emerald-400 font-medium">Ready for Ingestion</span>
            </div>
          </div>
        </div>

        <button
          onClick={onRemove}
          disabled={isUploading}
          title="Remove file"
          className="p-1.5 rounded-lg text-slate-400 hover:text-rose-400 hover:bg-slate-800/80 transition-colors disabled:opacity-50"
        >
          <X className="w-5 h-5" />
        </button>
      </div>

      <div className="pt-2 border-t border-slate-800 flex items-center justify-between">
        <span className="text-xs text-slate-400">
          Pipeline runs 6 AI/Forensics checks sequentially
        </span>

        <button
          onClick={onVerify}
          disabled={isUploading}
          className="inline-flex items-center space-x-2 px-6 py-2.5 rounded-xl bg-gradient-to-r from-emerald-600 to-teal-600 hover:from-emerald-500 hover:to-teal-500 text-white font-medium text-sm shadow-lg shadow-emerald-500/25 transition-all hover:scale-105 active:scale-95 disabled:opacity-50 disabled:pointer-events-none"
        >
          {isUploading ? (
            <>
              <Loader2 className="w-4 h-4 animate-spin" />
              <span>Uploading Document...</span>
            </>
          ) : (
            <>
              <span>Run Verification Pipeline</span>
              <ArrowRight className="w-4 h-4" />
            </>
          )}
        </button>
      </div>
    </div>
  );
};
