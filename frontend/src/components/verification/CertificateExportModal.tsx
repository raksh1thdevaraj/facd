import React, { useRef, useState } from 'react';
import {
  ForensicAuditCertificate,
  ForensicCertificateData,
} from './ForensicAuditCertificate';
import { exportCertificateElementToPdf } from '../../utils/pdfExport';
import {
  X,
  Download,
  Printer,
  FileCheck,
  Loader2,
  CheckCircle,
} from 'lucide-react';

interface Props {
  isOpen: boolean;
  onClose: () => void;
  certificateData: ForensicCertificateData;
}

export const CertificateExportModal: React.FC<Props> = ({
  isOpen,
  onClose,
  certificateData,
}) => {
  const certificateRef = useRef<HTMLDivElement>(null);
  const [downloading, setDownloading] = useState<boolean>(false);
  const [downloadSuccess, setDownloadSuccess] = useState<boolean>(false);

  if (!isOpen) return null;

  const handleDownloadPdf = async () => {
    if (!certificateRef.current) return;
    try {
      setDownloading(true);
      const cleanScanId = certificateData.scan_id.replace(/^scan_/, '').slice(0, 8);
      const filename = `Forensic_Audit_Certificate_${cleanScanId || 'EVAL'}.pdf`;

      await exportCertificateElementToPdf(certificateRef.current, {
        filename,
      });

      setDownloadSuccess(true);
      setTimeout(() => setDownloadSuccess(false), 3000);
    } catch (err: unknown) {
      console.error('PDF generation error:', err);
      alert('Unable to generate client-side PDF. Please try Print Official Certificate instead.');
    } finally {
      setDownloading(false);
    }
  };

  const handlePrint = () => {
    window.print();
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-slate-950/80 backdrop-blur-sm p-4 overflow-y-auto no-print">
      <div className="relative w-full max-w-5xl rounded-3xl bg-slate-900 border border-slate-800 shadow-2xl overflow-hidden my-6">
        {/* Top Modal Bar */}
        <div className="flex items-center justify-between px-6 py-4 border-b border-slate-800 bg-slate-950/60">
          <div className="flex items-center space-x-3">
            <div className="p-2 rounded-xl bg-amber-500/10 text-amber-400 border border-amber-500/20">
              <FileCheck className="w-5 h-5" />
            </div>
            <div>
              <h3 className="text-sm font-bold text-white uppercase tracking-wider">
                Forensic Verification Certificate & Audit Dossier
              </h3>
              <p className="text-[11px] text-slate-400">
                Official compliance document with SHA-256 cryptographic attestation & verification QR
              </p>
            </div>
          </div>

          <div className="flex items-center space-x-3">
            {/* Download PDF button */}
            <button
              onClick={handleDownloadPdf}
              disabled={downloading}
              className="inline-flex items-center space-x-2 px-4 py-2 rounded-xl bg-gradient-to-r from-amber-600 to-amber-700 hover:from-amber-500 hover:to-amber-600 text-white text-xs font-bold shadow-lg shadow-amber-600/20 transition-all cursor-pointer disabled:opacity-50"
            >
              {downloading ? (
                <>
                  <Loader2 className="w-4 h-4 animate-spin" />
                  <span>Compiling PDF...</span>
                </>
              ) : downloadSuccess ? (
                <>
                  <CheckCircle className="w-4 h-4 text-emerald-300" />
                  <span>Downloaded!</span>
                </>
              ) : (
                <>
                  <Download className="w-4 h-4" />
                  <span>Download Audit PDF</span>
                </>
              )}
            </button>

            {/* Print Certificate button */}
            <button
              onClick={handlePrint}
              className="inline-flex items-center space-x-2 px-3.5 py-2 rounded-xl bg-slate-800 hover:bg-slate-700 text-slate-200 text-xs font-semibold border border-slate-700 transition-colors cursor-pointer"
            >
              <Printer className="w-4 h-4 text-slate-300" />
              <span>Print</span>
            </button>

            {/* Close modal */}
            <button
              onClick={onClose}
              className="p-2 rounded-xl text-slate-400 hover:text-white hover:bg-slate-800 transition-colors cursor-pointer"
            >
              <X className="w-5 h-5" />
            </button>
          </div>
        </div>

        {/* Scrollable Certificate Viewer Area */}
        <div className="p-4 sm:p-8 max-h-[78vh] overflow-y-auto bg-slate-950/40 flex justify-center">
          <div ref={certificateRef} className="shadow-2xl">
            <ForensicAuditCertificate
              id="forensic-audit-certificate-print-root"
              data={certificateData}
            />
          </div>
        </div>
      </div>
    </div>
  );
};
