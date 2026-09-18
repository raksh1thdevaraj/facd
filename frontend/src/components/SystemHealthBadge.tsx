import React, { useEffect, useState } from 'react';
import { checkHealth } from '../services/api';
import { HealthCheckResponse } from '../types';
import { Activity, CheckCircle2, AlertTriangle } from 'lucide-react';

export const SystemHealthBadge: React.FC = () => {
  const [health, setHealth] = useState<HealthCheckResponse | null>(null);
  const [loading, setLoading] = useState<boolean>(true);
  const [error, setError] = useState<boolean>(false);

  useEffect(() => {
    let isMounted = true;
    const fetchHealth = async () => {
      try {
        const data = await checkHealth();
        if (isMounted) {
          setHealth(data);
          setError(false);
          setLoading(false);
        }
      } catch (err) {
        if (isMounted) {
          setError(true);
          setLoading(false);
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

  if (loading) {
    return (
      <div className="flex items-center space-x-2 text-xs text-slate-400 bg-slate-800/60 px-3 py-1.5 rounded-full border border-slate-700/50">
        <Activity className="w-3.5 h-3.5 animate-spin text-emerald-400" />
        <span>Checking Services...</span>
      </div>
    );
  }

  if (error || !health || health.status !== 'ok') {
    return (
      <div className="flex items-center space-x-2 text-xs text-amber-300 bg-amber-950/40 px-3 py-1.5 rounded-full border border-amber-800/50">
        <AlertTriangle className="w-3.5 h-3.5 text-amber-400" />
        <span>Degraded Service</span>
      </div>
    );
  }

  return (
    <div className="flex items-center space-x-2 text-xs text-emerald-300 bg-emerald-950/40 px-3 py-1.5 rounded-full border border-emerald-800/50">
      <CheckCircle2 className="w-3.5 h-3.5 text-emerald-400" />
      <span>System Operational (v{health.version})</span>
    </div>
  );
};
