import React, { useState, useEffect } from 'react';
import apiClient from '../../services/api';
import {
  ShieldAlert,
  ShieldCheck,
  AlertTriangle,
  RefreshCw,
  Clock,
  Filter,
  Globe,
  Monitor,
} from 'lucide-react';

interface BehavioralLogItem {
  user_id: string;
  timestamp: string;
  source_ip: string;
  location?: string;
  device_type: string;
  action: string;
  is_anomalous?: boolean;
  fraud_probability?: number;
  threat_level: 'CRITICAL' | 'ELEVATED' | 'NORMAL' | string;
  risk_score: number;
  flags: string[];
}

export const BehavioralMonitorTab: React.FC = () => {
  const [logs, setLogs] = useState<BehavioralLogItem[]>([]);
  const [loading, setLoading] = useState<boolean>(true);
  const [threatFilter, setThreatFilter] = useState<string>('ALL');
  const [error, setError] = useState<string | null>(null);

  const fetchLogs = async () => {
    try {
      setLoading(true);
      setError(null);
      const url =
        threatFilter === 'ALL'
          ? '/admin/behavioral-logs?limit=30'
          : `/admin/behavioral-logs?limit=30&threat_filter=${threatFilter}`;
      const res = await apiClient.get<BehavioralLogItem[]>(url);
      if (Array.isArray(res.data)) {
        setLogs(res.data);
      }
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : 'Failed to fetch behavioral logs');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchLogs();
  }, [threatFilter]);

  const criticalCount = logs.filter((l) => l.threat_level === 'CRITICAL').length;
  const normalCount = logs.filter((l) => l.threat_level === 'NORMAL').length;

  return (
    <div className="space-y-6">
      {/* Top Banner */}
      <div className="p-6 rounded-3xl bg-gradient-to-r from-slate-900 via-indigo-950/40 to-slate-900 border border-slate-800 flex flex-col md:flex-row md:items-center justify-between gap-4">
        <div>
          <div className="flex items-center space-x-2">
            <span className="px-2.5 py-0.5 rounded-full text-[10px] font-bold uppercase tracking-wider bg-indigo-500/10 text-indigo-400 border border-indigo-500/30">
              Khormi et al. (IEEE 2026) Engine
            </span>
            <span className="text-xs text-slate-500 font-mono">Logistic Regression + SMOTE (100% AUC)</span>
          </div>
          <h3 className="text-xl font-bold text-white mt-1">
            Pre-Issuance Behavioral Anomaly Monitor
          </h3>
          <p className="text-xs text-slate-400 mt-0.5 max-w-2xl">
            Monitors institutional registrar operational access logs to intercept insider credential tampering, off-hours batch creations, and unverified external IP issuance attempts before certificates reach student hands.
          </p>
        </div>

        {/* Action button */}
        <button
          onClick={fetchLogs}
          disabled={loading}
          className="inline-flex items-center space-x-2 px-4 py-2 rounded-xl bg-slate-800 hover:bg-slate-700 text-slate-200 text-xs font-semibold border border-slate-700 transition-colors self-start md:self-center cursor-pointer"
        >
          <RefreshCw className={`w-3.5 h-3.5 ${loading ? 'animate-spin text-emerald-400' : ''}`} />
          <span>Refresh Feed</span>
        </button>
      </div>

      {/* Filter and KPI Strip */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3">
        <div className="flex items-center space-x-2">
          <span className="text-xs font-bold text-slate-400 flex items-center space-x-1">
            <Filter className="w-3.5 h-3.5" />
            <span>Filter Threat:</span>
          </span>
          {['ALL', 'CRITICAL', 'ELEVATED', 'NORMAL'].map((lvl) => (
            <button
              key={lvl}
              onClick={() => setThreatFilter(lvl)}
              className={`px-3 py-1 rounded-lg text-xs font-semibold transition-all ${
                threatFilter === lvl
                  ? lvl === 'CRITICAL'
                    ? 'bg-rose-500 text-white'
                    : lvl === 'NORMAL'
                    ? 'bg-emerald-500 text-slate-950 font-bold'
                    : 'bg-indigo-500 text-white'
                  : 'bg-slate-900 text-slate-400 hover:text-white border border-slate-800'
              }`}
            >
              {lvl}
            </button>
          ))}
        </div>

        <div className="flex items-center space-x-3 text-xs text-slate-400">
          <span className="flex items-center space-x-1.5">
            <span className="w-2 h-2 rounded-full bg-rose-500 animate-pulse" />
            <span>Critical Threats: <strong className="text-rose-400">{criticalCount}</strong></span>
          </span>
          <span>•</span>
          <span className="flex items-center space-x-1.5">
            <span className="w-2 h-2 rounded-full bg-emerald-400" />
            <span>Normal Operations: <strong className="text-emerald-400">{normalCount}</strong></span>
          </span>
        </div>
      </div>

      {/* Live Stream Table */}
      {loading && logs.length === 0 ? (
        <div className="min-h-[260px] rounded-2xl bg-slate-900/40 border border-slate-800 flex items-center justify-center">
          <RefreshCw className="w-6 h-6 animate-spin text-indigo-400" />
        </div>
      ) : error ? (
        <div className="p-4 rounded-xl bg-rose-950/20 border border-rose-800/60 text-xs text-rose-300">
          {error}
        </div>
      ) : logs.length === 0 ? (
        <div className="p-8 text-center text-xs text-slate-500 rounded-2xl bg-slate-900/30 border border-slate-800">
          No logs match the selected threat filter.
        </div>
      ) : (
        <div className="space-y-3">
          {logs.map((log, idx) => {
            const isCritical = log.threat_level === 'CRITICAL';
            const isElevated = log.threat_level === 'ELEVATED';

            return (
              <div
                key={idx}
                className={`p-4 rounded-2xl border transition-all ${
                  isCritical
                    ? 'bg-gradient-to-r from-rose-950/40 via-slate-900 to-slate-900 border-rose-700/60 shadow-lg shadow-rose-950/20'
                    : isElevated
                    ? 'bg-amber-950/20 border-amber-800/40'
                    : 'bg-slate-900/60 border-slate-800/80 hover:border-slate-700'
                }`}
              >
                <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 mb-2">
                  <div className="flex items-center space-x-3">
                    <div
                      className={`p-2 rounded-xl ${
                        isCritical
                          ? 'bg-rose-500/20 text-rose-400 border border-rose-500/40'
                          : isElevated
                          ? 'bg-amber-500/20 text-amber-400 border border-amber-500/40'
                          : 'bg-emerald-500/10 text-emerald-400 border border-emerald-500/20'
                      }`}
                    >
                      {isCritical ? (
                        <ShieldAlert className="w-4 h-4" />
                      ) : isElevated ? (
                        <AlertTriangle className="w-4 h-4" />
                      ) : (
                        <ShieldCheck className="w-4 h-4" />
                      )}
                    </div>
                    <div>
                      <div className="flex items-center space-x-2">
                        <span className="font-mono text-xs font-bold text-white">
                          {log.user_id}
                        </span>
                        <span
                          className={`text-[9px] font-bold px-2 py-0.5 rounded-full border uppercase ${
                            isCritical
                              ? 'bg-rose-500/20 text-rose-300 border-rose-500/40'
                              : isElevated
                              ? 'bg-amber-500/20 text-amber-300 border-amber-500/40'
                              : 'bg-emerald-500/20 text-emerald-300 border-emerald-500/40'
                          }`}
                        >
                          {log.threat_level} • Risk {log.risk_score}
                        </span>
                      </div>
                      <span className="text-[11px] text-slate-400 flex items-center space-x-2 mt-0.5">
                        <Clock className="w-3 h-3 text-slate-500" />
                        <span>{log.timestamp}</span>
                      </span>
                    </div>
                  </div>

                  <div className="flex items-center space-x-4 text-xs">
                    <span className="text-slate-400 flex items-center space-x-1">
                      <Globe className="w-3 h-3 text-slate-500" />
                      <span className="font-mono">{log.source_ip}</span>
                    </span>
                    <span className="text-slate-400 flex items-center space-x-1">
                      <Monitor className="w-3 h-3 text-slate-500" />
                      <span>{log.device_type}</span>
                    </span>
                    <span className="font-bold text-slate-200 px-2 py-0.5 rounded bg-slate-800 text-[11px]">
                      {log.action}
                    </span>
                  </div>
                </div>

                {/* Threat Flags */}
                {log.flags && log.flags.length > 0 && (
                  <div className="mt-2.5 pt-2 border-t border-slate-800/80 flex flex-wrap gap-1.5">
                    {log.flags.map((flag: string, fIdx: number) => (
                      <span
                        key={fIdx}
                        className="text-[10px] font-medium px-2 py-0.5 rounded-md bg-rose-950/80 text-rose-300 border border-rose-800/60"
                      >
                        {flag}
                      </span>
                    ))}
                  </div>
                )}
              </div>
            );
          })}
        </div>
      )}
    </div>
  );
};
