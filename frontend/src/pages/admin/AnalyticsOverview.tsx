import React, { useEffect, useState } from 'react';
import { adminService } from '../../services/adminService';
import { AnalyticsSummaryResponse } from '../../types/admin';
import { MetricCard } from '../../components/admin/MetricCard';
import {
  FileCheck,
  ShieldAlert,
  CheckCircle2,
  AlertTriangle,
  Clock,
  Loader2,
  RefreshCw,
  BarChart3,
  PieChart,
} from 'lucide-react';

export const AnalyticsOverview: React.FC = () => {
  const [data, setData] = useState<AnalyticsSummaryResponse | null>(null);
  const [loading, setLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);

  const fetchAnalytics = async (bypassCache = false) => {
    try {
      setLoading(true);
      setError(null);
      const res = await adminService.getAnalyticsSummary(bypassCache);
      setData(res);
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : 'Failed to load analytics summary');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchAnalytics();
  }, []);

  if (loading && !data) {
    return (
      <div className="min-h-[400px] flex flex-col items-center justify-center space-y-3">
        <Loader2 className="w-8 h-8 animate-spin text-emerald-400" />
        <span className="text-xs text-slate-400">Aggregating real-time fraud metrics...</span>
      </div>
    );
  }

  if (error || !data) {
    return (
      <div className="p-6 rounded-2xl bg-rose-950/20 border border-rose-800/60 text-center text-sm text-rose-300">
        {error || 'Unable to load analytics summary.'}
      </div>
    );
  }

  const maxDailyVolume = Math.max(1, ...data.daily_trends.map((d) => d.total));

  return (
    <div className="space-y-8">
      {/* Top Header & Refresh */}
      <div className="flex items-center justify-between">
        <div>
          <h3 className="text-lg font-bold text-slate-100">Enterprise Fraud Intelligence</h3>
          <p className="text-xs text-slate-400">High-throughput operational KPIs and anomaly trends</p>
        </div>

        <button
          onClick={() => fetchAnalytics(true)}
          disabled={loading}
          className="inline-flex items-center space-x-1.5 px-3 py-1.5 rounded-lg bg-slate-800 hover:bg-slate-700 text-slate-300 text-xs font-medium border border-slate-700 transition-colors disabled:opacity-50"
        >
          <RefreshCw className={`w-3.5 h-3.5 ${loading ? 'animate-spin text-emerald-400' : ''}`} />
          <span>Refresh Data</span>
        </button>
      </div>

      {/* KPI Cards Grid */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-5 gap-4">
        <MetricCard
          title="Total Processed"
          value={data.total_certificates_verified}
          subtitle="Processed submissions"
          icon={FileCheck}
          accentColor="cyan"
          trend="+12.4%"
          isPositiveTrend={true}
        />
        <MetricCard
          title="Authentic Verified"
          value={data.total_authentic_count}
          subtitle="Passed all checks"
          icon={CheckCircle2}
          accentColor="emerald"
        />
        <MetricCard
          title="Fraud Rate"
          value={`${data.overall_fraud_rate_percentage}%`}
          subtitle="Confirmed tampering"
          icon={ShieldAlert}
          accentColor="rose"
          trend={data.overall_fraud_rate_percentage > 10 ? 'High' : 'Normal'}
          isPositiveTrend={data.overall_fraud_rate_percentage <= 10}
        />
        <MetricCard
          title="Flagged Review"
          value={data.total_suspicious_count}
          subtitle="Marginal confidence"
          icon={AlertTriangle}
          accentColor="amber"
        />
        <MetricCard
          title="Avg Latency"
          value={`${data.average_pipeline_latency_seconds}s`}
          subtitle="End-to-end pipeline"
          icon={Clock}
          accentColor="purple"
        />
      </div>

      {/* 30-Day Verification Trends Chart (Responsive SVG Bar Visualization) */}
      <div className="glass-card rounded-2xl p-6 border border-slate-800 shadow-xl space-y-4">
        <div className="flex items-center justify-between border-b border-slate-800 pb-3">
          <div className="flex items-center space-x-2">
            <BarChart3 className="w-5 h-5 text-cyan-400" />
            <h4 className="text-sm font-bold text-slate-100">30-Day Verification Throughput & Fraud Detection</h4>
          </div>
          <div className="flex items-center space-x-4 text-xs text-slate-400">
            <div className="flex items-center space-x-1.5">
              <span className="w-2.5 h-2.5 rounded-sm bg-emerald-500"></span>
              <span>Authentic</span>
            </div>
            <div className="flex items-center space-x-1.5">
              <span className="w-2.5 h-2.5 rounded-sm bg-rose-500"></span>
              <span>Manipulated</span>
            </div>
          </div>
        </div>

        {/* Bar Graph container */}
        <div className="h-44 w-full flex items-end gap-1.5 pt-6 pb-2 px-1">
          {data.daily_trends.map((item) => {
            const heightPercent = Math.max(8, (item.total / maxDailyVolume) * 100);
            const fraudHeightPercent = item.total > 0 ? (item.fraud / item.total) * 100 : 0;

            return (
              <div
                key={item.date}
                title={`${item.date}: ${item.total} total (${item.fraud} fraud)`}
                className="flex-1 flex flex-col justify-end h-full group relative cursor-pointer"
              >
                <div
                  className="w-full bg-emerald-500/80 group-hover:bg-emerald-400 rounded-t transition-all relative overflow-hidden"
                  style={{ height: `${heightPercent}%` }}
                >
                  {item.fraud > 0 && (
                    <div
                      className="w-full bg-rose-500 absolute bottom-0 rounded-b"
                      style={{ height: `${fraudHeightPercent}%` }}
                    />
                  )}
                </div>

                {/* Tooltip on hover */}
                <div className="hidden group-hover:block absolute -top-10 left-1/2 -translate-x-1/2 bg-slate-900 text-slate-100 border border-slate-700 px-2 py-1 rounded text-[10px] whitespace-nowrap z-20 shadow-lg">
                  {item.date.slice(5)}: {item.total} docs ({item.fraud} fraud)
                </div>
              </div>
            );
          })}
        </div>
        <div className="flex justify-between text-[11px] text-slate-500 pt-1">
          <span>{data.daily_trends[0]?.date || '30 days ago'}</span>
          <span>Last 30 Days Trend</span>
          <span>{data.daily_trends[data.daily_trends.length - 1]?.date || 'Today'}</span>
        </div>
      </div>

      {/* Two Columns: Verdict Distribution & Common Tampering Modalities */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Verdict Distribution */}
        <div className="glass-card rounded-2xl p-6 border border-slate-800 shadow-xl space-y-4">
          <div className="flex items-center space-x-2 border-b border-slate-800 pb-3">
            <PieChart className="w-5 h-5 text-teal-400" />
            <h4 className="text-sm font-bold text-slate-100">Verdict Proportions</h4>
          </div>

          <div className="space-y-4 pt-2">
            <div>
              <div className="flex justify-between text-xs mb-1.5">
                <span className="text-emerald-400 font-medium">Authentic Certificates</span>
                <span className="font-mono text-slate-300">
                  {data.total_authentic_count} (
                  {data.total_certificates_verified > 0
                    ? ((data.total_authentic_count / data.total_certificates_verified) * 100).toFixed(1)
                    : 0}
                  %)
                </span>
              </div>
              <div className="w-full bg-slate-800 h-2.5 rounded-full overflow-hidden">
                <div
                  className="bg-emerald-500 h-full rounded-full"
                  style={{
                    width: `${
                      data.total_certificates_verified > 0
                        ? (data.total_authentic_count / data.total_certificates_verified) * 100
                        : 0
                    }%`,
                  }}
                />
              </div>
            </div>

            <div>
              <div className="flex justify-between text-xs mb-1.5">
                <span className="text-rose-400 font-medium">Manipulated / Forged</span>
                <span className="font-mono text-slate-300">
                  {data.total_manipulated_count} (
                  {data.total_certificates_verified > 0
                    ? ((data.total_manipulated_count / data.total_certificates_verified) * 100).toFixed(1)
                    : 0}
                  %)
                </span>
              </div>
              <div className="w-full bg-slate-800 h-2.5 rounded-full overflow-hidden">
                <div
                  className="bg-rose-500 h-full rounded-full"
                  style={{
                    width: `${
                      data.total_certificates_verified > 0
                        ? (data.total_manipulated_count / data.total_certificates_verified) * 100
                        : 0
                    }%`,
                  }}
                />
              </div>
            </div>

            <div>
              <div className="flex justify-between text-xs mb-1.5">
                <span className="text-amber-400 font-medium">Suspicious (Review Needed)</span>
                <span className="font-mono text-slate-300">
                  {data.total_suspicious_count} (
                  {data.total_certificates_verified > 0
                    ? ((data.total_suspicious_count / data.total_certificates_verified) * 100).toFixed(1)
                    : 0}
                  %)
                </span>
              </div>
              <div className="w-full bg-slate-800 h-2.5 rounded-full overflow-hidden">
                <div
                  className="bg-amber-500 h-full rounded-full"
                  style={{
                    width: `${
                      data.total_certificates_verified > 0
                        ? (data.total_suspicious_count / data.total_certificates_verified) * 100
                        : 0
                    }%`,
                  }}
                />
              </div>
            </div>
          </div>
        </div>

        {/* Common Tampering Modalities */}
        <div className="glass-card rounded-2xl p-6 border border-slate-800 shadow-xl space-y-4">
          <div className="flex items-center space-x-2 border-b border-slate-800 pb-3">
            <ShieldAlert className="w-5 h-5 text-rose-400" />
            <h4 className="text-sm font-bold text-slate-100">Top Manipulation Modalities</h4>
          </div>

          <div className="space-y-3 pt-2">
            {data.manipulation_modalities.map((item) => (
              <div key={item.modality} className="p-3 rounded-xl bg-slate-900/60 border border-slate-800/80 space-y-1.5">
                <div className="flex items-center justify-between text-xs">
                  <span className="font-semibold text-slate-200">{item.modality}</span>
                  <span className="font-mono font-bold text-rose-400">{item.percentage}%</span>
                </div>
                <div className="w-full bg-slate-800 h-1.5 rounded-full overflow-hidden">
                  <div className="bg-rose-500 h-full rounded-full" style={{ width: `${item.percentage}%` }} />
                </div>
              </div>
            ))}
          </div>
        </div>
      </div>
    </div>
  );
};
