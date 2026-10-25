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
      let res;
      try {
        res = await axios.get<HealthData>('/api/health', { timeout: 3500 });
      } catch (primaryErr) {
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

    const pollInterval = isOperational && !isInitializing ? 15000 : 3000;
    const intervalId = setInterval(fetchHealth, pollInterval);

    return () => {
      isMountedRef.current = false;
      clearInterval(intervalId);
    };
  }, [fetchHealth, isOperational, isInitializing]);

  if (isOperational && !isInitializing) {
    return (
      <button
        type="button"
        onClick={fetchHealth}
        className="group relative inline-flex items-center space-x-2 px-2.5 py-1 rounded-md bg-emerald-50 border border-emerald-200 text-emerald-800 text-xs font-mono font-medium transition-all hover:bg-emerald-100/70 cursor-pointer focus:outline-none"
        title={`Forensic Engine Online • ${latency}ms latency (Click to probe)`}
        aria-label="Engine status: Active"
      >
        <span className="relative flex h-2 w-2">
          <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-emerald-500 opacity-75" />
          <span className="relative inline-flex rounded-full h-2 w-2 bg-emerald-600" />
        </span>
        <span className="font-semibold tracking-tight text-[11px]">Forensic Engine: Online</span>
        <span className="text-[10px] text-emerald-600 font-mono hidden sm:inline">{latency}ms</span>
        {isChecking && <span className="text-[10px] text-emerald-600 animate-pulse">↻</span>}

        <div className="absolute top-full left-1/2 -translate-x-1/2 mt-1.5 px-2 py-1 bg-slate-900 border border-slate-700 text-slate-100 text-[10px] rounded shadow-lg opacity-0 group-hover:opacity-100 pointer-events-none transition-opacity duration-150 whitespace-nowrap z-50">
          Multimodal Gemini + Firestore: Operational ({latency}ms)
        </div>
      </button>
    );
  }

  if (isInitializing) {
    return (
      <button
        type="button"
        onClick={fetchHealth}
        className="group relative inline-flex items-center space-x-2 px-2.5 py-1 rounded-md bg-amber-50 border border-amber-200 text-amber-800 text-xs font-mono font-medium transition-all hover:bg-amber-100/70 cursor-pointer focus:outline-none"
        title="Engine Initializing • Connecting... (Click to retry)"
        aria-label="Engine status: Initializing"
      >
        <span className="relative flex h-2 w-2">
          <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-amber-400 opacity-75" />
          <span className="relative inline-flex rounded-full h-2 w-2 bg-amber-500" />
        </span>
        <span className="font-semibold tracking-tight text-[11px]">Connecting Engine...</span>

        <div className="absolute top-full left-1/2 -translate-x-1/2 mt-1.5 px-2 py-1 bg-slate-900 border border-slate-700 text-slate-100 text-[10px] rounded shadow-lg opacity-0 group-hover:opacity-100 pointer-events-none transition-opacity duration-150 whitespace-nowrap z-50">
          Backend initializing • Click to retry
        </div>
      </button>
    );
  }

  return (
    <button
      type="button"
      onClick={fetchHealth}
      className="group relative inline-flex items-center space-x-2 px-2.5 py-1 rounded-md bg-rose-50 border border-rose-200 text-rose-800 text-xs font-mono font-medium transition-all hover:bg-rose-100/70 cursor-pointer focus:outline-none"
      title="System Offline (Click to retry)"
      aria-label="Engine status: System Offline"
    >
      <span className="relative flex h-2 w-2">
        <span className="relative inline-flex rounded-full h-2 w-2 bg-rose-500" />
      </span>
      <span className="font-semibold tracking-tight text-[11px]">Engine Standby</span>
      {isChecking && <span className="text-[10px] text-rose-600 animate-pulse">↻</span>}

      <div className="absolute top-full left-1/2 -translate-x-1/2 mt-1.5 px-2 py-1 bg-slate-900 border border-slate-700 text-slate-100 text-[10px] rounded shadow-lg opacity-0 group-hover:opacity-100 pointer-events-none transition-opacity duration-150 whitespace-nowrap z-50">
        Backend offline • Click to retry
      </div>
    </button>
  );
};
