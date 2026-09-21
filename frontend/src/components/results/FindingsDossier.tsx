import React, { useState } from 'react';
import { AlertOctagon, AlertTriangle, Info, ShieldAlert, ChevronDown, ChevronUp, FileText } from 'lucide-react';
import { FindingBullet, FindingSeverity } from '../../types/report';

interface FindingsDossierProps {
  findings: FindingBullet[];
}

const SEVERITY_CONFIG: Record<
  FindingSeverity,
  {
    label: string;
    icon: React.ElementType;
    badgeBg: string;
    badgeText: string;
    badgeBorder: string;
    cardBorder: string;
  }
> = {
  CRITICAL: {
    label: 'Critical Anomaly',
    icon: AlertOctagon,
    badgeBg: 'bg-rose-500/20',
    badgeText: 'text-rose-400',
    badgeBorder: 'border-rose-500/40',
    cardBorder: 'border-rose-900/50',
  },
  MAJOR: {
    label: 'Major Anomaly',
    icon: ShieldAlert,
    badgeBg: 'bg-amber-500/20',
    badgeText: 'text-amber-400',
    badgeBorder: 'border-amber-500/40',
    cardBorder: 'border-amber-900/50',
  },
  WARNING: {
    label: 'Warning',
    icon: AlertTriangle,
    badgeBg: 'bg-yellow-500/20',
    badgeText: 'text-yellow-400',
    badgeBorder: 'border-yellow-500/40',
    cardBorder: 'border-yellow-900/50',
  },
  INFO: {
    label: 'Informational',
    icon: Info,
    badgeBg: 'bg-cyan-500/20',
    badgeText: 'text-cyan-400',
    badgeBorder: 'border-cyan-500/40',
    cardBorder: 'border-cyan-900/50',
  },
};

export const FindingsDossier: React.FC<FindingsDossierProps> = ({ findings }) => {
  const [filter, setFilter] = useState<FindingSeverity | 'ALL'>('ALL');
  const [expandedIndex, setExpandedIndex] = useState<number | null>(null);

  const counts: Record<FindingSeverity, number> = {
    CRITICAL: findings.filter((f) => f.severity === 'CRITICAL').length,
    MAJOR: findings.filter((f) => f.severity === 'MAJOR').length,
    WARNING: findings.filter((f) => f.severity === 'WARNING').length,
    INFO: findings.filter((f) => f.severity === 'INFO').length,
  };

  const filteredFindings =
    filter === 'ALL' ? findings : findings.filter((f) => f.severity === filter);

  const toggleExpand = (index: number) => {
    setExpandedIndex(expandedIndex === index ? null : index);
  };

  return (
    <div className="glass-card rounded-2xl p-6 border border-slate-800 shadow-xl space-y-6">
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 border-b border-slate-800 pb-4">
        <div className="flex items-center space-x-3">
          <div className="p-2 rounded-xl bg-slate-800 text-amber-400 border border-slate-700">
            <FileText className="w-5 h-5" />
          </div>
          <div>
            <h3 className="text-base font-bold text-slate-100">Findings & Evidence Dossier</h3>
            <p className="text-xs text-slate-400">
              {findings.length} findings categorized across all pipeline subsystems
            </p>
          </div>
        </div>

        {/* Severity Filter Tabs */}
        <div className="flex flex-wrap items-center gap-1.5 text-xs">
          <button
            onClick={() => setFilter('ALL')}
            className={`px-2.5 py-1 rounded-lg border transition-colors ${
              filter === 'ALL'
                ? 'bg-slate-700 text-white border-slate-600'
                : 'bg-slate-900 text-slate-400 border-slate-800 hover:text-slate-200'
            }`}
          >
            All ({findings.length})
          </button>
          {(['CRITICAL', 'MAJOR', 'WARNING', 'INFO'] as FindingSeverity[]).map((sev) => {
            const count = counts[sev];
            const cfg = SEVERITY_CONFIG[sev];
            return (
              <button
                key={sev}
                onClick={() => setFilter(sev)}
                className={`flex items-center space-x-1.5 px-2.5 py-1 rounded-lg border transition-colors ${
                  filter === sev
                    ? `${cfg.badgeBg} ${cfg.badgeText} ${cfg.badgeBorder} font-semibold`
                    : 'bg-slate-900 text-slate-400 border-slate-800 hover:text-slate-200'
                }`}
              >
                <span>{sev}</span>
                <span className="font-mono text-[10px] px-1 rounded bg-slate-800">{count}</span>
              </button>
            );
          })}
        </div>
      </div>

      {filteredFindings.length === 0 ? (
        <div className="text-center py-8 text-slate-500 text-sm">
          No findings matching the selected severity level.
        </div>
      ) : (
        <div className="space-y-3">
          {filteredFindings.map((item, idx) => {
            const cfg = SEVERITY_CONFIG[item.severity] || SEVERITY_CONFIG.INFO;
            const Icon = cfg.icon;
            const isExpanded = expandedIndex === idx;

            return (
              <div
                key={idx}
                className={`rounded-xl border bg-slate-900/50 transition-all ${cfg.cardBorder} overflow-hidden`}
              >
                <div
                  onClick={() => toggleExpand(idx)}
                  className="flex items-center justify-between p-4 cursor-pointer hover:bg-slate-800/30 transition-colors"
                >
                  <div className="flex items-start space-x-3 min-w-0 pr-4">
                    <div className={`p-1.5 rounded-lg shrink-0 ${cfg.badgeBg} ${cfg.badgeText}`}>
                      <Icon className="w-4 h-4" />
                    </div>
                    <div className="min-w-0">
                      <div className="flex items-center space-x-2">
                        <span
                          className={`text-[10px] uppercase font-bold px-2 py-0.5 rounded border ${cfg.badgeBg} ${cfg.badgeText} ${cfg.badgeBorder}`}
                        >
                          {item.severity}
                        </span>
                        {item.module && (
                          <span className="text-xs text-slate-400 font-mono">[{item.module}]</span>
                        )}
                        {item.code && (
                          <span className="text-[11px] text-slate-500 font-mono">#{item.code}</span>
                        )}
                      </div>
                      <p className="text-sm font-medium text-slate-200 mt-1 line-clamp-2">
                        {item.description}
                      </p>
                    </div>
                  </div>

                  <div className="shrink-0 text-slate-500">
                    {isExpanded ? <ChevronUp className="w-4 h-4" /> : <ChevronDown className="w-4 h-4" />}
                  </div>
                </div>

                {isExpanded && (
                  <div className="px-4 pb-4 pt-1 text-xs text-slate-400 border-t border-slate-800/60 bg-slate-950/40 space-y-2">
                    <div>
                      <span className="text-slate-500 font-semibold uppercase text-[10px]">Detail:</span>
                      <p className="mt-0.5 text-slate-300 leading-relaxed">{item.description}</p>
                    </div>
                    {item.location && (
                      <div>
                        <span className="text-slate-500 font-semibold uppercase text-[10px]">
                          Detected Location:
                        </span>
                        <code className="block mt-0.5 p-2 rounded bg-slate-900 border border-slate-800 font-mono text-emerald-400">
                          {JSON.stringify(item.location)}
                        </code>
                      </div>
                    )}
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
