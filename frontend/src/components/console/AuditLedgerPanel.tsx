import React, { useState, useMemo } from 'react';
import {
  History,
  Search,
  CheckCircle2,
  AlertTriangle,
  XCircle,
  Eye,
  FileSpreadsheet,
} from 'lucide-react';
import { exportToCsv } from '../../utils/csvExport';

export interface AuditRecord {
  id: string;
  timestamp: string;
  fileName: string;
  fileUrl?: string;
  studentName: string;
  usn: string;
  collegeCode: string;
  sgpaListed: number;
  sgpaCalculated: number;
  arithmeticDiscrepancy: boolean;
  tamperingScore: number; // 0 to 100
  verdict: 'AUTHENTIC' | 'SUSPICIOUS' | 'FRAUDULENT';
  forensicReport?: string;
}

interface AuditLedgerPanelProps {
  records: AuditRecord[];
  onSelectRecord?: (record: AuditRecord) => void;
}

export const AuditLedgerPanel: React.FC<AuditLedgerPanelProps> = ({
  records,
  onSelectRecord,
}) => {
  const [searchTerm, setSearchTerm] = useState('');
  const [verdictFilter, setVerdictFilter] = useState<'ALL' | 'AUTHENTIC' | 'SUSPICIOUS' | 'FRAUDULENT'>('ALL');
  const [selectedRecordId, setSelectedRecordId] = useState<string | null>(null);

  // Filter records in memory with zero-lag
  const filteredRecords = useMemo(() => {
    return records.filter((rec) => {
      const matchSearch =
        !searchTerm.trim() ||
        rec.usn.toLowerCase().includes(searchTerm.toLowerCase()) ||
        rec.studentName.toLowerCase().includes(searchTerm.toLowerCase()) ||
        rec.collegeCode.toLowerCase().includes(searchTerm.toLowerCase()) ||
        rec.fileName.toLowerCase().includes(searchTerm.toLowerCase());

      const matchVerdict = verdictFilter === 'ALL' || rec.verdict === verdictFilter;

      return matchSearch && matchVerdict;
    });
  }, [records, searchTerm, verdictFilter]);

  const handleExportCsv = () => {
    if (filteredRecords.length === 0) return;
    const exportRows = filteredRecords.map((r) => ({
      id: r.id,
      timestamp: r.timestamp,
      usn: r.usn,
      studentName: r.studentName,
      collegeCode: r.collegeCode,
      sgpaListed: r.sgpaListed.toFixed(2),
      sgpaCalculated: r.sgpaCalculated.toFixed(2),
      delta: Math.abs(r.sgpaListed - r.sgpaCalculated).toFixed(2),
      arithmeticDiscrepancy: r.arithmeticDiscrepancy ? 'YES' : 'NO',
      tamperingScore: `${r.tamperingScore}%`,
      verdict: r.verdict,
      fileName: r.fileName,
    }));

    exportToCsv(
      `VTU_Marks_Card_Audit_Ledger_${new Date().toISOString().slice(0, 10)}.csv`,
      exportRows,
      [
        { key: 'id', label: 'Verification ID' },
        { key: 'timestamp', label: 'Timestamp (UTC)' },
        { key: 'usn', label: 'Student USN' },
        { key: 'studentName', label: 'Student Name' },
        { key: 'collegeCode', label: 'College' },
        { key: 'sgpaListed', label: 'Printed SGPA' },
        { key: 'sgpaCalculated', label: 'Calculated SGPA' },
        { key: 'delta', label: 'Arithmetic Delta' },
        { key: 'arithmeticDiscrepancy', label: 'Math Discrepancy' },
        { key: 'tamperingScore', label: 'Tamper Score' },
        { key: 'verdict', label: 'Verdict' },
        { key: 'fileName', label: 'Document File' },
      ]
    );
  };

  return (
    <div className="bg-white border border-slate-200 rounded-xl shadow-xs overflow-hidden flex flex-col h-full">
      {/* Panel Top Bar: Search, Verdict Filter, CSV Export */}
      <div className="p-4 border-b border-slate-200 bg-slate-50 flex flex-wrap items-center justify-between gap-3">
        <div className="flex items-center space-x-2">
          <History className="w-4 h-4 text-indigo-700" />
          <h3 className="font-bold text-sm text-slate-900">
            Institutional Audit Trail & Verification Ledger
          </h3>
          <span className="text-xs text-slate-500 font-mono bg-white px-2 py-0.5 rounded border border-slate-200">
            {filteredRecords.length} Records
          </span>
        </div>

        <div className="flex items-center space-x-2.5">
          {/* USN / Candidate Search */}
          <div className="relative">
            <Search className="w-3.5 h-3.5 text-slate-400 absolute left-2.5 top-1/2 -translate-y-1/2" />
            <input
              type="text"
              placeholder="Search USN (e.g. 1MS21CS045)..."
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
              className="pl-8 pr-3 py-1.5 text-xs rounded-lg border border-slate-200 bg-white text-slate-900 placeholder:text-slate-400 focus:outline-none focus:ring-1 focus:ring-indigo-500 w-52"
            />
          </div>

          {/* Verdict Filter */}
          <select
            value={verdictFilter}
            onChange={(e) => setVerdictFilter(e.target.value as any)}
            className="px-2.5 py-1.5 text-xs rounded-lg border border-slate-200 bg-white text-slate-800 font-medium focus:outline-none cursor-pointer"
          >
            <option value="ALL">All Verdicts</option>
            <option value="AUTHENTIC">Authentic Only</option>
            <option value="SUSPICIOUS">Suspicious Only</option>
            <option value="FRAUDULENT">Fraudulent Only</option>
          </select>

          {/* Export CSV */}
          <button
            type="button"
            onClick={handleExportCsv}
            disabled={filteredRecords.length === 0}
            className="inline-flex items-center space-x-1.5 px-3 py-1.5 rounded-lg border border-slate-200 bg-white hover:bg-slate-50 text-slate-700 text-xs font-semibold shadow-2xs transition-colors cursor-pointer disabled:opacity-50"
          >
            <FileSpreadsheet className="w-3.5 h-3.5 text-slate-500" />
            <span>Export CSV</span>
          </button>
        </div>
      </div>

      {/* Tabular Ledger View */}
      <div className="flex-1 overflow-x-auto">
        <table className="w-full text-left text-xs border-collapse">
          <thead>
            <tr className="border-b border-slate-200 bg-slate-50/80 text-[10px] font-semibold text-slate-600 uppercase tracking-wider">
              <th className="py-2.5 px-3">Timestamp</th>
              <th className="py-2.5 px-3">University Seat No (USN)</th>
              <th className="py-2.5 px-3">Student Name</th>
              <th className="py-2.5 px-3">College</th>
              <th className="py-2.5 px-3 text-center">Printed SGPA</th>
              <th className="py-2.5 px-3 text-center">Calculated SGPA</th>
              <th className="py-2.5 px-3 text-center">Delta (Δ)</th>
              <th className="py-2.5 px-3 text-center">Tamper Score</th>
              <th className="py-2.5 px-3">Verdict</th>
              <th className="py-2.5 px-3 text-right">Inspect</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-slate-100">
            {filteredRecords.length === 0 ? (
              <tr>
                <td colSpan={10} className="py-12 text-center text-slate-400">
                  <div className="text-xs">No audit verification records matching criteria.</div>
                </td>
              </tr>
            ) : (
              filteredRecords.map((rec) => {
                const delta = Math.abs(rec.sgpaListed - rec.sgpaCalculated);
                const isSelected = selectedRecordId === rec.id;

                const badge =
                  rec.verdict === 'AUTHENTIC'
                    ? { bg: 'bg-emerald-50 text-emerald-800 border-emerald-200', icon: CheckCircle2 }
                    : rec.verdict === 'SUSPICIOUS'
                    ? { bg: 'bg-amber-50 text-amber-800 border-amber-200', icon: AlertTriangle }
                    : { bg: 'bg-rose-50 text-rose-800 border-rose-200', icon: XCircle };

                return (
                  <tr
                    key={rec.id}
                    onClick={() => {
                      setSelectedRecordId(rec.id);
                      onSelectRecord && onSelectRecord(rec);
                    }}
                    className={`hover:bg-indigo-50/40 cursor-pointer transition-colors ${
                      isSelected ? 'bg-indigo-50/60' : ''
                    }`}
                  >
                    <td className="py-2.5 px-3 text-slate-500 font-mono text-[11px] whitespace-nowrap">
                      {new Date(rec.timestamp).toLocaleDateString()}{' '}
                      <span className="text-[10px] text-slate-400">
                        {new Date(rec.timestamp).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
                      </span>
                    </td>
                    <td className="py-2.5 px-3 font-mono font-bold text-indigo-900">{rec.usn}</td>
                    <td className="py-2.5 px-3 font-medium text-slate-900 truncate max-w-[140px]">
                      {rec.studentName}
                    </td>
                    <td className="py-2.5 px-3 text-slate-600 font-mono text-[11px]">
                      {rec.collegeCode}
                    </td>
                    <td className="py-2.5 px-3 text-center font-mono font-semibold text-slate-800">
                      {rec.sgpaListed.toFixed(2)}
                    </td>
                    <td className="py-2.5 px-3 text-center font-mono font-semibold text-slate-800">
                      {rec.sgpaCalculated.toFixed(2)}
                    </td>
                    <td className="py-2.5 px-3 text-center font-mono">
                      <span
                        className={`px-1.5 py-0.5 rounded text-[10px] font-bold ${
                          rec.arithmeticDiscrepancy
                            ? 'bg-rose-100 text-rose-800'
                            : 'bg-emerald-100 text-emerald-800'
                        }`}
                      >
                        {delta > 0.01 ? `+${delta.toFixed(2)}` : '0.00'}
                      </span>
                    </td>
                    <td className="py-2.5 px-3 text-center font-mono text-slate-700">
                      {rec.tamperingScore}%
                    </td>
                    <td className="py-2.5 px-3">
                      <span
                        className={`inline-flex items-center space-x-1 px-2 py-0.5 rounded-md border text-[10px] font-bold ${badge.bg}`}
                      >
                        <badge.icon className="w-3 h-3" />
                        <span>{rec.verdict}</span>
                      </span>
                    </td>
                    <td className="py-2.5 px-3 text-right">
                      <button
                        type="button"
                        className="p-1 rounded text-slate-400 hover:text-indigo-700 hover:bg-white transition-colors"
                        title="View Detailed Forensic Dossier"
                      >
                        <Eye className="w-4 h-4" />
                      </button>
                    </td>
                  </tr>
                );
              })
            )}
          </tbody>
        </table>
      </div>
    </div>
  );
};
