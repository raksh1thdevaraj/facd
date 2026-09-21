import React from 'react';
import { CheckCircle2, Loader2, AlertTriangle, ShieldCheck, Database, Search, Cpu, FileCheck } from 'lucide-react';
import { PIPELINE_STAGES } from '../../hooks/usePipelineProgress';
import { JobStatus } from '../../types/certificate';

interface PipelineStepperProps {
  progress: number;
  stageIndex: number;
  status: JobStatus | null;
  error?: string | null;
}

const STAGE_ICONS = [
  Database,     // Ingestion
  ShieldCheck,  // Preprocessing
  Search,       // OCR
  FileCheck,    // Forensics
  Cpu,          // Multimodal ML
  CheckCircle2, // Dossier
];

export const PipelineStepper: React.FC<PipelineStepperProps> = ({
  progress,
  stageIndex,
  status,
  error,
}) => {
  const isFailed = status === 'FAILED';

  return (
    <div className="glass-card rounded-2xl p-6 sm:p-8 border border-slate-800 shadow-2xl space-y-8">
      {/* Top Header & Percentage */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <div className="flex items-center space-x-2">
            <span className="relative flex h-3 w-3">
              {!isFailed && status !== 'COMPLETED' && (
                <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-emerald-400 opacity-75"></span>
              )}
              <span
                className={`relative inline-flex rounded-full h-3 w-3 ${
                  isFailed
                    ? 'bg-rose-500'
                    : status === 'COMPLETED'
                    ? 'bg-emerald-500'
                    : 'bg-emerald-400'
                }`}
              ></span>
            </span>
            <h3 className="text-lg font-bold text-slate-100">
              {isFailed
                ? 'Verification Pipeline Halted'
                : status === 'COMPLETED'
                ? 'Verification Pipeline Finished'
                : 'Running Automated Deep Verification Pipeline'}
            </h3>
          </div>
          <p className="text-xs sm:text-sm text-slate-400 mt-1">
            {isFailed
              ? error || 'Pipeline failed to process certificate'
              : status === 'COMPLETED'
              ? 'All forensic, typography, and visual models completed successfully'
              : 'Executing multi-stage forensic analysis, dual-OCR, and deep feature attribution'}
          </p>
        </div>

        <div className="flex items-baseline space-x-2 self-start sm:self-auto bg-slate-900/80 px-4 py-2 rounded-xl border border-slate-800">
          <span className="text-2xl sm:text-3xl font-extrabold font-mono text-emerald-400">
            {Math.round(progress)}%
          </span>
          <span className="text-xs uppercase tracking-wider text-slate-500 font-semibold">
            Progress
          </span>
        </div>
      </div>

      {/* Progress Bar */}
      <div className="w-full bg-slate-900 rounded-full h-2.5 overflow-hidden border border-slate-800">
        <div
          role="progressbar"
          aria-valuenow={Math.round(progress)}
          aria-valuemin={0}
          aria-valuemax={100}
          className={`h-full transition-all duration-500 rounded-full ${
            isFailed
              ? 'bg-rose-500'
              : 'bg-gradient-to-r from-emerald-500 via-teal-400 to-cyan-400'
          }`}
          style={{ width: `${Math.min(100, Math.max(0, progress))}%` }}
        />
      </div>

      {/* Stepper Stages Grid / List */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
        {PIPELINE_STAGES.map((stage, index) => {
          const Icon = STAGE_ICONS[index] || ShieldCheck;
          const isDone = index < stageIndex || status === 'COMPLETED';
          const isCurrent = index === stageIndex && status !== 'COMPLETED' && !isFailed;
          const isStageFailed = isFailed && index === stageIndex;

          return (
            <div
              key={stage.id}
              className={`flex items-start space-x-3.5 p-3.5 rounded-xl border transition-all ${
                isDone
                  ? 'bg-emerald-950/20 border-emerald-800/40 text-slate-200'
                  : isCurrent
                  ? 'bg-slate-800/80 border-emerald-500/60 shadow-lg shadow-emerald-900/20 text-slate-100 ring-1 ring-emerald-500/30'
                  : isStageFailed
                  ? 'bg-rose-950/20 border-rose-800/50 text-slate-300'
                  : 'bg-slate-900/40 border-slate-800/60 text-slate-500'
              }`}
            >
              <div
                className={`p-2 rounded-lg shrink-0 ${
                  isDone
                    ? 'bg-emerald-500/20 text-emerald-400'
                    : isCurrent
                    ? 'bg-emerald-600 text-white'
                    : isStageFailed
                    ? 'bg-rose-600 text-white'
                    : 'bg-slate-800 text-slate-600'
                }`}
              >
                {isDone ? (
                  <CheckCircle2 className="w-4 h-4" />
                ) : isCurrent ? (
                  <Loader2 className="w-4 h-4 animate-spin" />
                ) : isStageFailed ? (
                  <AlertTriangle className="w-4 h-4" />
                ) : (
                  <Icon className="w-4 h-4" />
                )}
              </div>

              <div className="min-w-0">
                <div className="flex items-center space-x-2">
                  <span className="text-xs font-mono font-medium text-slate-400">
                    0{index + 1}.
                  </span>
                  <h4 className="text-sm font-semibold truncate">{stage.label}</h4>
                </div>
                <p className="text-xs text-slate-400 mt-0.5 line-clamp-2 leading-relaxed">
                  {stage.description}
                </p>
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
};
