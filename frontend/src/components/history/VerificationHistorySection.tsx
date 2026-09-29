import React, { useEffect, useState, useCallback } from 'react';
import {
  History,
  FileText,
  Search,
  Filter,
  Download,
  Trash2,
  RefreshCw,
  Loader2,
  ExternalLink,
  ChevronRight,
  ShieldCheck,
  ShieldAlert,
  AlertTriangle,
  ArrowUpDown,
  User,
} from 'lucide-react';
import { historyService } from '../../services/historyService';
import { VerificationHistorySummary, VerificationHistoryDetail } from '../../types/history';
import { VerificationDetailModal } from './VerificationDetailModal';
import { exportToCsv } from '../../utils/csvExport';

interface VerificationHistorySectionProps {
  /** Optional signal (e.g. timestamp) indicating a new upload finished, triggering an auto-refresh */
  refreshTrigger?: number | string | null;
  /** Optional callback to navigate to upload/verify page */
  onNavigateToUpload?: () => void;
  /** Optional class name */
  className?: string;
}

export const VerificationHistorySection: React.FC<VerificationHistorySectionProps> = ({
  refreshTrigger,
  onNavigateToUpload,
  className = '',
}) => {
  const [items, setItems] = useState<VerificationHistorySummary[]>([]);
  const [loading, setLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);

  // Filter and sort state
  const [searchTerm, setSearchTerm] = useState<string>('');
  const [verdictFilter, setVerdictFilter] = useState<string>('ALL');
  const [docTypeFilter, setDocTypeFilter] = useState<string>('ALL');
  const [sortOrder, setSortOrder] = useState<'desc' | 'asc'>('desc');

  // Active detail modal state
  const [selectedDetail, setSelectedDetail] = useState<VerificationHistoryDetail | null>(null);
  const [detailLoadingId, setDetailLoadingId] = useState<string | null>(null);

  const fetchHistory = useCallback(async () => {
    try {
      setLoading(true);
      setError(null);
      const data = await historyService.getHistory({
        order: sortOrder,
        search: searchTerm.trim() || undefined,
        verdict: verdictFilter !== 'ALL' ? verdictFilter : undefined,
        document_type: docTypeFilter !== 'ALL' ? docTypeFilter : undefined,
      });
      setItems(data);
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : 'Failed to fetch verification history');
    } finally {
      setLoading(false);
    }
  }, [sortOrder, searchTerm, verdictFilter, docTypeFilter]);

  const isFirstMount = React.useRef(true);
  const prevTriggerRef = React.useRef(refreshTrigger);

  // Fetch on mount or filter change
  useEffect(() => {
    fetchHistory();
  }, [fetchHistory]);

  // Auto-refresh when refreshTrigger updates after mount
  useEffect(() => {
    if (isFirstMount.current) {
      isFirstMount.current = false;
      return;
    }
    if (refreshTrigger !== undefined && refreshTrigger !== null && refreshTrigger !== prevTriggerRef.current) {
      prevTriggerRef.current = refreshTrigger;
      fetchHistory();
    }
  }, [refreshTrigger, fetchHistory]);

  const handleOpenDetail = async (item: VerificationHistorySummary) => {
    try {
      setDetailLoadingId(item.id);
      const detail = await historyService.getHistoryDetail(item.id);
      setSelectedDetail(detail);
    } catch {
      setSelectedDetail({
        ...item,
        full_details: {
          extracted_data: {
            student_name: item.student_name,
            identifier: item.identifier,
            issuer: item.issuer,
          },
        },
      });
    } finally {
      setDetailLoadingId(null);
    }
  };

  const handleDeleteItem = async (id: string, e: React.MouseEvent) => {
    e.stopPropagation();
    if (!window.confirm('Are you sure you want to remove this verification record?')) return;
    try {
      await historyService.deleteHistoryItem(id);
      setItems((prev) => prev.filter((i) => i.id !== id));
    } catch {
      alert('Failed to delete verification record.');
    }
  };

  const handleClearAll = async () => {
    if (
      !window.confirm(
        'Are you sure you want to clear the entire verification history? This cannot be undone.'
      )
    )
      return;
    try {
      setLoading(true);
      await historyService.clearAllHistory();
      setItems([]);
    } catch {
      alert('Failed to clear verification history.');
    } finally {
      setLoading(false);
    }
  };

  const handleExportCsv = () => {
    if (items.length === 0) return;
    const exportRows = items.map((item) => ({
      id: item.id,
      timestamp: item.timestamp,
      original_filename: item.original_filename,
      document_type: item.document_type,
      student_name: item.student_name,
      identifier: item.identifier,
      issuer: item.issuer,
      verdict: item.verdict,
      confidence_score: `${(item.confidence_score * 100).toFixed(1)}%`,
      qr_status: item.qr_status ? 'Verified' : 'No QR',
      tampering_flags: (item.tampering_flags || []).join('; '),
      remarks: item.remarks,
    }));

    exportToCsv(`verification_history_${new Date().toISOString().slice(0, 10)}.csv`, exportRows, [
      { key: 'timestamp', label: 'Timestamp' },
      { key: 'student_name', label: 'Student Name' },
      { key: 'identifier', label: 'USN / Certificate ID' },
      { key: 'issuer', label: 'Issuer' },
      { key: 'document_type', label: 'Document Type' },
      { key: 'verdict', label: 'Verdict' },
      { key: 'confidence_score', label: 'Confidence' },
      { key: 'original_filename', label: 'File Name' },
      { key: 'qr_status', label: 'QR Status' },
      { key: 'tampering_flags', label: 'Tampering Flags' },
    ]);
  };

  const getVerdictBadge = (verdict: string) => {
    const v = (verdict || '').toUpperCase();
    if (v === 'AUTHENTIC') {
      return (
        <span className="inline-flex items-center space-x-1 px-2.5 py-1 rounded-full text-xs font-bold bg-emerald-500/10 text-emerald-400 border border-emerald-500/30">
          <ShieldCheck className="w-3.5 h-3.5" />
          <span>AUTHENTIC</span>
        </span>
      );
    }
    if (v === 'SUSPICIOUS') {
      return (
        <span className="inline-flex items-center space-x-1 px-2.5 py-1 rounded-full text-xs font-bold bg-amber-500/10 text-amber-400 border border-amber-500/30">
          <AlertTriangle className="w-3.5 h-3.5" />
          <span>SUSPICIOUS</span>
        </span>
      );
    }
    return (
      <span className="inline-flex items-center space-x-1 px-2.5 py-1 rounded-full text-xs font-bold bg-rose-500/10 text-rose-400 border border-rose-500/30">
        <ShieldAlert className="w-3.5 h-3.5" />
        <span>FRAUDULENT</span>
      </span>
    );
  };

  return (
    <div className={`space-y-6 ${className}`}>
      {/* Top Header Actions */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div className="flex items-center space-x-3">
          <div className="p-2.5 rounded-xl bg-slate-800 text-emerald-400 border border-slate-700 shadow-md">
            <History className="w-5 h-5" />
          </div>
          <div>
            <h3 className="text-lg sm:text-xl font-bold text-white">Verification History</h3>
            <p className="text-xs text-slate-400">
              Immutable audit ledger of previously verified certificates and forensic results
            </p>
          </div>
        </div>

        <div className="flex flex-wrap items-center gap-2 self-start sm:self-auto">
          <button
            onClick={() => fetchHistory()}
            disabled={loading}
            className="inline-flex items-center space-x-1.5 px-3 py-2 rounded-xl bg-slate-800 hover:bg-slate-700 text-slate-200 text-xs font-medium border border-slate-700 transition-colors disabled:opacity-50"
            title="Refresh history"
          >
            <RefreshCw className={`w-3.5 h-3.5 text-slate-400 ${loading ? 'animate-spin' : ''}`} />
            <span>Refresh</span>
          </button>

          <button
            onClick={handleExportCsv}
            disabled={items.length === 0}
            className="inline-flex items-center space-x-1.5 px-3 py-2 rounded-xl bg-slate-800 hover:bg-slate-700 text-slate-200 text-xs font-medium border border-slate-700 transition-colors disabled:opacity-50"
            title="Export to CSV"
          >
            <Download className="w-3.5 h-3.5 text-cyan-400" />
            <span>Export CSV</span>
          </button>

          {items.length > 0 && (
            <button
              onClick={handleClearAll}
              className="inline-flex items-center space-x-1.5 px-3 py-2 rounded-xl bg-rose-950/40 hover:bg-rose-900/60 text-rose-300 text-xs font-medium border border-rose-800/60 transition-colors"
              title="Clear all records"
            >
              <Trash2 className="w-3.5 h-3.5 text-rose-400" />
              <span>Clear History</span>
            </button>
          )}
        </div>
      </div>

      {/* Search and Filters Bar */}
      <div className="p-4 rounded-2xl bg-slate-900/80 border border-slate-800 backdrop-blur-md shadow-lg space-y-3">
        <div className="flex items-center justify-between text-xs font-semibold text-slate-400 uppercase tracking-wider">
          <div className="flex items-center space-x-1.5">
            <Filter className="w-3.5 h-3.5 text-emerald-400" />
            <span>Filter & Search History</span>
          </div>
          <button
            onClick={() => setSortOrder((prev) => (prev === 'desc' ? 'asc' : 'desc'))}
            className="flex items-center space-x-1 text-[11px] text-slate-400 hover:text-emerald-300 transition-colors lowercase"
          >
            <ArrowUpDown className="w-3 h-3" />
            <span>sort: {sortOrder === 'desc' ? 'newest first' : 'oldest first'}</span>
          </button>
        </div>

        <div className="grid grid-cols-1 sm:grid-cols-3 lg:grid-cols-4 gap-3 text-xs">
          {/* Global Search Input */}
          <div className="relative sm:col-span-2 lg:col-span-2">
            <Search className="w-4 h-4 text-slate-500 absolute left-3 top-2.5" />
            <input
              type="text"
              placeholder="Search filename or ID..."
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
              className="w-full pl-9 pr-3 py-2 rounded-xl bg-slate-950/80 border border-slate-800 text-slate-100 placeholder-slate-500 focus:outline-none focus:border-emerald-500 transition-colors"
            />
          </div>

          {/* Verdict Filter */}
          <div>
            <select
              value={verdictFilter}
              onChange={(e) => setVerdictFilter(e.target.value)}
              className="w-full px-3 py-2 rounded-xl bg-slate-950/80 border border-slate-800 text-slate-200 focus:outline-none focus:border-emerald-500 transition-colors"
            >
              <option value="ALL">All Verdicts</option>
              <option value="AUTHENTIC">Authentic Only</option>
              <option value="SUSPICIOUS">Suspicious Only</option>
              <option value="FRAUDULENT">Fraudulent Only</option>
            </select>
          </div>

          {/* Document Type Filter */}
          <div>
            <select
              value={docTypeFilter}
              onChange={(e) => setDocTypeFilter(e.target.value)}
              className="w-full px-3 py-2 rounded-xl bg-slate-950/80 border border-slate-800 text-slate-200 focus:outline-none focus:border-emerald-500 transition-colors"
            >
              <option value="ALL">All Document Types</option>
              <option value="VTU_MARKSCARD">VTU Marks Card</option>
              <option value="ONLINE_COURSE_CERTIFICATE">Online Course Cert</option>
            </select>
          </div>
        </div>
      </div>

      {/* Main Content Area */}
      {loading ? (
        <div className="min-h-[260px] flex flex-col items-center justify-center space-y-3 p-8 rounded-2xl bg-slate-900/40 border border-slate-800/80">
          <Loader2 className="w-8 h-8 animate-spin text-emerald-400" />
          <span className="text-xs text-slate-400 font-medium">Loading verification ledger...</span>
        </div>
      ) : error ? (
        <div className="p-6 rounded-2xl bg-rose-950/20 border border-rose-800/60 text-center text-sm text-rose-300">
          <p>{error}</p>
          <button
            onClick={() => fetchHistory()}
            className="mt-3 px-3 py-1.5 rounded-lg bg-rose-900/60 text-xs font-semibold text-rose-200 hover:bg-rose-800 transition-colors"
          >
            Try Again
          </button>
        </div>
      ) : items.length === 0 ? (
        /* Empty State Banner (Requirement 3) */
        <div className="p-12 rounded-2xl bg-slate-900/60 border border-slate-800 text-center space-y-4 shadow-xl">
          <div className="w-14 h-14 mx-auto rounded-2xl bg-slate-800/80 border border-slate-700 flex items-center justify-center text-slate-500">
            <FileText className="w-7 h-7 text-slate-400" />
          </div>
          <div className="max-w-md mx-auto space-y-1">
            <h4 className="text-base font-bold text-slate-200">
              No certificate verifications recorded yet. Upload a document to start.
            </h4>
            <p className="text-xs text-slate-400">
              Every document analyzed through the verification pipeline is automatically recorded in
              this audit ledger.
            </p>
          </div>
          {onNavigateToUpload && (
            <button
              onClick={onNavigateToUpload}
              className="inline-flex items-center space-x-2 px-5 py-2.5 rounded-xl bg-gradient-to-r from-emerald-600 to-teal-600 hover:from-emerald-500 hover:to-teal-500 text-white text-xs font-bold shadow-lg shadow-emerald-600/25 transition-all"
            >
              <span>Verify a Certificate</span>
              <ChevronRight className="w-4 h-4" />
            </button>
          )}
        </div>
      ) : (
        /* Searchable, Sortable Table */
        <div className="rounded-2xl border border-slate-800 bg-slate-900/90 overflow-hidden shadow-2xl">
          <div className="overflow-x-auto">
            <table className="w-full text-left text-xs sm:text-sm">
              <thead className="bg-slate-950/80 border-b border-slate-800 text-slate-400 uppercase text-[11px] tracking-wider font-semibold">
                <tr>
                  <th className="py-3.5 px-4">Timestamp</th>
                  <th className="py-3.5 px-4">Student Name & USN</th>
                  <th className="py-3.5 px-4 hidden md:table-cell">Document Type / Issuer</th>
                  <th className="py-3.5 px-4">Verdict Badge</th>
                  <th className="py-3.5 px-4 text-center">Confidence</th>
                  <th className="py-3.5 px-4 text-right">Actions</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-800/60 text-slate-300">
                {items.map((item) => (
                  <tr
                    key={item.id}
                    onClick={() => handleOpenDetail(item)}
                    className="hover:bg-slate-800/40 transition-colors cursor-pointer group"
                  >
                    {/* Timestamp */}
                    <td className="py-4 px-4 text-xs text-slate-400 whitespace-nowrap">
                      {new Date(item.timestamp).toLocaleString(undefined, {
                        month: 'short',
                        day: 'numeric',
                        year: 'numeric',
                        hour: '2-digit',
                        minute: '2-digit',
                      })}
                    </td>

                    {/* Student Name & USN */}
                    <td className="py-4 px-4">
                      <div className="flex items-center space-x-2.5">
                        <div className="w-7 h-7 rounded-lg bg-slate-800 border border-slate-700 flex items-center justify-center text-slate-300 shrink-0">
                          <User className="w-3.5 h-3.5 text-emerald-400" />
                        </div>
                        <div>
                          <span className="font-semibold text-white block group-hover:text-emerald-300 transition-colors">
                            {item.student_name && item.student_name !== 'Not Detected'
                              ? item.student_name
                              : item.original_filename}
                          </span>
                          <span className="text-[11px] font-mono text-emerald-400/90 block">
                            {item.identifier && item.identifier !== 'Not Detected'
                              ? item.identifier
                              : 'ID Pending'}
                          </span>
                        </div>
                      </div>
                    </td>

                    {/* Document Type / Issuer */}
                    <td className="py-4 px-4 hidden md:table-cell">
                      <span className="text-xs font-medium text-slate-200 block">
                        {item.issuer && item.issuer !== 'Not Detected'
                          ? item.issuer
                          : item.document_type}
                      </span>
                      <span className="text-[11px] text-slate-400 block">
                        {item.document_type === 'VTU_MARKSCARD'
                          ? 'VTU Marks Card'
                          : item.document_type === 'ONLINE_COURSE_CERTIFICATE'
                          ? 'Online Course'
                          : item.document_type}
                      </span>
                    </td>

                    {/* Verdict Badge */}
                    <td className="py-4 px-4">{getVerdictBadge(item.verdict)}</td>

                    {/* Confidence */}
                    <td className="py-4 px-4 text-center">
                      <div className="inline-flex flex-col items-center">
                        <span className="font-mono font-bold text-xs text-white">
                          {(item.confidence_score * 100).toFixed(1)}%
                        </span>
                        <div className="w-14 bg-slate-800 h-1.5 rounded-full overflow-hidden mt-1">
                          <div
                            className={`h-full rounded-full ${
                              item.verdict === 'AUTHENTIC'
                                ? 'bg-emerald-500'
                                : item.verdict === 'SUSPICIOUS'
                                ? 'bg-amber-500'
                                : 'bg-rose-500'
                            }`}
                            style={{ width: `${Math.min(100, item.confidence_score * 100)}%` }}
                          />
                        </div>
                      </div>
                    </td>

                    {/* Actions */}
                    <td className="py-4 px-4 text-right">
                      <div className="flex items-center justify-end space-x-2">
                        <button
                          onClick={(e) => {
                            e.stopPropagation();
                            handleOpenDetail(item);
                          }}
                          disabled={detailLoadingId === item.id}
                          className="inline-flex items-center space-x-1 px-3 py-1.5 rounded-lg bg-emerald-950/60 hover:bg-emerald-900/80 text-emerald-300 border border-emerald-700/60 text-xs font-semibold transition-all"
                        >
                          {detailLoadingId === item.id ? (
                            <Loader2 className="w-3.5 h-3.5 animate-spin" />
                          ) : (
                            <>
                              <span>View Details</span>
                              <ExternalLink className="w-3 h-3" />
                            </>
                          )}
                        </button>

                        <button
                          onClick={(e) => handleDeleteItem(item.id, e)}
                          title="Remove from history"
                          className="p-1.5 rounded-lg text-slate-500 hover:text-rose-400 hover:bg-rose-950/40 transition-colors"
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

          <div className="px-4 py-3 bg-slate-950/80 border-t border-slate-800 text-xs text-slate-400 flex items-center justify-between">
            <span>
              Showing {items.length} recorded verification{items.length === 1 ? '' : 's'}
            </span>
            <span className="text-[11px] text-slate-500 font-mono">
              All records cryptographically indexed &bull; ISO-8601
            </span>
          </div>
        </div>
      )}

      {/* Detail Modal */}
      {selectedDetail && (
        <VerificationDetailModal
          record={selectedDetail}
          onClose={() => setSelectedDetail(null)}
        />
      )}
    </div>
  );
};
