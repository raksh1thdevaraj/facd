import React from 'react';
import { Layers, ShieldCheck, AlertCircle } from 'lucide-react';
import { SubsystemScoreItem } from '../../types/report';

interface SubsystemScoresProps {
  subsystems: SubsystemScoreItem[] | Record<string, SubsystemScoreItem>;
}

export const SubsystemScores: React.FC<SubsystemScoresProps> = ({ subsystems }) => {
  const subsystemEntries: [string, SubsystemScoreItem][] = Array.isArray(subsystems)
    ? subsystems.map((item, idx) => [item.name || `subsystem_${idx}`, item])
    : Object.entries(subsystems);


  const getStatusBadge = (score: number) => {
    if (score >= 0.75) {
      return {
        label: 'Passed',
        classes: 'bg-emerald-500/10 text-emerald-400 border-emerald-500/20',
      };
    }
    if (score >= 0.45) {
      return {
        label: 'Marginal',
        classes: 'bg-amber-500/10 text-amber-400 border-amber-500/20',
      };
    }
    return {
      label: 'Anomaly',
      classes: 'bg-rose-500/10 text-rose-400 border-rose-500/20',
    };
  };

  const formatName = (key: string, name?: string) => {
    if (name) return name;
    return key
      .replace(/_/g, ' ')
      .replace(/\b\w/g, (c) => c.toUpperCase());
  };

  return (
    <div className="glass-card rounded-2xl p-6 border border-slate-800 shadow-xl space-y-6">
      <div className="flex items-center space-x-3 border-b border-slate-800 pb-4">
        <div className="p-2 rounded-xl bg-slate-800 text-teal-400 border border-slate-700">
          <Layers className="w-5 h-5" />
        </div>
        <div>
          <h3 className="text-base font-bold text-slate-100">Subsystem Score Breakdown</h3>
          <p className="text-xs text-slate-400">Independent analytical pipeline metrics fused into final verdict</p>
        </div>
      </div>

      <div className="space-y-4">
        {subsystemEntries.map(([key, item]) => {
          const scorePercent = Math.min(100, Math.max(0, item.score * 100));
          const badge = getStatusBadge(item.score);

          return (
            <div key={key} className="p-3.5 rounded-xl bg-slate-900/40 border border-slate-800/80 space-y-2">
              <div className="flex items-center justify-between">
                <div>
                  <span className="text-sm font-semibold text-slate-200">
                    {formatName(key, item.name)}
                  </span>
                  {item.weight !== undefined && (
                    <span className="text-xs text-slate-500 ml-2 font-mono">
                      (Weight: {(item.weight * 100).toFixed(0)}%)
                    </span>
                  )}
                </div>

                <div className="flex items-center space-x-2.5">
                  <span className={`text-[11px] px-2 py-0.5 rounded font-medium border ${badge.classes}`}>
                    {badge.label}
                  </span>
                  <span className="text-sm font-mono font-bold text-slate-100">
                    {scorePercent.toFixed(1)}%
                  </span>
                </div>
              </div>

              {/* Progress bar */}
              <div className="w-full bg-slate-800/80 rounded-full h-2 overflow-hidden">
                <div
                  className={`h-full rounded-full transition-all duration-700 ${
                    item.score >= 0.75
                      ? 'bg-emerald-500'
                      : item.score >= 0.45
                      ? 'bg-amber-500'
                      : 'bg-rose-500'
                  }`}
                  style={{ width: `${scorePercent}%` }}
                />
              </div>

              {item.notes && (
                <div className="flex items-center space-x-1.5 text-xs text-slate-400 pt-1">
                  {item.score >= 0.75 ? (
                    <ShieldCheck className="w-3.5 h-3.5 text-emerald-400 shrink-0" />
                  ) : (
                    <AlertCircle className="w-3.5 h-3.5 text-amber-400 shrink-0" />
                  )}
                  <span className="truncate">{item.notes}</span>
                </div>
              )}
            </div>
          );
        })}
      </div>
    </div>
  );
};
