import { useState, useEffect, useCallback, useRef } from 'react';
import { certificateService } from '../services/certificateService';
import { JobStatus } from '../types/certificate';

export interface PipelineProgressState {
  certificateId: string | null;
  status: JobStatus | null;
  progress: number;
  stageIndex: number;
  error: string | null;
  reportId: string | null;
  isComplete: boolean;
  isFailed: boolean;
}

export const PIPELINE_STAGES = [
  { id: 'ingestion', label: 'Ingestion & Hashing', description: 'SHA-256 verification & format parsing' },
  { id: 'preprocessing', label: 'Preprocessing & Rectification', description: 'Deskewing, illumination correction & noise reduction' },
  { id: 'ocr', label: 'OCR & Layout Extraction', description: 'Dual-engine text extraction & spatial token mapping' },
  { id: 'forensics', label: 'Forensics & Consistency', description: 'ELA, copy-move detection & font cross-validation' },
  { id: 'classification', label: 'Multimodal ML Ensemble', description: 'ResNet-50 visual feature attribution & fused scoring' },
  { id: 'dossier', label: 'Dossier Generation', description: 'Cryptographic report assembly & tamper-evident signature' },
];

export const getStageIndexFromProgress = (progress: number, status: JobStatus | null): number => {
  if (status === 'COMPLETED') return 5;
  if (progress <= 15) return 0;
  if (progress <= 35) return 1;
  if (progress <= 55) return 2;
  if (progress <= 75) return 3;
  if (progress <= 90) return 4;
  return 5;
};

export const usePipelineProgress = (certificateId: string | null, pollIntervalMs: number = 800) => {
  const [state, setState] = useState<PipelineProgressState>({
    certificateId,
    status: null,
    progress: 0,
    stageIndex: 0,
    error: null,
    reportId: null,
    isComplete: false,
    isFailed: false,
  });

  const timerRef = useRef<ReturnType<typeof setInterval> | null>(null);

  const fetchStatus = useCallback(async () => {
    if (!certificateId) return;

    try {
      const res = await certificateService.getCertificateStatus(certificateId);
      const isComplete = res.status === 'COMPLETED';
      const isFailed = res.status === 'FAILED';
      const stageIdx = getStageIndexFromProgress(res.progress, res.status);

      setState({
        certificateId,
        status: res.status,
        progress: res.progress,
        stageIndex: stageIdx,
        error: isFailed ? res.error || 'Verification pipeline encountered a failure' : null,
        reportId: res.report_id || null,
        isComplete,
        isFailed,
      });

      if (isComplete || isFailed) {
        if (timerRef.current) {
          clearInterval(timerRef.current);
          timerRef.current = null;
        }
      }
    } catch (err: unknown) {
      const errorMessage = err instanceof Error ? err.message : 'Network error polling status';
      setState((prev) => ({
        ...prev,
        error: errorMessage,
      }));
    }
  }, [certificateId]);

  useEffect(() => {
    if (!certificateId) {
      setState({
        certificateId: null,
        status: null,
        progress: 0,
        stageIndex: 0,
        error: null,
        reportId: null,
        isComplete: false,
        isFailed: false,
      });
      return;
    }

    fetchStatus();
    timerRef.current = setInterval(fetchStatus, pollIntervalMs);

    return () => {
      if (timerRef.current) {
        clearInterval(timerRef.current);
        timerRef.current = null;
      }
    };
  }, [certificateId, pollIntervalMs, fetchStatus]);

  return {
    ...state,
    refetch: fetchStatus,
  };
};
