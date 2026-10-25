import React, { useEffect, useState, useCallback } from 'react';
import { Link } from 'react-router-dom';
import { certificateService } from '../services/certificateService';
import { CertificateListItem } from '../types/certificate';
import { exportToCsv } from '../utils/csvExport';
import {
  History,
  FileText,
  ChevronRight,
  Loader2,
  ChevronLeft,
  ArrowRight,
  Download,
  Search,
  Filter,
  Trash2,
} from 'lucide-react';

export const HistoryPage: React.FC = () => {
  const [items, setItems] = useState<CertificateListItem[]>([]);
  const [total, setTotal] = useState<number>(0);
  const [page, setPage] = useState<number>(1);
  const [limit] = useState<number>(10);
  const [loading, setLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);

  // Filter states
  const [searchTerm, setSearchTerm] = useState<string>('');
  const [verdictFilter, setVerdictFilter] = useState<string>('ALL');
  const [dateFrom, setDateFrom] = useState<string>('');
  const [dateTo, setDateTo] = useState<string>('');

  const fetchHistory = useCallback(async () => {
    try {
      setLoading(true);
      setError(null);
      const data = await certificateService.listCertificates(page, limit, {
        search: searchTerm || undefined,
        verdict: verdictFilter !== 'ALL' ? verdictFilter : undefined,
        date_from: dateFrom || undefined,
        date_to: dateTo || undefined,
      });
      setItems(data.items);
      setTotal(data.total);
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : 'Failed to fetch verification history');
    } finally {
      setLoading(false);
    }
  }, [page, limit, searchTerm, verdictFilter, dateFrom, dateTo]);

  useEffect(() => {
    fetchHistory();
  }, [fetchHistory]);

  const handleDelete = async (id: string) => {
    if (!window.confirm('Are you sure you want to remove this verification record?')) return;
    try {
      await certificateService.deleteCertificate(id);
      setItems((prev) => prev.filter((item) => item.id !== id));
      setTotal((prev) => Math.max(0, prev - 1));
    } catch {
      alert('Failed to delete certificate.');
    }
  };

  const handleExportCsv = () => {
    if (items.length === 0) return;
    const exportRows = items.map((item) => ({
      id: item.id,
      filename: item.original_filename,
      status: item.job_status || item.status,
      verdict: item.final_verdict || item.verdict || 'N/A',
      authenticity_score:
        (item.authenticity_score ?? item.overall_authenticity_score) != null
          ? `${(((item.authenticity_score ?? item.overall_authenticity_score) as number) * 100).toFixed(1)}%`
          : 'N/A',
      created_at: item.created_at,
    }));

    exportToCsv(`verification_history_${new Date().toISOString().slice(0, 10)}.csv`, exportRows, [
      { key: 'id', label: 'Certificate UUID' },
      { key: 'filename', label: 'Document Name' },
      { key: 'status', label: 'Job Status' },
      { key: 'verdict', label: 'Verdict' },
      { key: 'authenticity_score', label: 'Score %' },
      { key: 'created_at', label: 'Timestamp' },
    ]);
  };

  const totalPages = Math.max(1, Math.ceil(total / limit));

  const getStatusBadge = (status: string, verdict?: string) => {
    if (status === 'PROCESSING' || status === 'PENDING') {
      return (
        <span className="px-2.5 py-0.5 rounded-full text-xs font-medium bg-amber-500/10 text-amber-400 border border-amber-500/20">
          In Progress
        </span>
      );
    }
    if (status === 'FAILED') {
      return (
        <span className="px-2.5 py-0.5 rounded-full text-xs font-medium bg-rose-500/10 text-rose-400 border border-rose-500/20">
          Failed
        </span>
      );
    }
    if (verdict === 'AUTHENTIC') {
      return (
        <span className="px-2.5 py-0.5 rounded-full text-xs font-medium bg-emerald-500/10 text-emerald-400 border border-emerald-500/20">
          Authentic
        </span>
      );
    }
    if (verdict === 'MANIPULATED') {
      return (
        <span className="px-2.5 py-0.5 rounded-full text-xs font-medium bg-rose-500/10 text-rose-400 border border-rose-500/20">
          Manipulated
        </span>
      );
    }
    if (verdict === 'SUSPICIOUS') {
      return (
        <span className="px-2.5 py-0.5 rounded-full text-xs font-medium bg-amber-500/10 text-amber-400 border border-amber-500/20">
          Suspicious
        </span>
      );
    }
    return (
      <span className="px-2.5 py-0.5 rounded-full text-xs font-medium bg-slate-500/10 text-slate-300 border border-slate-500/20">
        Completed
      </span>
    );
  };

  return (
    <div className="max-w-6xl mx-auto space-y-6 pb-12">
      {/* Top Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div className="flex items-center space-x-3">
          <div className="p-2.5 rounded-xl bg-slate-800 text-emerald-400 border border-slate-700">
            <History className="w-6 h-6" />
          </div>
          <div>
            <h2 className="text-xl sm:text-2xl font-bold text-slate-100">Verification History</h2>
            <p className="text-xs sm:text-sm text-slate-400">
              Audit trail and forensic reports for all processed documents
            </p>
          </div>
        </div>

        <div className="flex flex-wrap items-center gap-2.5 self-start sm:self-auto">
          <button
            onClick={handleExportCsv}
            disabled={items.length === 0}
            className="inline-flex items-center space-x-1.5 px-3.5 py-2 rounded-xl bg-slate-800 hover:bg-slate-700 text-slate-200 text-xs sm:text-sm font-medium border border-slate-700 transition-colors disabled:opacity-50"
          >
            <Download className="w-4 h-4 text-cyan-400" />
            <span>Export to CSV</span>
          </button>

          <Link
            to="/"
            className="inline-flex items-center space-x-2 px-4 py-2 rounded-xl bg-indigo-900 hover:bg-indigo-800 text-white text-xs sm:text-sm font-semibold shadow-md transition-all"
          >
            <span>Inspection Console</span>
            <ArrowRight className="w-4 h-4" />
          </Link>
        </div>
      </div>

      {/* Multi-Criteria Filter Bar (CHIP ADM-02) */}
      <div className="glass-card rounded-2xl p-4 border border-slate-800 space-y-3">
        <div className="flex items-center space-x-2 text-xs font-semibold text-slate-400 uppercase tracking-wider">
          <Filter className="w-3.5 h-3.5 text-emerald-400" />
          <span>Filter & Search Records</span>
        </div>

        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-3 text-xs">
          {/* Search Box */}
          <div className="relative">
            <Search className="w-4 h-4 text-slate-500 absolute left-3 top-2.5" />
            <input
              type="text"
              placeholder="Search filename or ID..."
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
              className="w-full pl-9 pr-3 py-2 rounded-xl bg-slate-900/90 border border-slate-800 text-slate-200 focus:outline-none focus:border-emerald-500 placeholder-slate-500"
            />
          </div>

          {/* Verdict Filter */}
          <div>
            <select
              value={verdictFilter}
              onChange={(e) => setVerdictFilter(e.target.value)}
              className="w-full px-3 py-2 rounded-xl bg-slate-900/90 border border-slate-800 text-slate-200 focus:outline-none focus:border-emerald-500"
            >
              <option value="ALL">All Verdicts</option>
              <option value="AUTHENTIC">Authentic Only</option>
              <option value="SUSPICIOUS">Suspicious Only</option>
              <option value="MANIPULATED">Manipulated Only</option>
            </select>
          </div>

          {/* Date From */}
          <div>
            <input
              type="date"
              value={dateFrom}
              onChange={(e) => setDateFrom(e.target.value)}
              title="From date"
              className="w-full px-3 py-2 rounded-xl bg-slate-900/90 border border-slate-800 text-slate-200 focus:outline-none focus:border-emerald-500"
            />
          </div>

          {/* Date To */}
          <div>
            <input
              type="date"
              value={dateTo}
              onChange={(e) => setDateTo(e.target.value)}
              title="To date"
              className="w-full px-3 py-2 rounded-xl bg-slate-900/90 border border-slate-800 text-slate-200 focus:outline-none focus:border-emerald-500"
            />
          </div>
        </div>
      </div>

      {loading ? (
        <div className="min-h-[300px] flex flex-col items-center justify-center space-y-3">
          <Loader2 className="w-8 h-8 animate-spin text-emerald-400" />
          <span className="text-xs text-slate-400">Loading verification records...</span>
        </div>
      ) : error ? (
        <div className="p-6 rounded-2xl bg-rose-950/20 border border-rose-800/50 text-center text-sm text-rose-300">
          {error}
        </div>
      ) : items.length === 0 ? (
        <div className="glass-card rounded-2xl p-12 border border-slate-800 text-center space-y-4">
          <FileText className="w-12 h-12 text-slate-600 mx-auto" />
          <h4 className="text-base font-semibold text-slate-300">No Matching Verification Records</h4>
          <p className="text-xs text-slate-400 max-w-sm mx-auto">
            Try adjusting your search criteria or date filters, or upload a new certificate document.
          </p>
          <Link
            to="/upload"
            className="inline-block px-4 py-2 rounded-xl bg-emerald-600 text-white text-xs font-semibold hover:bg-emerald-500 transition-colors"
          >
            Upload Certificate
          </Link>
        </div>
      ) : (
        <div className="glass-card rounded-2xl border border-slate-800 overflow-hidden shadow-xl">
          <div className="overflow-x-auto">
            <table className="w-full text-left text-xs sm:text-sm">
              <thead className="bg-slate-900/80 border-b border-slate-800 text-slate-400 uppercase text-[11px] tracking-wider font-semibold">
                <tr>
                  <th className="py-3.5 px-4">Document</th>
                  <th className="py-3.5 px-4">Status / Verdict</th>
                  <th className="py-3.5 px-4">Authenticity</th>
                  <th className="py-3.5 px-4 hidden md:table-cell">Timestamp</th>
                  <th className="py-3.5 px-4 text-right">Actions</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-800/60 text-slate-300">
                {items.map((item) => (
                  <tr key={item.id} className="hover:bg-slate-800/30 transition-colors">
                    <td className="py-4 px-4 font-medium flex items-center space-x-2.5">
                      <FileText className="w-4 h-4 text-slate-400 shrink-0" />
                      <span className="truncate max-w-[180px] sm:max-w-xs">{item.original_filename}</span>
                    </td>
                    <td className="py-4 px-4">
                      {getStatusBadge(
                        item.job_status || item.status || 'COMPLETED',
                        item.final_verdict || item.verdict || undefined
                      )}
                    </td>
                    <td className="py-4 px-4 font-mono font-medium">
                      {(item.authenticity_score ?? item.overall_authenticity_score) != null
                        ? `${(((item.authenticity_score ?? item.overall_authenticity_score) as number) * 100).toFixed(1)}%`
                        : '—'}
                    </td>
                    <td className="py-4 px-4 text-slate-400 text-xs hidden md:table-cell">
                      {new Date(item.created_at).toLocaleString()}
                    </td>
                    <td className="py-4 px-4 text-right">
                      <div className="flex items-center justify-end space-x-3">
                        <Link
                          to={`/results/${item.report_id || item.id}`}
                          className="inline-flex items-center space-x-1 text-xs text-emerald-400 hover:text-emerald-300 font-semibold"
                        >
                          <span>View Dossier</span>
                          <ChevronRight className="w-3.5 h-3.5" />
                        </Link>
                        <button
                          onClick={() => handleDelete(item.id)}
                          title="Remove record"
                          className="text-slate-500 hover:text-rose-400 transition-colors"
                        >
                          <Trash2 className="w-3.5 h-3.5" />
                        </button>
                      </div>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>

          {/* Pagination */}
          {totalPages > 1 && (
            <div className="p-4 border-t border-slate-800 flex items-center justify-between text-xs text-slate-400 bg-slate-900/40">
              <span>
                Page {page} of {totalPages} ({total} total records)
              </span>
              <div className="flex items-center space-x-2">
                <button
                  onClick={() => setPage((p) => Math.max(1, p - 1))}
                  disabled={page <= 1}
                  className="p-1.5 rounded-lg bg-slate-800 hover:bg-slate-700 disabled:opacity-40 transition-colors"
                >
                  <ChevronLeft className="w-4 h-4" />
                </button>
                <button
                  onClick={() => setPage((p) => Math.min(totalPages, p + 1))}
                  disabled={page >= totalPages}
                  className="p-1.5 rounded-lg bg-slate-800 hover:bg-slate-700 disabled:opacity-40 transition-colors"
                >
                  <ChevronRight className="w-4 h-4" />
                </button>
              </div>
            </div>
          )}
        </div>
      )}
    </div>
  );
};
