import React, { useCallback, useEffect, useRef, useState } from 'react';
import axios from 'axios';

interface HealthData {
  status: string;
  service?: string;
  timestamp?: string;
  db_connected?: boolean;
  model_engine?: string;
  latency_ms?: number;
}

export const SystemHealthBadge: React.FC = () => {
  const [isOperational, setIsOperational] = useState<boolean>(true);
  const [isInitializing, setIsInitializing] = useState<boolean>(false);
  const [latency, setLatency] = useState<number>(24);
  const [isChecking, setIsChecking] = useState<boolean>(false);

  const consecutiveFailuresRef = useRef<number>(0);
  const isMountedRef = useRef<boolean>(true);

  const fetchHealth = useCallback(async () => {
    if (!isMountedRef.current) return;
    setIsChecking(true);
    const startTime = performance.now();

    try {
      // 1. Primary probe to /api/health with tight 3.5s timeout
      let res;
      try {
        res = await axios.get<HealthData>('/api/health', { timeout: 3500 });
      } catch (primaryErr) {
        // Fallback probe to root /health in case of route proxy jitter
        if (axios.isAxiosError(primaryErr) && primaryErr.response?.status === 503) {
          if (isMountedRef.current) {
            setIsInitializing(true);
            setIsOperational(true);
            consecutiveFailuresRef.current = 0;
          }
          return;
        }
        res = await axios.get<HealthData>('/health', { timeout: 3500 });
      }

      const endLatency = Math.round(performance.now() - startTime);

      if (isMountedRef.current) {
        const data = res.data;
        const healthy =
          data.status === 'healthy' ||
          data.status === 'ok' ||
          data.service === 'operational' ||
          data.status === 'degraded';

        if (healthy) {
          consecutiveFailuresRef.current = 0;
          setIsOperational(true);
          setIsInitializing(false);
          setLatency(data.latency_ms || endLatency || 18);
        } else {
          consecutiveFailuresRef.current += 1;
          if (consecutiveFailuresRef.current >= 2) {
            setIsOperational(false);
            setIsInitializing(false);
          }
        }
      }
    } catch {
      if (isMountedRef.current) {
        consecutiveFailuresRef.current += 1;
        // Require 2 consecutive failures before showing error badge
        if (consecutiveFailuresRef.current >= 2) {
          setIsOperational(false);
          setIsInitializing(false);
        }
      }
    } finally {
      if (isMountedRef.current) {
        setIsChecking(false);
      }
    }
  }, []);

  useEffect(() => {
    isMountedRef.current = true;
    fetchHealth();

    // Adaptive polling: poll every 3s if degraded/recovering, otherwise every 15s
    const pollInterval = isOperational && !isInitializing ? 15000 : 3000;
    const intervalId = setInterval(fetchHealth, pollInterval);

    return () => {
      isMountedRef.current = false;
      clearInterval(intervalId);
    };
  }, [fetchHealth, isOperational, isInitializing]);

  // Case 1: Operational / Healthy
  if (isOperational && !isInitializing) {
    return (
      <button
        type="button"
        onClick={fetchHealth}
        className="group relative inline-flex items-center space-x-2 px-3 py-1.5 rounded-full bg-emerald-950/60 border border-emerald-500/30 text-emerald-400 text-xs font-mono font-medium shadow-sm transition-all hover:border-emerald-500/60 cursor-pointer focus:outline-none"
        title={`Engine Active • ${latency}ms (Click to refresh)`}
        aria-label="Engine status: Active"
      >
        <span className="relative flex h-2 w-2">
          <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-[#10B981] opacity-75" />
          <span className="relative inline-flex rounded-full h-2 w-2 bg-[#10B981]" />
        </span>
        <span className="font-semibold tracking-wide">Engine Active</span>
        {isChecking && <span className="text-[10px] opacity-70 animate-pulse">↻</span>}

        {/* Hover Tooltip displaying latency and click advisory */}
        <div className="absolute top-full left-1/2 -translate-x-1/2 mt-2 px-2.5 py-1 bg-slate-900 border border-slate-700 text-slate-200 text-[11px] rounded-lg shadow-xl opacity-0 group-hover:opacity-100 pointer-events-none transition-opacity duration-150 whitespace-nowrap z-50">
          Operational • {latency}ms • Click to refresh
        </div>
      </button>
    );
  }

  // Case 2: Initializing / Warming up
  if (isInitializing) {
    return (
      <button
        type="button"
        onClick={fetchHealth}
        className="group relative inline-flex items-center space-x-2 px-3 py-1.5 rounded-full bg-amber-950/60 border border-amber-500/40 text-amber-400 text-xs font-mono font-medium shadow-sm transition-all hover:border-amber-500/70 cursor-pointer focus:outline-none"
        title="Engine Initializing • Connecting... (Click to retry)"
        aria-label="Engine status: Initializing"
      >
        <span className="relative flex h-2 w-2">
          <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-amber-400 opacity-75" />
          <span className="relative inline-flex rounded-full h-2 w-2 bg-amber-400" />
        </span>
        <span className="font-semibold tracking-wide">Engine Starting...</span>

        {/* Hover Tooltip */}
        <div className="absolute top-full left-1/2 -translate-x-1/2 mt-2 px-2.5 py-1 bg-slate-900 border border-amber-700 text-amber-300 text-[11px] rounded-lg shadow-xl opacity-0 group-hover:opacity-100 pointer-events-none transition-opacity duration-150 whitespace-nowrap z-50">
          Backend is initializing • Auto-reconnecting • Click to retry
        </div>
      </button>
    );
  }

  // Case 3: Offline / Server Unreachable
  return (
    <button
      type="button"
      onClick={fetchHealth}
      className="group relative inline-flex items-center space-x-2 px-3 py-1.5 rounded-full bg-rose-950/60 border border-[#EF4444]/40 text-[#EF4444] text-xs font-mono font-medium shadow-sm transition-all hover:border-[#EF4444]/80 cursor-pointer focus:outline-none"
      title="System Issues Detected • Server Unreachable (Click to retry)"
      aria-label="Engine status: System Issues Detected"
    >
      <span className="relative flex h-2 w-2">
        <span className="relative inline-flex rounded-full h-2 w-2 bg-[#EF4444]" />
      </span>
      <span className="font-semibold tracking-wide">System Issues Detected</span>
      {isChecking && <span className="text-[10px] opacity-70 animate-pulse">↻</span>}

      {/* Hover Tooltip */}
      <div className="absolute top-full left-1/2 -translate-x-1/2 mt-2 px-2.5 py-1 bg-slate-900 border border-rose-800 text-rose-300 text-[11px] rounded-lg shadow-xl opacity-0 group-hover:opacity-100 pointer-events-none transition-opacity duration-150 whitespace-nowrap z-50">
        System Issues Detected • Server Unreachable • Click to retry
      </div>
    </button>
  );
};
