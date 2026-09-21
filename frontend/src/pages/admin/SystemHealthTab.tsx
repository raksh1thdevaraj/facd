import React, { useEffect, useState } from 'react';
import { adminService } from '../../services/adminService';
import { SystemHealthDiagnostic } from '../../types/admin';
import {
  Activity,
  HardDrive,
  Database,
  Cpu,
  CheckCircle2,
  AlertTriangle,
  Loader2,
  RefreshCw,
} from 'lucide-react';

export const SystemHealthTab: React.FC = () => {
  const [health, setHealth] = useState<SystemHealthDiagnostic | null>(null);
  const [loading, setLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);

  const fetchHealth = async () => {
    try {
      setLoading(true);
      setError(null);
      const res = await adminService.getSystemHealth();
      setHealth(res);
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : 'Failed to retrieve system health');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchHealth();
    const interval = setInterval(fetchHealth, 15000);
    return () => clearInterval(interval);
  }, []);

  if (loading && !health) {
    return (
      <div className="min-h-[300px] flex flex-col items-center justify-center space-y-3">
        <Loader2 className="w-8 h-8 animate-spin text-emerald-400" />
        <span className="text-xs text-slate-400">Querying platform diagnostic metrics...</span>
      </div>
    );
  }

  if (error || !health) {
    return (
      <div className="p-6 rounded-2xl bg-rose-950/20 border border-rose-800/60 text-center text-sm text-rose-300">
        {error || 'Unable to load diagnostic health.'}
      </div>
    );
  }

  const storagePercentage = Math.min(
    100,
    Math.round((health.storage_used_gb / health.storage_total_gb) * 100)
  );

  const stages = [
    { name: 'Ingestion & Hashing', latency: health.latency_breakdown.ingestion, max: 2.0 },
    { name: 'Deskew & Preprocessing', latency: health.latency_breakdown.preprocessing, max: 3.5 },
    { name: 'Dual-Engine OCR Extraction', latency: health.latency_breakdown.ocr, max: 5.0 },
    { name: 'Forensics & ELA Analysis', latency: health.latency_breakdown.forensics, max: 3.0 },
    { name: 'Multimodal ML Inference', latency: health.latency_breakdown.ml_inference, max: 2.0 },
    { name: 'Report & Signature Assembly', latency: health.latency_breakdown.report_generation, max: 2.5 },
  ];

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h3 className="text-lg font-bold text-slate-100">System Diagnostic Health</h3>
          <p className="text-xs text-slate-400">Hardware resources, engine statuses, and pipeline latency</p>
        </div>

        <button
          onClick={fetchHealth}
          disabled={loading}
          className="inline-flex items-center space-x-1.5 px-3 py-1.5 rounded-lg bg-slate-800 hover:bg-slate-700 text-slate-300 text-xs font-medium border border-slate-700 transition-colors disabled:opacity-50"
        >
          <RefreshCw className={`w-3.5 h-3.5 ${loading ? 'animate-spin text-emerald-400' : ''}`} />
          <span>Probe Health</span>
        </button>
      </div>

      {/* Diagnostics Grid */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        {/* Database Status Card */}
        <div className="glass-card rounded-2xl p-5 border border-slate-800 space-y-3">
          <div className="flex items-center justify-between">
            <span className="text-xs font-semibold text-slate-400 uppercase tracking-wider">Database Service</span>
            <Database className="w-4 h-4 text-cyan-400" />
          </div>

          <div className="flex items-center space-x-2">
            {health.db_status === 'ONLINE' ? (
              <CheckCircle2 className="w-5 h-5 text-emerald-400" />
            ) : (
              <AlertTriangle className="w-5 h-5 text-rose-400" />
            )}
            <span className="text-xl font-extrabold text-slate-100">{health.db_status}</span>
          </div>

          <div className="text-xs text-slate-400">
            <span>Ping Latency: </span>
            <span className="font-mono text-emerald-400 font-bold">{health.db_latency_ms} ms</span>
          </div>
        </div>

        {/* Disk Storage Card */}
        <div className="glass-card rounded-2xl p-5 border border-slate-800 space-y-3">
          <div className="flex items-center justify-between">
            <span className="text-xs font-semibold text-slate-400 uppercase tracking-wider">Document Storage</span>
            <HardDrive className="w-4 h-4 text-amber-400" />
          </div>

          <div className="flex items-baseline justify-between">
            <span className="text-xl font-extrabold font-mono text-slate-100">
              {health.storage_used_gb} GB / {health.storage_total_gb} GB
            </span>
            <span className="text-xs font-semibold text-slate-400">{storagePercentage}%</span>
          </div>

          <div className="w-full bg-slate-800 h-2 rounded-full overflow-hidden">
            <div
              className={`h-full rounded-full ${
                storagePercentage > 85 ? 'bg-rose-500' : storagePercentage > 65 ? 'bg-amber-500' : 'bg-emerald-500'
              }`}
              style={{ width: `${storagePercentage}%` }}
            />
          </div>
        </div>

        {/* Inference Acceleration Device */}
        <div className="glass-card rounded-2xl p-5 border border-slate-800 space-y-3">
          <div className="flex items-center justify-between">
            <span className="text-xs font-semibold text-slate-400 uppercase tracking-wider">AI Engines</span>
            <Cpu className="w-4 h-4 text-purple-400" />
          </div>

          <div className="flex items-center space-x-2">
            <CheckCircle2 className="w-5 h-5 text-emerald-400" />
            <span className="text-xl font-extrabold text-slate-100">Active</span>
          </div>

          <div className="text-xs text-slate-400 flex items-center justify-between">
            <span>OCR: <strong className="text-slate-200">{health.ocr_engine_status}</strong></span>
            <span>Device: <strong className="text-slate-200">{health.ml_device}</strong></span>
          </div>
        </div>
      </div>

      {/* Latency Breakdown Across Stages */}
      <div className="glass-card rounded-2xl p-6 border border-slate-800 shadow-xl space-y-4">
        <div className="flex items-center space-x-2 border-b border-slate-800 pb-3">
          <Activity className="w-5 h-5 text-emerald-400" />
          <h4 className="text-sm font-bold text-slate-100">Pipeline Latency Benchmarks by Subsystem</h4>
        </div>

        <div className="space-y-4 pt-2">
          {stages.map((stg) => {
            const pct = Math.min(100, Math.round((stg.latency / stg.max) * 100));
            return (
              <div key={stg.name} className="space-y-1.5 text-xs">
                <div className="flex items-center justify-between">
                  <span className="font-semibold text-slate-300">{stg.name}</span>
                  <span className="font-mono font-bold text-emerald-400">{stg.latency.toFixed(2)}s</span>
                </div>
                <div className="w-full bg-slate-800 h-2 rounded-full overflow-hidden">
                  <div
                    className="bg-gradient-to-r from-emerald-500 to-teal-400 h-full rounded-full transition-all duration-500"
                    style={{ width: `${pct}%` }}
                  />
                </div>
              </div>
            );
          })}
        </div>
      </div>
    </div>
  );
};
