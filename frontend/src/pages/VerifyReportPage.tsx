import React, { useEffect, useState } from 'react';
import { useParams, Link } from 'react-router-dom';
import { reportService } from '../services/reportService';
import { FullVerificationReport } from '../types/report';
import { ShieldCheck, ShieldAlert, AlertTriangle, Loader2, ArrowLeft, ExternalLink } from 'lucide-react';

export const VerifyReportPage: React.FC = () => {
  const { id } = useParams<{ id: string }>();
  const [report, setReport] = useState<FullVerificationReport | null>(null);
  const [integrityValid, setIntegrityValid] = useState<boolean | null>(null);
  const [loading, setLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let isMounted = true;

    const runVerification = async () => {
      if (!id) return;
      try {
        setLoading(true);
        setError(null);
        // Run parallel report retrieval and cryptographic signature validation
        const [reportData, integrityRes] = await Promise.allSettled([
          reportService.getReport(id),
          reportService.verifyReportIntegrity(id),
        ]);

        if (!isMounted) return;

        if (reportData.status === 'fulfilled') {
          setReport(reportData.value);
        } else {
          setError('Verification record not found or inaccessible.');
        }

        if (integrityRes.status === 'fulfilled') {
          setIntegrityValid(integrityRes.value.is_valid);
        } else {
          setIntegrityValid(false);
        }
      } catch (err: unknown) {
        if (isMounted) {
          setError(err instanceof Error ? err.message : 'Failed to verify report');
        }
      } finally {
        if (isMounted) {
          setLoading(false);
        }
      }
    };

    runVerification();

    return () => {
      isMounted = false;
    };
  }, [id]);

  if (loading) {
    return (
      <div className="min-h-[400px] flex flex-col items-center justify-center space-y-4 px-4 text-center">
        <Loader2 className="w-10 h-10 animate-spin text-emerald-400" />
        <h3 className="text-base font-bold text-slate-200">Verifying Cryptographic Digital Seal...</h3>
        <p className="text-xs text-slate-400">Validating HMAC-SHA256 signature against database audit trail</p>
      </div>
    );
  }

  if (error || !report) {
    return (
      <div className="max-w-md mx-auto my-8 glass-card rounded-2xl p-6 border border-rose-800/60 text-center space-y-4">
        <div className="p-3 bg-rose-500/20 text-rose-400 rounded-2xl w-fit mx-auto">
          <AlertTriangle className="w-8 h-8" />
        </div>
        <h3 className="text-lg font-bold text-slate-100">Verification Seal Unresolvable</h3>
        <p className="text-xs text-slate-400">{error || 'This report ID is invalid or has expired.'}</p>
        <Link
          to="/"
          className="inline-flex items-center space-x-2 text-xs text-emerald-400 hover:text-emerald-300 font-medium pt-2"
        >
          <ArrowLeft className="w-4 h-4" />
          <span>Return to Homepage</span>
        </Link>
      </div>
    );
  }

  const isAuthentic = report.verdict === 'AUTHENTIC';
  const isManipulated = report.verdict === 'MANIPULATED';
  const credentials = report.extracted_fields || report.credentials || {};

  return (
    <div className="max-w-lg mx-auto py-4 px-4 sm:px-0 space-y-6">
      {/* Mobile-Friendly Header Card */}
      <div className="glass-card rounded-2xl p-6 border border-slate-800 shadow-2xl text-center space-y-4">
        <div
          className={`p-3.5 rounded-2xl w-fit mx-auto ${
            integrityValid && isAuthentic
              ? 'bg-emerald-600 text-white shadow-lg shadow-emerald-600/30'
              : 'bg-rose-600 text-white shadow-lg shadow-rose-600/30'
          }`}
        >
          {integrityValid && isAuthentic ? (
            <ShieldCheck className="w-8 h-8" />
          ) : (
            <ShieldAlert className="w-8 h-8" />
          )}
        </div>

        <div>
          <span
            className={`inline-block px-3 py-1 rounded-full text-xs font-bold uppercase tracking-wider mb-2 border ${
              isAuthentic
                ? 'bg-emerald-500/20 text-emerald-300 border-emerald-500/40'
                : isManipulated
                ? 'bg-rose-500/20 text-rose-300 border-rose-500/40'
                : 'bg-amber-500/20 text-amber-300 border-amber-500/40'
            }`}
          >
            {report.verdict}
          </span>
          <h2 className="text-xl font-extrabold text-slate-100">Official Verification Result</h2>
          <p className="text-xs text-slate-400 mt-1">
            HMAC Signature:{' '}
            <span className={integrityValid ? 'text-emerald-400 font-semibold' : 'text-rose-400 font-semibold'}>
              {integrityValid ? 'VALID & UNTAMPERED' : 'UNVERIFIED / ALTERED'}
            </span>
          </p>
        </div>
      </div>

      {/* Certificate Details Card */}
      <div className="glass-card rounded-2xl p-6 border border-slate-800 shadow-xl space-y-4 text-xs">
        <h4 className="text-sm font-bold text-slate-200 border-b border-slate-800 pb-2">
          Academic Particulars
        </h4>

        <div className="space-y-3">
          <div>
            <span className="text-slate-500 uppercase tracking-wider text-[10px] block">Student Name</span>
            <span className="text-sm font-semibold text-slate-200">
              {credentials.student_name || 'Not detected'}
            </span>
          </div>

          <div>
            <span className="text-slate-500 uppercase tracking-wider text-[10px] block">Accredited Institution</span>
            <span className="text-sm font-semibold text-slate-200">
              {credentials.institution_name || 'Not detected'}
            </span>
          </div>

          <div>
            <span className="text-slate-500 uppercase tracking-wider text-[10px] block">Conferred Degree</span>
            <span className="text-sm font-semibold text-slate-200">
              {credentials.course_degree || credentials.degree_title || 'Not detected'}
            </span>
          </div>

          <div className="grid grid-cols-2 gap-2 pt-1 border-t border-slate-800/80">
            <div>
              <span className="text-slate-500 uppercase tracking-wider text-[10px] block">Issue Date</span>
              <span className="text-slate-300 font-medium">
                {credentials.issue_date || credentials.graduation_date || 'N/A'}
              </span>
            </div>
            <div>
              <span className="text-slate-500 uppercase tracking-wider text-[10px] block">Confidence</span>
              <span className="text-emerald-400 font-mono font-bold">
                {(report.authenticity_score * 100).toFixed(1)}%
              </span>
            </div>
          </div>
        </div>

        {/* Cryptographic SHA256 snippet */}
        <div className="pt-3 border-t border-slate-800 text-[11px] text-slate-400">
          <span className="block font-semibold text-slate-300 mb-1">Document Fingerprint:</span>
          <code className="block bg-slate-950 p-2 rounded border border-slate-800 text-slate-400 font-mono break-all">
            {report.file_metadata.sha256_checksum}
          </code>
        </div>
      </div>


      {/* Action to view full dashboard */}
      <div className="text-center pt-2">
        <Link
          to={`/results/${report.report_id}`}
          className="inline-flex items-center space-x-2 px-5 py-2.5 rounded-xl bg-slate-800 hover:bg-slate-700 text-slate-200 text-xs sm:text-sm font-medium border border-slate-700 transition-colors"
        >
          <span>Open Full Interactive Dossier</span>
          <ExternalLink className="w-4 h-4 text-emerald-400" />
        </Link>
      </div>
    </div>
  );
};
