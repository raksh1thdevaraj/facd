import React, { useState, useEffect } from 'react';
import apiClient from '../../services/api';
import {
  ShieldAlert,
  AlertTriangle,
  CheckCircle2,
  RefreshCw,
  Search,
  GraduationCap,
  Award,
} from 'lucide-react';

interface ScanItem {
  id: string;
  filename: string;
  certificate_type: string;
  final_status: string;
  verdict_badge?: string;
  confidence_score: number;
  qr_detected?: boolean;
  domain_valid?: boolean;
  tampering_detected?: boolean;
  created_at?: string;
  ip_address?: string;
  latency_ms?: number;
  timestamp?: string;
}

export const VerificationScansTab: React.FC = () => {
  const [scans, setScans] = useState<ScanItem[]>([]);
  const [searchTerm, setSearchTerm] = useState<string>('');
  const [statusFilter, setStatusFilter] = useState<string>('ALL');
  const [typeFilter, setTypeFilter] = useState<string>('ALL');
  const [loading, setLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);

  const fetchScans = async () => {
    try {
      setLoading(true);
      setError(null);
      let url = '/admin/scans?limit=50';
      if (statusFilter !== 'ALL') url += `&status_filter=${statusFilter}`;
      if (typeFilter !== 'ALL') url += `&type_filter=${typeFilter}`;

      const res = await apiClient.get<ScanItem[]>(url);
      if (Array.isArray(res.data)) {
        setScans(res.data);
      }
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : 'Failed to load verification scans');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchScans();
  }, [statusFilter, typeFilter]);

  const filteredScans = scans.filter((s) => {
    if (!searchTerm) return true;
    const term = searchTerm.toLowerCase();
    return s.filename.toLowerCase().includes(term) || s.id.toLowerCase().includes(term);
  });

  return (
    <div className="space-y-6">
      {/* Top Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h3 className="text-xl font-bold text-white">Verification Scans Ledger</h3>
          <p className="text-xs text-slate-400 mt-0.5">
            Real-time multi-modal verification history for marks cards and course certificates
          </p>
        </div>

        <button
          onClick={fetchScans}
          disabled={loading}
          className="inline-flex items-center space-x-2 px-4 py-2 rounded-xl bg-slate-800 hover:bg-slate-700 text-slate-200 text-xs font-semibold border border-slate-700 transition-colors self-start sm:self-center cursor-pointer"
        >
          <RefreshCw className={`w-3.5 h-3.5 ${loading ? 'animate-spin text-emerald-400' : ''}`} />
          <span>Refresh Ledger</span>
        </button>
      </div>

      {/* Filter and Search Bar */}
      <div className="p-4 rounded-2xl bg-slate-900/60 border border-slate-800 flex flex-col md:flex-row items-center justify-between gap-4">
        <div className="flex flex-wrap items-center gap-2 w-full md:w-auto">
          {/* Status Filter */}
          <div className="flex items-center space-x-1 bg-slate-950 p-1 rounded-xl border border-slate-800 text-xs">
            {['ALL', 'VERIFIED', 'SUSPICIOUS', 'REJECTED'].map((st) => (
              <button
                key={st}
                onClick={() => setStatusFilter(st)}
                className={`px-3 py-1.5 rounded-lg font-semibold transition-all ${
                  statusFilter === st
                    ? st === 'VERIFIED'
                      ? 'bg-emerald-500 text-slate-950'
                      : st === 'REJECTED'
                      ? 'bg-rose-500 text-white'
                      : st === 'SUSPICIOUS'
                      ? 'bg-amber-500 text-slate-950'
                      : 'bg-slate-800 text-white'
                    : 'text-slate-400 hover:text-white'
                }`}
              >
                {st}
              </button>
            ))}
          </div>

          {/* Type Filter */}
          <div className="flex items-center space-x-1 bg-slate-950 p-1 rounded-xl border border-slate-800 text-xs">
            <button
              onClick={() => setTypeFilter('ALL')}
              className={`px-3 py-1.5 rounded-lg font-semibold transition-all ${
                typeFilter === 'ALL' ? 'bg-slate-800 text-white' : 'text-slate-400 hover:text-white'
              }`}
            >
              All Types
            </button>
            <button
              onClick={() => setTypeFilter('marks_card')}
              className={`px-3 py-1.5 rounded-lg font-semibold transition-all ${
                typeFilter === 'marks_card'
                  ? 'bg-emerald-500/20 text-emerald-400 border border-emerald-500/30'
                  : 'text-slate-400 hover:text-white'
              }`}
            >
              Marks Cards
            </button>
            <button
              onClick={() => setTypeFilter('course_certificate')}
              className={`px-3 py-1.5 rounded-lg font-semibold transition-all ${
                typeFilter === 'course_certificate'
                  ? 'bg-teal-500/20 text-teal-400 border border-teal-500/30'
                  : 'text-slate-400 hover:text-white'
              }`}
            >
              Course Certs
            </button>
          </div>
        </div>

        {/* Search Input */}
        <div className="relative w-full md:w-64">
          <Search className="w-4 h-4 text-slate-500 absolute left-3 top-2.5" />
          <input
            type="text"
            placeholder="Search filename or scan ID..."
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
            className="w-full pl-9 pr-3 py-2 rounded-xl bg-slate-950 border border-slate-800 text-xs text-white placeholder-slate-500 focus:outline-none focus:border-emerald-500"
          />
        </div>
      </div>

      {/* Scans Table */}
      {loading && scans.length === 0 ? (
        <div className="min-h-[300px] rounded-2xl bg-slate-900/40 border border-slate-800 flex items-center justify-center">
          <RefreshCw className="w-6 h-6 animate-spin text-emerald-400" />
        </div>
      ) : error ? (
        <div className="p-4 rounded-xl bg-rose-950/20 border border-rose-800/60 text-xs text-rose-300">
          {error}
        </div>
      ) : filteredScans.length === 0 ? (
        <div className="p-12 text-center text-xs text-slate-500 rounded-2xl bg-slate-900/30 border border-slate-800">
          No verification scans match the selected criteria.
        </div>
      ) : (
        <div className="rounded-2xl bg-slate-900/60 border border-slate-800 overflow-hidden">
          <div className="overflow-x-auto">
            <table className="w-full text-left text-xs">
              <thead className="bg-slate-950 border-b border-slate-800 text-[11px] font-bold text-slate-400 uppercase tracking-wider">
                <tr>
                  <th className="py-3 px-4">Document / Filename</th>
                  <th className="py-3 px-4">Type</th>
                  <th className="py-3 px-4">Verdict Status</th>
                  <th className="py-3 px-4">Confidence</th>
                  <th className="py-3 px-4">Latency</th>
                  <th className="py-3 px-4">Timestamp</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-800/60 text-slate-300">
                {filteredScans.map((scan) => {
                  const isVerified = scan.final_status === 'VERIFIED';
                  const isSuspicious = scan.final_status === 'SUSPICIOUS';

                  return (
                    <tr key={scan.id} className="hover:bg-slate-800/30 transition-colors">
                      <td className="py-3 px-4">
                        <div className="flex items-center space-x-2.5">
                          <div
                            className={`p-1.5 rounded-lg ${
                              isVerified
                                ? 'bg-emerald-500/10 text-emerald-400'
                                : isSuspicious
                                ? 'bg-amber-500/10 text-amber-400'
                                : 'bg-rose-500/10 text-rose-400'
                            }`}
                          >
                            {isVerified ? (
                              <CheckCircle2 className="w-4 h-4" />
                            ) : isSuspicious ? (
                              <AlertTriangle className="w-4 h-4" />
                            ) : (
                              <ShieldAlert className="w-4 h-4" />
                            )}
                          </div>
                          <div>
                            <span className="font-bold text-white block truncate max-w-[220px]">
                              {scan.filename}
                            </span>
                            <span className="font-mono text-[10px] text-slate-500">
                              ID: {scan.id.slice(0, 8)}
                            </span>
                          </div>
                        </div>
                      </td>

                      <td className="py-3 px-4">
                        <span className="inline-flex items-center space-x-1 px-2 py-0.5 rounded text-[10px] font-semibold bg-slate-800 text-slate-300 border border-slate-700">
                          {scan.certificate_type === 'marks_card' ? (
                            <>
                              <GraduationCap className="w-3 h-3 text-emerald-400" />
                              <span>Marks Card</span>
                            </>
                          ) : (
                            <>
                              <Award className="w-3 h-3 text-teal-400" />
                              <span>Course Cert</span>
                            </>
                          )}
                        </span>
                      </td>

                      <td className="py-3 px-4">
                        <span
                          className={`text-[10px] font-bold px-2 py-0.5 rounded-full border ${
                            isVerified
                              ? 'bg-emerald-500/10 text-emerald-400 border-emerald-500/30'
                              : isSuspicious
                              ? 'bg-amber-500/10 text-amber-400 border-amber-500/30'
                              : 'bg-rose-500/10 text-rose-400 border-rose-500/30'
                          }`}
                        >
                          {scan.final_status}
                        </span>
                      </td>

                      <td className="py-3 px-4 font-mono font-medium">
                        {(scan.confidence_score * 100).toFixed(1)}%
                      </td>

                      <td className="py-3 px-4 font-mono text-slate-400">
                        {scan.latency_ms} ms
                      </td>

                      <td className="py-3 px-4 text-slate-400 text-[11px] whitespace-nowrap">
                        {scan.timestamp ? scan.timestamp.replace('T', ' ').slice(0, 19) : 'Just now'}
                      </td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>
        </div>
      )}
    </div>
  );
};
