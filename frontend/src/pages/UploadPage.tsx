import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { FileDropzone } from '../components/upload/FileDropzone';
import { FilePreview } from '../components/upload/FilePreview';
import { PipelineStepper } from '../components/progress/PipelineStepper';
import { usePipelineProgress } from '../hooks/usePipelineProgress';
import { certificateService } from '../services/certificateService';
import { ArrowRight, RotateCcw, AlertCircle } from 'lucide-react';

export const UploadPage: React.FC = () => {
  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const [isUploading, setIsUploading] = useState<boolean>(false);
  const [certificateId, setCertificateId] = useState<string | null>(null);
  const [uploadError, setUploadError] = useState<string | null>(null);
  const navigate = useNavigate();

  const { progress, stageIndex, status, error, reportId, isComplete, isFailed } =
    usePipelineProgress(certificateId);

  // Auto-navigate to results once complete
  useEffect(() => {
    if (isComplete && (reportId || certificateId)) {
      const targetId = reportId || certificateId;
      const timeout = setTimeout(() => {
        navigate(`/results/${targetId}`);
      }, 1200);
      return () => clearTimeout(timeout);
    }
  }, [isComplete, reportId, certificateId, navigate]);

  const handleFileSelected = (file: File) => {
    setSelectedFile(file);
    setUploadError(null);
  };

  const handleRemoveFile = () => {
    setSelectedFile(null);
    setCertificateId(null);
    setUploadError(null);
  };

  const handleStartVerification = async () => {
    if (!selectedFile) return;

    try {
      setIsUploading(true);
      setUploadError(null);
      const res = await certificateService.uploadCertificate(selectedFile);
      setCertificateId(res.certificate_id);
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : 'Failed to upload and start verification';
      setUploadError(msg);
    } finally {
      setIsUploading(false);
    }
  };

  const handleReset = () => {
    setSelectedFile(null);
    setCertificateId(null);
    setUploadError(null);
  };

  return (
    <div className="max-w-4xl mx-auto space-y-8 pb-12">
      <div className="text-center space-y-2">
        <h2 className="text-2xl sm:text-3xl font-extrabold text-slate-100">
          Academic Certificate Verification
        </h2>
        <p className="text-sm text-slate-400 max-w-xl mx-auto">
          Upload any official degree, diploma, or academic transcript for multi-layer AI inspection.
        </p>
      </div>

      {uploadError && (
        <div className="p-4 rounded-xl bg-rose-950/40 border border-rose-800/60 text-rose-300 text-sm flex items-center space-x-3">
          <AlertCircle className="w-5 h-5 text-rose-400 shrink-0" />
          <span>{uploadError}</span>
        </div>
      )}

      {/* Stepper active if certificateId exists */}
      {certificateId ? (
        <div className="space-y-6">
          <PipelineStepper
            progress={progress}
            stageIndex={stageIndex}
            status={status}
            error={error}
          />

          {isComplete && (
            <div className="flex items-center justify-center pt-2">
              <button
                onClick={() => navigate(`/results/${reportId || certificateId}`)}
                className="inline-flex items-center space-x-2 px-6 py-3 rounded-xl bg-emerald-600 hover:bg-emerald-500 text-white font-semibold text-sm shadow-xl shadow-emerald-600/25 transition-all hover:scale-105"
              >
                <span>View Full Forensic Dossier</span>
                <ArrowRight className="w-4 h-4" />
              </button>
            </div>
          )}

          {isFailed && (
            <div className="flex items-center justify-center pt-2">
              <button
                onClick={handleReset}
                className="inline-flex items-center space-x-2 px-5 py-2.5 rounded-xl bg-slate-800 hover:bg-slate-700 text-slate-300 text-sm font-medium border border-slate-700 transition-colors"
              >
                <RotateCcw className="w-4 h-4" />
                <span>Upload Another Certificate</span>
              </button>
            </div>
          )}
        </div>
      ) : (
        <div className="space-y-6">
          {!selectedFile ? (
            <FileDropzone onFileSelected={handleFileSelected} disabled={isUploading} />
          ) : (
            <FilePreview
              file={selectedFile}
              onRemove={handleRemoveFile}
              onVerify={handleStartVerification}
              isUploading={isUploading}
            />
          )}
        </div>
      )}
    </div>
  );
};
