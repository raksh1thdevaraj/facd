import React, { useEffect, useState } from 'react';
import axios from 'axios';

interface HealthData {
  status: string;
  timestamp?: string;
  db_connected?: boolean;
  model_engine?: string;
  latency_ms?: number;
}

export const SystemHealthBadge: React.FC = () => {
  const [isOperational, setIsOperational] = useState<boolean>(true);
  const [latency, setLatency] = useState<number>(24);

  useEffect(() => {
    let isMounted = true;

    const fetchHealth = async () => {
      const startTime = performance.now();
      try {
        const res = await axios.get<HealthData>('/api/health');
        const endLatency = Math.round(performance.now() - startTime);
        if (isMounted) {
          const healthy = res.data.status === 'healthy' || res.data.status === 'ok';
          setIsOperational(healthy && res.data.db_connected !== false);
          setLatency(res.data.latency_ms || endLatency || 18);
        }
      } catch {
        if (isMounted) {
          setIsOperational(false);
        }
      }
    };

    fetchHealth();
    const interval = setInterval(fetchHealth, 15000);
    return () => {
      isMounted = false;
      clearInterval(interval);
    };
  }, []);

  if (isOperational) {
    return (
      <div
        className="group relative inline-flex items-center space-x-2 px-3 py-1.5 rounded-full bg-emerald-950/60 border border-emerald-500/30 text-emerald-400 text-xs font-mono font-medium shadow-sm transition-all cursor-pointer"
        title={`Operational • ${latency}ms`}
      >
        <span className="relative flex h-2 w-2">
          <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-[#10B981] opacity-75" />
          <span className="relative inline-flex rounded-full h-2 w-2 bg-[#10B981]" />
        </span>
        <span className="font-semibold tracking-wide">Engine Active</span>

        {/* Hover Tooltip displaying latency */}
        <div className="absolute top-full left-1/2 -translate-x-1/2 mt-2 px-2.5 py-1 bg-slate-900 border border-slate-700 text-slate-200 text-[11px] rounded-lg shadow-xl opacity-0 group-hover:opacity-100 pointer-events-none transition-opacity duration-150 whitespace-nowrap z-50">
          Operational • {latency}ms
        </div>
      </div>
    );
  }

  return (
    <div
      className="group relative inline-flex items-center space-x-2 px-3 py-1.5 rounded-full bg-rose-950/60 border border-[#EF4444]/40 text-[#EF4444] text-xs font-mono font-medium shadow-sm transition-all cursor-pointer"
      title="System Issues Detected"
    >
      <span className="relative flex h-2 w-2">
        <span className="relative inline-flex rounded-full h-2 w-2 bg-[#EF4444]" />
      </span>
      <span className="font-semibold tracking-wide">System Issues Detected</span>

      {/* Hover Tooltip */}
      <div className="absolute top-full left-1/2 -translate-x-1/2 mt-2 px-2.5 py-1 bg-slate-900 border border-rose-800 text-rose-300 text-[11px] rounded-lg shadow-xl opacity-0 group-hover:opacity-100 pointer-events-none transition-opacity duration-150 whitespace-nowrap z-50">
        System Issues Detected • Server Unreachable
      </div>
    </div>
  );
};


