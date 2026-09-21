import React, { useState, useEffect } from 'react';
import {
  ShieldCheck,
  ShieldAlert,
  AlertTriangle,
  HelpCircle,
  UploadCloud,
  FileCheck,
  Download,
  Search,
  QrCode,
  Globe,
  Fingerprint,
  FileText,
  Loader2,
  RotateCcw,
} from 'lucide-react';
import { courseCertificateService } from '../services/courseCertificateService';
import {
  CourseVerificationResponse,
  CourseVerificationStatus,
  CourseURLVerificationResult,
  IssuerInfo,
} from '../types/courseCertificate';

export const CourseVerificationPage: React.FC = () => {
  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const [previewUrl, setPreviewUrl] = useState<string | null>(null);
  const [isVerifying, setIsVerifying] = useState<boolean>(false);
  const [verificationResult, setVerificationResult] = useState<CourseVerificationResponse | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [isDownloadingPdf, setIsDownloadingPdf] = useState<boolean>(false);

  // Standalone URL test tool state
  const [testUrl, setTestUrl] = useState<string>('');
  const [isTestingUrl, setIsTestingUrl] = useState<boolean>(false);
  const [urlTestResult, setUrlTestResult] = useState<CourseURLVerificationResult | null>(null);

  // Authoritative issuers list
  const [issuers, setIssuers] = useState<IssuerInfo[]>([]);

  useEffect(() => {
    courseCertificateService
      .listIssuers()
      .then((data) => setIssuers(data))
      .catch((err) => console.warn('Failed to load issuers registry:', err));
  }, []);

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files && e.target.files[0]) {
      const file = e.target.files[0];
      setSelectedFile(file);
      setError(null);
      setVerificationResult(null);

      if (file.type.startsWith('image/')) {
        const url = URL.createObjectURL(file);
        setPreviewUrl(url);
      } else {
        setPreviewUrl(null);
      }
    }
  };

  const handleDrop = (e: React.DragEvent<HTMLDivElement>) => {
    e.preventDefault();
    if (e.dataTransfer.files && e.dataTransfer.files[0]) {
      const file = e.dataTransfer.files[0];
      setSelectedFile(file);
      setError(null);
      setVerificationResult(null);

      if (file.type.startsWith('image/')) {
        const url = URL.createObjectURL(file);
        setPreviewUrl(url);
      } else {
        setPreviewUrl(null);
      }
    }
  };

  const handleRunVerification = async () => {
    if (!selectedFile) return;

    try {
      setIsVerifying(true);
      setError(null);
      const res = await courseCertificateService.verifyCourseCertificate(selectedFile);
      setVerificationResult(res);
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : 'Verification failed';
      setError(msg);
    } finally {
      setIsVerifying(false);
    }
  };

  const handleDownloadPdf = async () => {
    if (!verificationResult) return;
    try {
      setIsDownloadingPdf(true);
      await courseCertificateService.downloadReport(
        verificationResult.verification_id,
        `course_audit_${verificationResult.certificate_id || 'report'}.pdf`
      );
    } catch (err) {
      console.error('Failed to download PDF:', err);
    } finally {
      setIsDownloadingPdf(false);
    }
  };

  const handleTestUrl = async () => {
    if (!testUrl.trim()) return;
    try {
      setIsTestingUrl(true);
      const res = await courseCertificateService.verifyUrl(testUrl.trim());
      setUrlTestResult(res);
    } catch (err) {
      console.error('URL test error:', err);
    } finally {
      setIsTestingUrl(false);
    }
  };

  const handleReset = () => {
    setSelectedFile(null);
    setPreviewUrl(null);
    setVerificationResult(null);
    setError(null);
  };

  // Verdict visual helpers
  const getStatusBadge = (status: CourseVerificationStatus) => {
    switch (status) {
      case 'VERIFIED':
        return {
          icon: <ShieldCheck className="w-8 h-8 text-emerald-400" />,
          title: 'VERIFIED - AUTHENTIC COURSE CERTIFICATE',
          bgColor: 'bg-emerald-950/40 border-emerald-500/40 text-emerald-300',
          badgeColor: 'bg-emerald-500/20 text-emerald-400 border-emerald-500/30',
          description: 'Document matches official issuer online registries with zero evidence of tampering.',
        };
      case 'SUSPICIOUS':
        return {
          icon: <AlertTriangle className="w-8 h-8 text-amber-400" />,
          title: 'SUSPICIOUS - DISCREPANCIES OBSERVED',
          bgColor: 'bg-amber-950/40 border-amber-500/40 text-amber-300',
          badgeColor: 'bg-amber-500/20 text-amber-400 border-amber-500/30',
          description: 'Partial mismatch between certificate text and registry, or unrecognized issuer domain.',
        };
      case 'FRAUDULENT':
        return {
          icon: <ShieldAlert className="w-8 h-8 text-rose-400" />,
          title: 'FRAUDULENT - TAMPERING / ATTACK DETECTED',
          bgColor: 'bg-rose-950/40 border-rose-500/40 text-rose-300',
          badgeColor: 'bg-rose-500/20 text-rose-400 border-rose-500/30',
          description: 'High-confidence manipulation detected (e.g. copied QR, modified recipient name or malicious URL).',
        };
      default:
        return {
          icon: <HelpCircle className="w-8 h-8 text-slate-400" />,
          title: 'UNVERIFIED - ONLINE RECORD UNAVAILABLE',
          bgColor: 'bg-slate-900/60 border-slate-700 text-slate-300',
          badgeColor: 'bg-slate-700 text-slate-300 border-slate-600',
          description: 'Online verification service unreachable or document lacks machine-verifiable online credentials.',
        };
    }
  };

  return (
    <div className="space-y-8 animate-fade-in">
      {/* Page Header */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 border-b border-slate-800 pb-6">
        <div>
          <div className="flex items-center space-x-3">
            <div className="p-2.5 rounded-xl bg-gradient-to-tr from-emerald-600 to-teal-500 text-white shadow-lg shadow-emerald-500/20">
              <ShieldCheck className="w-6 h-6" />
            </div>
            <div>
              <h1 className="text-2xl font-extrabold text-slate-100 tracking-tight">
                Course Certificate Authenticity Verification
              </h1>
              <p className="text-sm text-slate-400">
                Multi-signal forensic auditing, QR decoding, SSRF-safe URL resolution & cross-modal online record matching
              </p>
            </div>
          </div>
        </div>

        <div className="flex items-center space-x-2">
          <span className="inline-flex items-center px-3 py-1 rounded-full text-xs font-medium bg-emerald-500/10 text-emerald-400 border border-emerald-500/20">
            <span className="w-1.5 h-1.5 rounded-full bg-emerald-400 mr-1.5 animate-pulse" />
            Active Issuers Registry: {issuers.length || 8} Providers
          </span>
        </div>
      </div>

      {/* Main Grid: Upload & Verification Section */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-8">
        {/* Left Column: Upload & Control Panel */}
        <div className="lg:col-span-5 space-y-6">
          <div className="p-6 rounded-2xl bg-slate-900/60 border border-slate-800 backdrop-blur-xl shadow-xl space-y-5">
            <h2 className="text-base font-semibold text-slate-200 flex items-center space-x-2">
              <UploadCloud className="w-5 h-5 text-emerald-400" />
              <span>Upload Certificate Document</span>
            </h2>

            {!selectedFile ? (
              <div
                onDragOver={(e) => e.preventDefault()}
                onDrop={handleDrop}
                className="border-2 border-dashed border-slate-700 hover:border-emerald-500/60 transition-all rounded-xl p-8 text-center cursor-pointer bg-slate-950/40 hover:bg-slate-900/50 group"
                onClick={() => document.getElementById('course-cert-upload-input')?.click()}
              >
                <input
                  type="file"
                  id="course-cert-upload-input"
                  className="hidden"
                  accept="image/png,image/jpeg,image/jpg,image/webp,application/pdf"
                  onChange={handleFileChange}
                />
                <div className="w-14 h-14 mx-auto mb-4 rounded-xl bg-slate-800/60 flex items-center justify-center text-slate-400 group-hover:text-emerald-400 group-hover:scale-110 transition-all">
                  <FileCheck className="w-7 h-7" />
                </div>
                <p className="text-sm font-medium text-slate-200">
                  Click or drag course certificate here
                </p>
                <p className="text-xs text-slate-500 mt-1">
                  Supports Coursera, edX, HarvardX, Udemy, Credly certificates (PNG, JPG, PDF)
                </p>
              </div>
            ) : (
              <div className="space-y-4">
                <div className="relative rounded-xl overflow-hidden border border-slate-800 bg-slate-950 p-3">
                  {previewUrl ? (
                    <img
                      src={previewUrl}
                      alt="Certificate Preview"
                      className="max-h-56 w-full object-contain rounded-lg"
                    />
                  ) : (
                    <div className="py-8 text-center text-slate-400">
                      <FileText className="w-12 h-12 mx-auto mb-2 text-emerald-400" />
                      <p className="text-sm font-medium">{selectedFile.name}</p>
                      <p className="text-xs text-slate-500">{(selectedFile.size / 1024).toFixed(1)} KB</p>
                    </div>
                  )}
                </div>

                <div className="flex items-center space-x-3">
                  <button
                    onClick={handleRunVerification}
                    disabled={isVerifying}
                    className="flex-1 py-2.5 px-4 rounded-xl bg-gradient-to-r from-emerald-600 to-teal-600 hover:from-emerald-500 hover:to-teal-500 text-white font-medium text-sm flex items-center justify-center space-x-2 shadow-lg shadow-emerald-500/20 disabled:opacity-50 transition-all cursor-pointer"
                  >
                    {isVerifying ? (
                      <>
                        <Loader2 className="w-4 h-4 animate-spin" />
                        <span>Running Multi-Signal Audit...</span>
                      </>
                    ) : (
                      <>
                        <ShieldCheck className="w-4 h-4" />
                        <span>Verify Authenticity</span>
                      </>
                    )}
                  </button>

                  <button
                    onClick={handleReset}
                    disabled={isVerifying}
                    className="p-2.5 rounded-xl border border-slate-700 text-slate-400 hover:text-slate-200 hover:bg-slate-800 transition-colors"
                    title="Reset selection"
                  >
                    <RotateCcw className="w-4 h-4" />
                  </button>
                </div>
              </div>
            )}

            {error && (
              <div className="p-3.5 rounded-xl bg-rose-950/40 border border-rose-500/30 text-rose-300 text-xs flex items-center space-x-2">
                <AlertTriangle className="w-4 h-4 text-rose-400 shrink-0" />
                <span>{error}</span>
              </div>
            )}
          </div>

          {/* Quick URL & SSRF Tester Card */}
          <div className="p-6 rounded-2xl bg-slate-900/60 border border-slate-800 backdrop-blur-xl shadow-xl space-y-4">
            <div className="flex items-center justify-between">
              <h3 className="text-sm font-semibold text-slate-200 flex items-center space-x-2">
                <Globe className="w-4 h-4 text-teal-400" />
                <span>Verification URL & SSRF Tester</span>
              </h3>
              <span className="text-[10px] uppercase font-bold text-slate-400 bg-slate-800 px-2 py-0.5 rounded">
                Sandbox
              </span>
            </div>

            <p className="text-xs text-slate-400">
              Test candidate QR code verification URLs directly for domain spoofing, private IP SSRF attacks, and issuer registry matching.
            </p>

            <div className="flex space-x-2">
              <input
                type="text"
                placeholder="https://coursera.org/verify/..."
                value={testUrl}
                onChange={(e) => setTestUrl(e.target.value)}
                className="flex-1 bg-slate-950 border border-slate-700 rounded-lg px-3 py-1.5 text-xs text-slate-200 focus:outline-none focus:border-teal-500"
              />
              <button
                onClick={handleTestUrl}
                disabled={isTestingUrl || !testUrl.trim()}
                className="px-3 py-1.5 rounded-lg bg-teal-600 hover:bg-teal-500 text-white text-xs font-medium flex items-center space-x-1 disabled:opacity-50"
              >
                {isTestingUrl ? <Loader2 className="w-3.5 h-3.5 animate-spin" /> : <Search className="w-3.5 h-3.5" />}
                <span>Inspect</span>
              </button>
            </div>

            {urlTestResult && (
              <div className="p-3.5 rounded-xl bg-slate-950 border border-slate-800 space-y-2 text-xs">
                <div className="flex items-center justify-between">
                  <span className="text-slate-400">Trust Level:</span>
                  <span
                    className={`font-semibold px-2 py-0.5 rounded text-[11px] ${
                      urlTestResult.risk_level === 'SAFE'
                        ? 'bg-emerald-500/20 text-emerald-400'
                        : urlTestResult.risk_level === 'MALICIOUS'
                        ? 'bg-rose-500/20 text-rose-400'
                        : 'bg-amber-500/20 text-amber-400'
                    }`}
                  >
                    {urlTestResult.risk_level} ({urlTestResult.trust_score * 100}%)
                  </span>
                </div>
                <div className="flex items-center justify-between">
                  <span className="text-slate-400">Resolved Issuer:</span>
                  <span className="text-slate-200 font-medium">
                    {urlTestResult.resolved_issuer || 'Unrecognized Domain'}
                  </span>
                </div>
                <div className="flex items-center justify-between">
                  <span className="text-slate-400">Domain Match:</span>
                  <span>{urlTestResult.domain_match ? '✅ Verified Domain' : '❌ Unrecognized'}</span>
                </div>
                {urlTestResult.remarks && (
                  <p className="text-[11px] text-slate-400 pt-1 border-t border-slate-800">
                    {urlTestResult.remarks}
                  </p>
                )}
              </div>
            )}
          </div>
        </div>

        {/* Right Column: Detailed Multi-Signal Audit Results */}
        <div className="lg:col-span-7 space-y-6">
          {!verificationResult ? (
            <div className="h-full min-h-[440px] flex flex-col items-center justify-center p-8 rounded-2xl bg-slate-900/40 border border-slate-800 text-center text-slate-400 space-y-4">
              <div className="p-4 rounded-2xl bg-slate-800/40 text-slate-500">
                <Fingerprint className="w-12 h-12" />
              </div>
              <div className="max-w-md">
                <h3 className="text-base font-semibold text-slate-300">No Document Audited Yet</h3>
                <p className="text-xs text-slate-500 mt-1">
                  Upload a completion certificate on the left to trigger the multi-signal AI verification engine.
                </p>
              </div>
            </div>
          ) : (
            <div className="space-y-6">
              {/* Top Verdict Banner */}
              {(() => {
                const badge = getStatusBadge(verificationResult.decision.status);
                return (
                  <div className={`p-6 rounded-2xl border ${badge.bgColor} backdrop-blur-xl shadow-2xl relative overflow-hidden`}>
                    <div className="flex items-start space-x-4">
                      <div className="shrink-0 p-2 rounded-xl bg-slate-950/60 border border-slate-800">
                        {badge.icon}
                      </div>
                      <div className="flex-1">
                        <div className="flex items-center space-x-2">
                          <h2 className="text-lg font-bold tracking-wide">{badge.title}</h2>
                          <span className={`px-2 py-0.5 rounded text-xs font-bold border ${badge.badgeColor}`}>
                            {verificationResult.decision.status}
                          </span>
                        </div>
                        <p className="text-xs mt-1 opacity-90">{badge.description}</p>

                        <div className="grid grid-cols-2 sm:grid-cols-4 gap-3 mt-4 pt-4 border-t border-slate-800/60 text-xs">
                          <div>
                            <span className="text-slate-400 block text-[11px]">Authenticity Score</span>
                            <span className="text-base font-bold text-slate-100">
                              {(verificationResult.decision.overall_authenticity_score * 100).toFixed(1)}%
                            </span>
                          </div>
                          <div>
                            <span className="text-slate-400 block text-[11px]">Fraud Risk</span>
                            <span className="text-base font-bold text-slate-100">
                              {(verificationResult.decision.fraud_risk_score * 100).toFixed(1)}%
                            </span>
                          </div>
                          <div>
                            <span className="text-slate-400 block text-[11px]">OCR Quality</span>
                            <span className="text-base font-bold text-slate-100">
                              {(verificationResult.extracted_fields.ocr_confidence * 100).toFixed(1)}%
                            </span>
                          </div>
                          <div>
                            <span className="text-slate-400 block text-[11px]">Domain Trust</span>
                            <span className="text-base font-bold text-slate-100">
                              {(verificationResult.url_result.trust_score * 100).toFixed(0)}%
                            </span>
                          </div>
                        </div>
                      </div>
                    </div>
                  </div>
                );
              })()}

              {/* Copied QR Code Attack Warning Banner */}
              {verificationResult.comparison_result.copied_qr_detected && (
                <div className="p-4 rounded-xl bg-rose-950/60 border-2 border-rose-500/80 text-rose-200 text-xs space-y-2 animate-pulse">
                  <div className="flex items-center space-x-2 font-bold text-sm text-rose-300">
                    <ShieldAlert className="w-5 h-5 text-rose-400" />
                    <span>CRITICAL SECURITY ALERT: TRANSPLANTED / COPIED QR CODE DETECTED</span>
                  </div>
                  <p>
                    The QR code embedded on this certificate leads to a genuine, authentic credential page. However,
                    the recipient name or credential ID registered on the official online registry does NOT match the text
                    printed on this certificate.
                  </p>
                </div>
              )}

              {/* Side-by-Side Cross-Modal Comparison Card */}
              <div className="p-6 rounded-2xl bg-slate-900/60 border border-slate-800 backdrop-blur-xl shadow-xl space-y-4">
                <div className="flex items-center justify-between">
                  <h3 className="text-sm font-semibold text-slate-200 flex items-center space-x-2">
                    <FileText className="w-4 h-4 text-emerald-400" />
                    <span>Cross-Modal Record Comparison (Certificate vs Online Record)</span>
                  </h3>
                  <span className="text-xs font-medium text-emerald-400">
                    {(verificationResult.comparison_result.overall_match_score * 100).toFixed(1)}% Agreement
                  </span>
                </div>

                <div className="overflow-x-auto">
                  <table className="w-full text-xs text-left">
                    <thead className="text-[11px] uppercase bg-slate-950/60 text-slate-400 border-b border-slate-800">
                      <tr>
                        <th className="py-2 px-3">Field</th>
                        <th className="py-2 px-3">Certificate OCR Text</th>
                        <th className="py-2 px-3">Official Online Record</th>
                        <th className="py-2 px-3 text-right">Alignment</th>
                      </tr>
                    </thead>
                    <tbody className="divide-y divide-slate-800/60 text-slate-300">
                      <tr>
                        <td className="py-2.5 px-3 font-medium text-slate-400">Candidate Name</td>
                        <td className="py-2.5 px-3 font-semibold text-slate-100">
                          {verificationResult.extracted_fields.candidate_name || 'Not Extracted'}
                        </td>
                        <td className="py-2.5 px-3">
                          {verificationResult.comparison_result.online_record?.candidate_name || (
                            <span className="text-slate-500 italic">No online record</span>
                          )}
                        </td>
                        <td className="py-2.5 px-3 text-right font-medium">
                          {verificationResult.comparison_result.name_match_score >= 0.8 ? (
                            <span className="text-emerald-400">{(verificationResult.comparison_result.name_match_score * 100).toFixed(0)}% ✅</span>
                          ) : (
                            <span className="text-rose-400">{(verificationResult.comparison_result.name_match_score * 100).toFixed(0)}% ❌</span>
                          )}
                        </td>
                      </tr>

                      <tr>
                        <td className="py-2.5 px-3 font-medium text-slate-400">Course Title</td>
                        <td className="py-2.5 px-3 font-semibold text-slate-100">
                          {verificationResult.extracted_fields.course_name || 'Not Extracted'}
                        </td>
                        <td className="py-2.5 px-3">
                          {verificationResult.comparison_result.online_record?.course_name || (
                            <span className="text-slate-500 italic">No online record</span>
                          )}
                        </td>
                        <td className="py-2.5 px-3 text-right font-medium">
                          {verificationResult.comparison_result.course_match_score >= 0.75 ? (
                            <span className="text-emerald-400">{(verificationResult.comparison_result.course_match_score * 100).toFixed(0)}% ✅</span>
                          ) : (
                            <span className="text-rose-400">{(verificationResult.comparison_result.course_match_score * 100).toFixed(0)}% ❌</span>
                          )}
                        </td>
                      </tr>

                      <tr>
                        <td className="py-2.5 px-3 font-medium text-slate-400">Certificate ID</td>
                        <td className="py-2.5 px-3 font-semibold text-slate-100">
                          {verificationResult.extracted_fields.certificate_id || 'Not Extracted'}
                        </td>
                        <td className="py-2.5 px-3">
                          {verificationResult.comparison_result.online_record?.certificate_id || (
                            <span className="text-slate-500 italic">No online record</span>
                          )}
                        </td>
                        <td className="py-2.5 px-3 text-right font-medium">
                          {verificationResult.comparison_result.cert_id_match_score >= 0.85 ? (
                            <span className="text-emerald-400">{(verificationResult.comparison_result.cert_id_match_score * 100).toFixed(0)}% ✅</span>
                          ) : (
                            <span className="text-rose-400">{(verificationResult.comparison_result.cert_id_match_score * 100).toFixed(0)}% ❌</span>
                          )}
                        </td>
                      </tr>

                      <tr>
                        <td className="py-2.5 px-3 font-medium text-slate-400">Issuer Provider</td>
                        <td className="py-2.5 px-3 font-semibold text-slate-100">
                          {verificationResult.extracted_fields.issuer || 'Unknown'}
                        </td>
                        <td className="py-2.5 px-3">
                          {verificationResult.url_result.resolved_issuer || 'Unverified'}
                        </td>
                        <td className="py-2.5 px-3 text-right font-medium">
                          {verificationResult.url_result.is_known_issuer ? (
                            <span className="text-emerald-400">Trusted ✅</span>
                          ) : (
                            <span className="text-amber-400">Unknown ⚠️</span>
                          )}
                        </td>
                      </tr>
                    </tbody>
                  </table>
                </div>
              </div>

              {/* Forensics & Multi-Signal Meters */}
              <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                <div className="p-5 rounded-2xl bg-slate-900/60 border border-slate-800 space-y-3">
                  <h4 className="text-xs font-semibold text-slate-200 flex items-center space-x-1.5">
                    <Fingerprint className="w-4 h-4 text-teal-400" />
                    <span>Pixel & Document Forensics</span>
                  </h4>
                  <div className="space-y-2 text-xs">
                    <div className="flex justify-between">
                      <span className="text-slate-400">Tampering Probability:</span>
                      <span className={verificationResult.forensic_result.tampering_probability > 0.4 ? 'text-rose-400 font-bold' : 'text-slate-200'}>
                        {(verificationResult.forensic_result.tampering_probability * 100).toFixed(1)}%
                      </span>
                    </div>
                    <div className="flex justify-between">
                      <span className="text-slate-400">Copy-Move Duplication:</span>
                      <span className={verificationResult.forensic_result.copy_move_detected ? 'text-rose-400 font-bold' : 'text-emerald-400'}>
                        {verificationResult.forensic_result.copy_move_detected ? 'Detected ❌' : 'Clean ✅'}
                      </span>
                    </div>
                    <div className="flex justify-between">
                      <span className="text-slate-400">Noise Inconsistency:</span>
                      <span className="text-slate-200">
                        {verificationResult.forensic_result.noise_inconsistency_score.toFixed(3)}
                      </span>
                    </div>
                  </div>
                </div>

                <div className="p-5 rounded-2xl bg-slate-900/60 border border-slate-800 space-y-3">
                  <h4 className="text-xs font-semibold text-slate-200 flex items-center space-x-1.5">
                    <QrCode className="w-4 h-4 text-emerald-400" />
                    <span>QR Code & Signature Analysis</span>
                  </h4>
                  <div className="space-y-2 text-xs">
                    <div className="flex justify-between">
                      <span className="text-slate-400">QR Code Decoded:</span>
                      <span className={verificationResult.qr_result.qr_decoded ? 'text-emerald-400 font-bold' : 'text-slate-400'}>
                        {verificationResult.qr_result.qr_decoded ? 'Decoded ✅' : 'Absent / Unreadable'}
                      </span>
                    </div>
                    <div className="flex justify-between">
                      <span className="text-slate-400">Signature Stroke Presence:</span>
                      <span className="text-slate-200">
                        {verificationResult.seal_signature_result?.signature_detected ? 'Detected ✅' : 'Standard Text'}
                      </span>
                    </div>
                    <div className="flex justify-between">
                      <span className="text-slate-400">Institutional Seal:</span>
                      <span className="text-slate-200">
                        {verificationResult.seal_signature_result?.seal_detected ? 'Detected ✅' : 'Not Found'}
                      </span>
                    </div>
                  </div>
                </div>
              </div>

              {/* Explanatory Findings & Audit Action */}
              <div className="p-6 rounded-2xl bg-slate-900/60 border border-slate-800 backdrop-blur-xl shadow-xl space-y-4">
                <h4 className="text-xs font-semibold text-slate-200">Decision Rationale & Audit Findings</h4>
                <ul className="space-y-1.5 text-xs text-slate-300 list-disc list-inside">
                  {verificationResult.decision.decision_reasons.map((r, i) => (
                    <li key={i} className="text-slate-300">{r}</li>
                  ))}
                  {verificationResult.decision.risk_factors.map((rf, i) => (
                    <li key={`rf-${i}`} className="text-rose-400 font-medium">▲ {rf}</li>
                  ))}
                </ul>

                <div className="pt-4 border-t border-slate-800 flex items-center justify-between">
                  <span className="text-xs text-slate-500">
                    Audit ID: {verificationResult.verification_id}
                  </span>

                  <button
                    onClick={handleDownloadPdf}
                    disabled={isDownloadingPdf}
                    className="py-2 px-4 rounded-xl bg-slate-800 hover:bg-slate-700 text-slate-200 font-medium text-xs flex items-center space-x-2 border border-slate-700 transition-all cursor-pointer"
                  >
                    {isDownloadingPdf ? (
                      <Loader2 className="w-4 h-4 animate-spin text-emerald-400" />
                    ) : (
                      <Download className="w-4 h-4 text-emerald-400" />
                    )}
                    <span>Download Official Audit Report (PDF)</span>
                  </button>
                </div>
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
};
export default CourseVerificationPage;
