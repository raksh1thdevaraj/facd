import React from 'react';
import {
  X,
  ShieldCheck,
  ShieldAlert,
  AlertTriangle,
  QrCode,
  FileText,
  User,
  CheckCircle2,
  XCircle,
  Copy,
  Printer,
  ExternalLink,
} from 'lucide-react';
import { VerificationHistoryDetail } from '../../types/history';

interface VerificationDetailModalProps {
  record: VerificationHistoryDetail;
  onClose: () => void;
}

export const VerificationDetailModal: React.FC<VerificationDetailModalProps> = ({
  record,
  onClose,
}) => {
  const full = record.full_details || {};
  const extracted =
    full.extracted_data || full.extracted_fields || {
      student_name: record.student_name,
      identifier: record.identifier,
      issuer: record.issuer,
    };
  const rag = full.rag_validation || {};
  const qr = full.qr_verification || {};
  const tamperingFlags = record.tampering_flags || [];

  const getVerdictBadge = (verdict: string) => {
    const v = (verdict || '').toUpperCase();
    if (v === 'AUTHENTIC') {
      return (
        <span className="inline-flex items-center space-x-1 px-3 py-1 rounded-full text-xs font-bold bg-emerald-500/10 text-emerald-400 border border-emerald-500/30">
          <ShieldCheck className="w-3.5 h-3.5" />
          <span>AUTHENTIC</span>
        </span>
      );
    }
    if (v === 'SUSPICIOUS') {
      return (
        <span className="inline-flex items-center space-x-1 px-3 py-1 rounded-full text-xs font-bold bg-amber-500/10 text-amber-400 border border-amber-500/30">
          <AlertTriangle className="w-3.5 h-3.5" />
          <span>SUSPICIOUS</span>
        </span>
      );
    }
    return (
      <span className="inline-flex items-center space-x-1 px-3 py-1 rounded-full text-xs font-bold bg-rose-500/10 text-rose-400 border border-rose-500/30">
        <ShieldAlert className="w-3.5 h-3.5" />
        <span>FRAUDULENT</span>
      </span>
    );
  };

  const copyAsJson = () => {
    navigator.clipboard.writeText(JSON.stringify(record, null, 2));
    alert('Verification record copied to clipboard as JSON!');
  };

  const handlePrint = () => {
    window.print();
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/80 backdrop-blur-md animate-in fade-in duration-200">
      <div className="relative w-full max-w-4xl max-h-[90vh] bg-slate-900 border border-slate-700/80 rounded-2xl shadow-2xl overflow-hidden flex flex-col text-slate-100">
        {/* Modal Header */}
        <div className="px-6 py-4 border-b border-slate-800 flex items-center justify-between bg-slate-950/70">
          <div className="flex items-center space-x-3">
            <div className="p-2 rounded-xl bg-slate-800 border border-slate-700 text-emerald-400">
              <FileText className="w-5 h-5" />
            </div>
            <div>
              <div className="flex items-center space-x-2.5">
                <h3 className="text-base sm:text-lg font-bold text-white truncate max-w-md">
                  {record.original_filename}
                </h3>
                {getVerdictBadge(record.verdict)}
              </div>
              <p className="text-xs text-slate-400 mt-0.5">
                Verified on {new Date(record.timestamp).toLocaleString()} &bull; ID:{' '}
                <span className="font-mono text-slate-300">{record.id.slice(0, 8)}...</span>
              </p>
            </div>
          </div>

          <div className="flex items-center space-x-2">
            <button
              onClick={copyAsJson}
              title="Copy Record JSON"
              className="p-2 rounded-xl bg-slate-800 hover:bg-slate-700 text-slate-300 transition-colors border border-slate-700"
            >
              <Copy className="w-4 h-4" />
            </button>
            <button
              onClick={handlePrint}
              title="Print Dossier"
              className="p-2 rounded-xl bg-slate-800 hover:bg-slate-700 text-slate-300 transition-colors border border-slate-700"
            >
              <Printer className="w-4 h-4" />
            </button>
            <button
              onClick={onClose}
              title="Close modal"
              className="p-2 rounded-xl bg-slate-800 hover:bg-rose-900/60 text-slate-400 hover:text-rose-200 transition-colors border border-slate-700"
            >
              <X className="w-4 h-4" />
            </button>
          </div>
        </div>

        {/* Modal Body */}
        <div className="p-6 overflow-y-auto space-y-6 text-sm">
          {/* Top Banner KPI Grid */}
          <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
            <div className="p-3.5 rounded-xl bg-slate-800/60 border border-slate-700/60">
              <span className="text-[11px] font-semibold text-slate-400 uppercase tracking-wider block">
                Confidence
              </span>
              <span className="text-lg font-black text-white font-mono">
                {(record.confidence_score * 100).toFixed(1)}%
              </span>
            </div>

            <div className="p-3.5 rounded-xl bg-slate-800/60 border border-slate-700/60">
              <span className="text-[11px] font-semibold text-slate-400 uppercase tracking-wider block">
                Document Type
              </span>
              <span className="text-xs font-bold text-slate-200 truncate block mt-1">
                {record.document_type === 'VTU_MARKSCARD'
                  ? 'VTU Marks Card'
                  : record.document_type === 'ONLINE_COURSE_CERTIFICATE'
                  ? 'Online Certificate'
                  : record.document_type}
              </span>
            </div>

            <div className="p-3.5 rounded-xl bg-slate-800/60 border border-slate-700/60">
              <span className="text-[11px] font-semibold text-slate-400 uppercase tracking-wider block">
                QR Verification
              </span>
              <span
                className={`text-xs font-bold inline-flex items-center space-x-1 mt-1 ${
                  record.qr_status ? 'text-emerald-400' : 'text-slate-400'
                }`}
              >
                {record.qr_status ? (
                  <>
                    <CheckCircle2 className="w-3.5 h-3.5" />
                    <span>Verified</span>
                  </>
                ) : (
                  <>
                    <XCircle className="w-3.5 h-3.5 text-slate-500" />
                    <span>Not Found</span>
                  </>
                )}
              </span>
            </div>

            <div className="p-3.5 rounded-xl bg-slate-800/60 border border-slate-700/60">
              <span className="text-[11px] font-semibold text-slate-400 uppercase tracking-wider block">
                Tampering Flags
              </span>
              <span
                className={`text-xs font-bold mt-1 block ${
                  tamperingFlags.length > 0 ? 'text-rose-400' : 'text-emerald-400'
                }`}
              >
                {tamperingFlags.length > 0 ? `${tamperingFlags.length} Flagged` : '0 Clean'}
              </span>
            </div>
          </div>

          {/* Section 1: Extracted Candidate & Institution Details */}
          <div className="space-y-3">
            <h4 className="text-xs font-bold uppercase tracking-wider text-slate-400 flex items-center space-x-2">
              <User className="w-4 h-4 text-emerald-400" />
              <span>Extracted Document Credentials</span>
            </h4>
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
              <div className="p-3 rounded-xl bg-slate-950/60 border border-slate-800 flex items-center justify-between">
                <span className="text-xs text-slate-400">Student Name</span>
                <span className="text-xs font-semibold text-slate-100">
                  {extracted.student_name || record.student_name || 'Not Detected'}
                </span>
              </div>
              <div className="p-3 rounded-xl bg-slate-950/60 border border-slate-800 flex items-center justify-between">
                <span className="text-xs text-slate-400">USN / Identifier</span>
                <span className="text-xs font-mono font-semibold text-emerald-300">
                  {extracted.identifier || extracted.reg_no || record.identifier || 'Not Detected'}
                </span>
              </div>
              <div className="p-3 rounded-xl bg-slate-950/60 border border-slate-800 flex items-center justify-between">
                <span className="text-xs text-slate-400">Issuer / Authority</span>
                <span className="text-xs font-semibold text-slate-100">
                  {extracted.issuer || extracted.institution_name || record.issuer || 'Not Detected'}
                </span>
              </div>
              <div className="p-3 rounded-xl bg-slate-950/60 border border-slate-800 flex items-center justify-between">
                <span className="text-xs text-slate-400">Issue Date / SGPA</span>
                <span className="text-xs font-semibold text-slate-100">
                  {extracted.date || extracted.score_or_cgpa || extracted.sgpa
                    ? `${extracted.date || ''} ${extracted.score_or_cgpa || extracted.sgpa ? `(Score: ${extracted.score_or_cgpa || extracted.sgpa})` : ''}`
                    : 'N/A'}
                </span>
              </div>
            </div>
          </div>

          {/* Section 2: RAG Ground-Truth Validation Notes */}
          <div className="space-y-3">
            <h4 className="text-xs font-bold uppercase tracking-wider text-slate-400 flex items-center space-x-2">
              <ShieldCheck className="w-4 h-4 text-cyan-400" />
              <span>RAG Ground-Truth & Schema Verification</span>
            </h4>
            <div className="p-4 rounded-xl bg-slate-950/60 border border-slate-800 space-y-3">
              <div className="flex flex-wrap items-center gap-3">
                <div className="flex items-center space-x-1.5 text-xs">
                  <span className="text-slate-400">Institutional Schema:</span>
                  <span
                    className={`font-semibold ${
                      rag.schema_matched ? 'text-emerald-400' : 'text-amber-400'
                    }`}
                  >
                    {rag.schema_matched ? 'Matched' : 'Unmatched / Non-Standard'}
                  </span>
                </div>
                <div className="flex items-center space-x-1.5 text-xs">
                  <span className="text-slate-400">Marks Arithmetic:</span>
                  <span
                    className={`font-semibold ${
                      rag.arithmetic_valid ? 'text-emerald-400' : 'text-rose-400'
                    }`}
                  >
                    {rag.arithmetic_valid ? 'Consistent' : 'Inconsistent / Discrepancy'}
                  </span>
                </div>
              </div>

              {rag.anomalies_detected && rag.anomalies_detected.length > 0 ? (
                <div className="space-y-1 pt-1">
                  <span className="text-[11px] font-semibold text-rose-300 block">
                    Validation Observations / Discrepancies:
                  </span>
                  <ul className="list-disc list-inside text-xs text-slate-300 space-y-1">
                    {rag.anomalies_detected.map((note: string, idx: number) => (
                      <li key={idx} className="text-rose-300/90">
                        {note}
                      </li>
                    ))}
                  </ul>
                </div>
              ) : (
                <p className="text-xs text-emerald-400/90 flex items-center space-x-1">
                  <CheckCircle2 className="w-3.5 h-3.5" />
                  <span>
                    Document layout and credential structures successfully conform to institutional reference templates.
                  </span>
                </p>
              )}
            </div>
          </div>

          {/* Section 3: QR Payload & Whitelist Validation */}
          <div className="space-y-3">
            <h4 className="text-xs font-bold uppercase tracking-wider text-slate-400 flex items-center space-x-2">
              <QrCode className="w-4 h-4 text-purple-400" />
              <span>Cryptographic QR Code Validation</span>
            </h4>
            <div className="p-4 rounded-xl bg-slate-950/60 border border-slate-800 space-y-2">
              <div className="flex items-center justify-between text-xs">
                <span className="text-slate-400">Verification Source:</span>
                <span
                  className={`font-semibold ${
                    record.qr_status || qr.detected || qr.qr_present || qr.url_verified || qr.is_url
                      ? 'text-emerald-400'
                      : 'text-slate-400'
                  }`}
                >
                  {record.qr_status || qr.detected || qr.qr_present
                    ? 'Detected & Scanned (QR Code)'
                    : qr.url_verified || qr.is_url
                    ? 'Valid Institutional Verification URL'
                    : 'Printed URL / Visual Forensics'}
                </span>
              </div>
              {(qr.payload_or_url || qr.url) && (
                <div className="text-xs space-y-1 pt-1">
                  <span className="text-slate-400 block">Decoded URL / Payload:</span>
                  <div className="p-2.5 rounded-lg bg-slate-900 border border-slate-800 font-mono text-[11px] text-cyan-300 break-all select-all flex items-center justify-between">
                    <span>{qr.payload_or_url || qr.url}</span>
                    <a
                      href={qr.payload_or_url || qr.url || undefined}
                      target="_blank"
                      rel="noopener noreferrer"
                      className="ml-2 text-slate-400 hover:text-white"
                    >
                      <ExternalLink className="w-3.5 h-3.5" />
                    </a>
                  </div>
                </div>
              )}
              {qr.matches_document_text !== undefined && (
                <div className="flex items-center space-x-1.5 text-xs pt-1">
                  <span className="text-slate-400">Matches Extracted Typography:</span>
                  <span
                    className={`font-semibold ${
                      qr.matches_document_text ? 'text-emerald-400' : 'text-rose-400'
                    }`}
                  >
                    {qr.matches_document_text ? 'Yes' : 'Discrepancy Detected'}
                  </span>
                </div>
              )}
            </div>
          </div>

          {/* Section 4: Tampering & Forgery Flags */}
          <div className="space-y-3">
            <h4 className="text-xs font-bold uppercase tracking-wider text-slate-400 flex items-center space-x-2">
              <AlertTriangle className="w-4 h-4 text-amber-400" />
              <span>Forensic Tampering Indicators</span>
            </h4>
            <div className="p-4 rounded-xl bg-slate-950/60 border border-slate-800">
              {tamperingFlags.length > 0 ? (
                <div className="flex flex-wrap gap-2">
                  {tamperingFlags.map((flag, idx) => (
                    <span
                      key={idx}
                      className="px-2.5 py-1 rounded-lg text-xs font-semibold bg-rose-500/10 text-rose-300 border border-rose-500/30"
                    >
                      {flag}
                    </span>
                  ))}
                </div>
              ) : (
                <p className="text-xs text-emerald-400/90 flex items-center space-x-1.5">
                  <CheckCircle2 className="w-4 h-4" />
                  <span>
                    Zero tampering or font splicing anomalies detected across forensic inspection layers.
                  </span>
                </p>
              )}

              {record.remarks && (
                <div className="mt-3 pt-3 border-t border-slate-800/80 text-xs text-slate-300">
                  <span className="text-slate-400 font-semibold block mb-0.5">Remarks / Rationale:</span>
                  <p className="italic text-slate-300/90">{record.remarks}</p>
                </div>
              )}
            </div>
          </div>
        </div>

        {/* Modal Footer */}
        <div className="px-6 py-3.5 border-t border-slate-800 bg-slate-950/70 flex items-center justify-between">
          <span className="text-xs text-slate-500">
            Immutable Verification Ledger &bull; SHA-256 Validated
          </span>
          <button
            onClick={onClose}
            className="px-4 py-2 rounded-xl bg-slate-800 hover:bg-slate-700 text-white text-xs font-semibold border border-slate-700 transition-colors"
          >
            Close Inspector
          </button>
        </div>
      </div>
    </div>
  );
};
