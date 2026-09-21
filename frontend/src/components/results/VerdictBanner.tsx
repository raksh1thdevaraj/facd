import React, { useState } from 'react';
import { ShieldCheck, AlertTriangle, ShieldAlert, Copy, Check } from 'lucide-react';
import { VerificationVerdict } from '../../types/report';

interface VerdictBannerProps {
  verdict: VerificationVerdict;
  authenticityScore: number;
  sha256Hash: string;
  processingTimeMs?: number;
  reportId: string;
}

export const VerdictBanner: React.FC<VerdictBannerProps> = ({
  verdict,
  authenticityScore,
  sha256Hash,
  processingTimeMs,
  reportId,
}) => {
  const [copied, setCopied] = useState<boolean>(false);

  const copyHash = () => {
    navigator.clipboard.writeText(sha256Hash);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  const getVerdictConfig = () => {
    switch (verdict) {
      case 'AUTHENTIC':
        return {
          title: 'CERTIFICATE VERIFIED AS AUTHENTIC',
          subtitle: 'Multi-engine forensics and visual AI detected zero indicators of tampering or forgery.',
          badgeColor: 'bg-emerald-500/20 text-emerald-300 border-emerald-500/40',
          gradient: 'from-emerald-950/60 via-slate-900 to-slate-950 border-emerald-600/40',
          iconBg: 'bg-emerald-600 text-white shadow-emerald-600/30',
          icon: ShieldCheck,
          textAccent: 'text-emerald-400',
        };
      case 'SUSPICIOUS':
        return {
          title: 'VERIFICATION RESULT: SUSPICIOUS',
          subtitle: 'Moderate anomalies identified in typography or texture compression. Manual inspection recommended.',
          badgeColor: 'bg-amber-500/20 text-amber-300 border-amber-500/40',
          gradient: 'from-amber-950/60 via-slate-900 to-slate-950 border-amber-600/40',
          iconBg: 'bg-amber-600 text-white shadow-amber-600/30',
          icon: AlertTriangle,
          textAccent: 'text-amber-400',
        };
      case 'MANIPULATED':
      default:
        return {
          title: 'TAMPERING & MANIPULATION DETECTED',
          subtitle: 'Critical forensic inconsistencies, copy-move splicing, or visual anomalies confirmed.',
          badgeColor: 'bg-rose-500/20 text-rose-300 border-rose-500/40',
          gradient: 'from-rose-950/60 via-slate-900 to-slate-950 border-rose-600/40',
          iconBg: 'bg-rose-600 text-white shadow-rose-600/30',
          icon: ShieldAlert,
          textAccent: 'text-rose-400',
        };
    }
  };

  const config = getVerdictConfig();
  const Icon = config.icon;

  return (
    <div className={`relative overflow-hidden rounded-2xl p-6 sm:p-8 border bg-gradient-to-br ${config.gradient} shadow-2xl space-y-6`}>
      <div className="flex flex-col md:flex-row items-start md:items-center justify-between gap-6">
        <div className="flex items-start space-x-4">
          <div className={`p-3.5 rounded-2xl ${config.iconBg} shadow-xl shrink-0 mt-0.5`}>
            <Icon className="w-8 h-8" />
          </div>
          <div>
            <div className="flex flex-wrap items-center gap-2 mb-1">
              <span className={`px-2.5 py-0.5 rounded-full text-xs font-bold uppercase tracking-wider border ${config.badgeColor}`}>
                {verdict}
              </span>
              <span className="text-xs font-mono text-slate-400">
                Report ID: {reportId.slice(0, 8)}...
              </span>
            </div>
            <h2 className={`text-xl sm:text-2xl font-extrabold tracking-tight ${config.textAccent}`}>
              {config.title}
            </h2>
            <p className="text-xs sm:text-sm text-slate-300 mt-1.5 max-w-2xl leading-relaxed">
              {config.subtitle}
            </p>
          </div>
        </div>

        {/* Quick Stat Pill */}
        <div className="flex md:flex-col items-center md:items-end justify-between w-full md:w-auto pt-4 md:pt-0 border-t md:border-t-0 border-slate-800 gap-2">
          <div className="text-left md:text-right">
            <span className="text-xs uppercase tracking-wider text-slate-400 font-semibold block">
              Confidence Score
            </span>
            <span className="text-2xl sm:text-3xl font-extrabold font-mono text-slate-100">
              {(authenticityScore * 100).toFixed(1)}%
            </span>
          </div>
          {processingTimeMs && (
            <span className="text-xs text-slate-500 font-mono">
              Latency: {processingTimeMs.toFixed(0)} ms
            </span>
          )}
        </div>
      </div>

      {/* SHA256 Fingerprint */}
      <div className="pt-4 border-t border-slate-800/80 flex flex-wrap items-center justify-between gap-3 text-xs text-slate-400">
        <div className="flex items-center space-x-2 min-w-0">
          <span className="font-semibold text-slate-300 shrink-0">SHA-256 Digest:</span>
          <code className="font-mono text-slate-400 bg-slate-950/80 px-2.5 py-1 rounded border border-slate-800 truncate max-w-xs sm:max-w-md">
            {sha256Hash}
          </code>
        </div>
        <button
          onClick={copyHash}
          className="inline-flex items-center space-x-1.5 text-xs text-slate-400 hover:text-slate-200 bg-slate-800/80 hover:bg-slate-800 px-2.5 py-1 rounded-lg border border-slate-700 transition-colors"
        >
          {copied ? (
            <>
              <Check className="w-3.5 h-3.5 text-emerald-400" />
              <span className="text-emerald-400">Copied</span>
            </>
          ) : (
            <>
              <Copy className="w-3.5 h-3.5" />
              <span>Copy Hash</span>
            </>
          )}
        </button>
      </div>
    </div>
  );
};
