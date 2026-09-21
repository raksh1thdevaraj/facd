import React, { useState } from 'react';
import { Download, FileJson, Share2, Check, Loader2, ShieldCheck } from 'lucide-react';
import { reportService } from '../../services/reportService';

interface ReportActionsProps {
  reportId: string;
}

export const ReportActions: React.FC<ReportActionsProps> = ({ reportId }) => {
  const [downloadingPdf, setDownloadingPdf] = useState<boolean>(false);
  const [downloadingJson, setDownloadingJson] = useState<boolean>(false);
  const [verifying, setVerifying] = useState<boolean>(false);
  const [copiedLink, setCopiedLink] = useState<boolean>(false);
  const [verifyResult, setVerifyResult] = useState<string | null>(null);

  const handleDownloadPdf = async () => {
    try {
      setDownloadingPdf(true);
      await reportService.downloadReportPdf(reportId);
    } catch (err) {
      console.error('Failed to download PDF:', err);
      alert('Failed to download official PDF. Please ensure the backend report generator is accessible.');
    } finally {
      setDownloadingPdf(false);
    }
  };

  const handleDownloadJson = async () => {
    try {
      setDownloadingJson(true);
      await reportService.downloadReportJson(reportId);
    } catch (err) {
      console.error('Failed to download JSON:', err);
      alert('Failed to download report JSON.');
    } finally {
      setDownloadingJson(false);
    }
  };

  const handleCopyLink = () => {
    const url = `${window.location.origin}/verify-report/${reportId}`;
    navigator.clipboard.writeText(url);
    setCopiedLink(true);
    setTimeout(() => setCopiedLink(false), 2500);
  };

  const handleVerifyIntegrity = async () => {
    try {
      setVerifying(true);
      const res = await reportService.verifyReportIntegrity(reportId);
      if (res.is_valid) {
        setVerifyResult('HMAC-SHA256 signature verified: Document payload is untampered.');
      } else {
        setVerifyResult('Signature verification failed: Potential data tampering detected.');
      }
    } catch {
      setVerifyResult('Could not verify digital signature.');
    } finally {
      setVerifying(false);
      setTimeout(() => setVerifyResult(null), 5000);
    }
  };

  return (
    <div className="glass-card rounded-2xl p-6 border border-slate-800 shadow-xl space-y-4">
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h3 className="text-base font-bold text-slate-100">Export & Verification Actions</h3>
          <p className="text-xs text-slate-400">Download tamper-evident documents or share verification URL</p>
        </div>

        <div className="flex flex-wrap items-center gap-3">
          <button
            onClick={handleDownloadPdf}
            disabled={downloadingPdf}
            className="inline-flex items-center space-x-2 px-4 py-2 rounded-xl bg-emerald-600 hover:bg-emerald-500 text-white text-xs sm:text-sm font-semibold shadow-lg shadow-emerald-600/20 transition-all hover:scale-105 active:scale-95 disabled:opacity-50"
          >
            {downloadingPdf ? (
              <Loader2 className="w-4 h-4 animate-spin" />
            ) : (
              <Download className="w-4 h-4" />
            )}
            <span>{downloadingPdf ? 'Rendering PDF...' : 'Download Official PDF'}</span>
          </button>

          <button
            onClick={handleDownloadJson}
            disabled={downloadingJson}
            className="inline-flex items-center space-x-2 px-3.5 py-2 rounded-xl bg-slate-800 hover:bg-slate-700 text-slate-200 text-xs sm:text-sm font-medium border border-slate-700 transition-colors disabled:opacity-50"
          >
            {downloadingJson ? (
              <Loader2 className="w-4 h-4 animate-spin text-slate-400" />
            ) : (
              <FileJson className="w-4 h-4 text-cyan-400" />
            )}
            <span>Download JSON</span>
          </button>

          <button
            onClick={handleCopyLink}
            className="inline-flex items-center space-x-2 px-3.5 py-2 rounded-xl bg-slate-800 hover:bg-slate-700 text-slate-200 text-xs sm:text-sm font-medium border border-slate-700 transition-colors"
          >
            {copiedLink ? (
              <>
                <Check className="w-4 h-4 text-emerald-400" />
                <span className="text-emerald-400">Link Copied!</span>
              </>
            ) : (
              <>
                <Share2 className="w-4 h-4 text-amber-400" />
                <span>Share Public URL</span>
              </>
            )}
          </button>

          <button
            onClick={handleVerifyIntegrity}
            disabled={verifying}
            className="inline-flex items-center space-x-2 px-3.5 py-2 rounded-xl bg-slate-800 hover:bg-slate-700 text-slate-200 text-xs sm:text-sm font-medium border border-slate-700 transition-colors disabled:opacity-50"
          >
            {verifying ? (
              <Loader2 className="w-4 h-4 animate-spin text-emerald-400" />
            ) : (
              <ShieldCheck className="w-4 h-4 text-emerald-400" />
            )}
            <span>Verify Signature</span>
          </button>
        </div>
      </div>

      {verifyResult && (
        <div className="p-3 rounded-xl bg-slate-900 border border-emerald-500/30 text-xs text-emerald-300 animate-fadeIn">
          {verifyResult}
        </div>
      )}
    </div>
  );
};
