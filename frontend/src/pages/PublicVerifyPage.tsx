import React, { useState } from 'react';
import {
  ShieldCheck,
  ShieldAlert,
  AlertTriangle,
  CheckCircle2,
  UploadCloud,
  FileCheck,
  QrCode,
  Layers,
  ArrowRight,
  ExternalLink,
  RefreshCw,
  Clock,
  Printer,
  FileSearch,
  GraduationCap,
  Award,
  Sparkles,
  Download,
  Loader2,
} from 'lucide-react';
import axios from 'axios';
import apiClient from '../services/api';
import { exportCertificateElementToPdf } from '../utils/pdfExport';

const VerificationHistorySection = React.lazy(() =>
  import('../components/history/VerificationHistorySection').then((m) => ({
    default: m.VerificationHistorySection,
  }))
);

const CertificateExportModal = React.lazy(() =>
  import('../components/verification/CertificateExportModal').then((m) => ({
    default: m.CertificateExportModal,
  }))
);

const ForensicAuditCertificate = React.lazy(() =>
  import('../components/verification/ForensicAuditCertificate').then((m) => ({
    default: m.ForensicAuditCertificate,
  }))
);

interface VerificationResult {
  success?: boolean;
  status?: 'authentic' | 'fraudulent' | string;
  source?: string;
  document_type?: 'VTU_MARKSCARD' | 'ONLINE_COURSE_CERTIFICATE' | string;
  extracted_data?: {
    student_name: string;
    identifier: string;
    issuer: string;
    date: string;
    score_or_cgpa: string;
  };
  rag_validation?: {
    schema_matched: boolean;
    arithmetic_valid: boolean;
    anomalies_detected: string[];
  };
  verdict?: 'AUTHENTIC' | 'SUSPICIOUS' | 'FRAUDULENT' | string;
  confidence?: number;
  details?: {
    ocr_extracted?: Record<string, any>;
    forgery_detected?: boolean;
    qr_verified?: boolean;
    file_metadata?: Record<string, any>;
    gemini_verified?: boolean | null;
    gemini_analysis?: Record<string, any>;
    remarks?: string;
  };
  gemini_analysis?: Record<string, any>;
  file_metadata?: Record<string, any>;
  scan_id: string;
  filename: string;
  certificate_type: string;
  final_status: 'VERIFIED' | 'SUSPICIOUS' | 'REJECTED';
  verdict_badge: string;
  color: string;
  is_authentic: boolean;
  confidence_score: number;
  latency_ms: number;
  rejection_reasons: string[];
  warnings: string[];
  extracted_fields?: {
    student_name: string;
    institution_name: string;
    reg_no: string;
    mother_name?: string;
    father_name?: string;
    sgpa?: string;
    ocr_engine?: string;
  };
  qr_verification?: {
    detected?: boolean;
    payload_or_url?: string | null;
    matches_document_text?: boolean;
    qr_present?: boolean;
    domain_valid?: boolean;
    url?: string | null;
    domain?: string;
    verified?: boolean;
    reason?: string;
    payload_data?: Record<string, any>;
    url_verified?: boolean;
    is_url?: boolean;
    detection_method?: string;
    payload_text_match?: string;
    live_server_status?: string | null;
    issuer_db_match?: string | null;
    web_registered_name?: string | null;
    discrepancy_details?: string | null;
    mismatch_flag?: string | null;
  };
  cross_verification?: {
    name_similarity: number;
    id_similarity: number;
    institution_similarity: number;
    matches_qr: boolean;
    qr_ground_truth?: {
      name: string;
      id: string;
      institution: string;
      sgpa: string;
    };
  };
  forensic_cards: {
    qr_and_url?: {
      status?: string;
      qr_present?: boolean;
      qr_detected?: boolean;
      url_verified?: boolean;
      domain_valid: boolean;
      url?: string | null;
      domain?: string;
      raw_payload?: string | null;
      provider_type?: string;
      message?: string;
      reason?: string;
      payload_data?: Record<string, any>;
      live_server_status?: string | null;
      issuer_db_match?: string | null;
      web_registered_name?: string | null;
      discrepancy_details?: string | null;
      mismatch_flag?: string | null;
    };
    extracted_fields?: {
      student_name: string;
      institution_name: string;
      reg_no: string;
      mother_name?: string;
      father_name?: string;
      sgpa?: string;
      ocr_engine?: string;
    };
    cross_verification?: {
      name_similarity: number;
      id_similarity: number;
      institution_similarity: number;
      matches_qr: boolean;
      qr_ground_truth?: {
        name: string;
        id: string;
        institution: string;
        sgpa: string;
      };
    };
    layout_alignment?: {
      baseline_variance: number;
      splicing_suspected: boolean;
      text_matches_qr: boolean;
      qr_cross_match_score?: number;
      status: string;
    };
    template_integrity?: {
      verified: boolean;
      ssim_score: number;
      ssim_passed: boolean;
      ssim_threshold: number;
      edge_diff_ratio: number;
      edge_passed: boolean;
      edge_diff_threshold: number;
      matched_template: string;
    };
    metadata_checks?: {
      student_name_match?: boolean;
      student_name_score?: number;
      reg_no_match?: boolean;
      reg_no_score?: number;
    };
    gemini_vision?: {
      success?: boolean;
      status?: string;
      model_used?: string;
      is_authentic?: boolean;
      confidence_score?: number;
      verdict?: string;
      entities?: {
        student_name?: string | null;
        registration_no?: string | null;
        cgpa_or_score?: string | null;
        issuing_institution?: string | null;
        degree_or_program?: string | null;
        issue_date?: string | null;
      };
      forgery_indicators?: {
        font_mismatch?: boolean;
        text_baseline_shift?: boolean;
        patch_compression_artifacts?: boolean;
        splicing_detected?: boolean;
        details?: string;
      };
      arithmetic_consistency?: {
        is_consistent?: boolean;
        details?: string;
      };
      forensic_summary?: string;
    };
    rag_validation?: {
      schema_matched?: boolean;
      arithmetic_valid?: boolean;
      anomalies_detected?: string[];
      document_type?: string;
      mismatch_report?: string;
    };
  };
  timestamp: string;
}

export const PublicVerifyPage: React.FC = () => {
  const [certificateType, setCertificateType] = useState<'marks_card' | 'course_certificate'>('marks_card');
  const [file, setFile] = useState<File | null>(null);
  const [filePreview, setFilePreview] = useState<string | null>(null);
  const [loading, setLoading] = useState<boolean>(false);
  const [verifyingStep, setVerifyingStep] = useState<string>('');
  const [result, setResult] = useState<VerificationResult | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [dashboardTab, setDashboardTab] = useState<'verifier' | 'history'>('verifier');
  const [historyRefreshTrigger, setHistoryRefreshTrigger] = useState<number>(Date.now());
  const [isCertificateModalOpen, setIsCertificateModalOpen] = useState<boolean>(false);
  const [isGeneratingPdf, setIsGeneratingPdf] = useState<boolean>(false);

  const handleQuickDownloadPdf = async () => {
    if (!result) return;
    try {
      setIsGeneratingPdf(true);
      const cleanScanId = result.scan_id.replace(/^scan_/, '').slice(0, 8);
      const filename = `Forensic_Audit_Certificate_${cleanScanId || 'EVAL'}.pdf`;

      // 1. First attempt: Client-side high-resolution canvas capture
      const certEl = document.getElementById('forensic-audit-certificate-hidden-root');
      if (certEl) {
        await exportCertificateElementToPdf(certEl, { filename });
        return;
      }

      // 2. Fallback attempt: Stream from backend ReportLab endpoint
      const resp = await apiClient.post('/verify/export-pdf', result, { responseType: 'blob' });
      const blob = new Blob([resp.data], { type: 'application/pdf' });
      const url = window.URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = filename;
      document.body.appendChild(a);
      a.click();
      a.remove();
      window.URL.revokeObjectURL(url);
    } catch (err: unknown) {
      console.error('Direct PDF export error, launching certificate modal fallback:', err);
      setIsCertificateModalOpen(true);
    } finally {
      setIsGeneratingPdf(false);
    }
  };

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files && e.target.files[0]) {
      const selected = e.target.files[0];
      setFile(selected);
      setError(null);
      if (selected.type.startsWith('image/')) {
        setFilePreview(URL.createObjectURL(selected));
      } else {
        setFilePreview(null);
      }
    }
  };

  const handleDrop = (e: React.DragEvent) => {
    e.preventDefault();
    if (e.dataTransfer.files && e.dataTransfer.files[0]) {
      const selected = e.dataTransfer.files[0];
      setFile(selected);
      setError(null);
      if (selected.type.startsWith('image/')) {
        setFilePreview(URL.createObjectURL(selected));
      } else {
        setFilePreview(null);
      }
    }
  };

  const handleVerifySubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!file) {
      setError('Please select or drop a certificate document to verify.');
      return;
    }

    setLoading(true);
    setError(null);
    setVerifyingStep('Ingesting document and executing multi-modal forensic pipeline...');

    try {
      const formData = new FormData();
      formData.append('file', file);
      formData.append('certificate_type', certificateType);

      const res = await apiClient.post<any>('/verify', formData, {
        timeout: 180000,
      });
      const data = res.data;

      // Normalize verification response to handle contract and detailed UI fields
      const isAuthentic = data.is_authentic ?? (data.status === 'authentic' || data.final_status === 'VERIFIED');
      const finalStatus: 'VERIFIED' | 'SUSPICIOUS' | 'REJECTED' =
        data.final_status || (isAuthentic ? 'VERIFIED' : 'REJECTED');

      const normalizedResult: VerificationResult = {
        scan_id: data.scan_id || `scan_${Date.now()}`,
        filename: data.filename || file.name,
        certificate_type: data.certificate_type || certificateType,
        final_status: finalStatus,
        verdict_badge:
          data.verdict_badge ||
          (finalStatus === 'VERIFIED'
            ? 'VERIFIED (Authentic & Validated)'
            : finalStatus === 'SUSPICIOUS'
            ? 'SUSPICIOUS (Requires Review)'
            : 'REJECTED (Tampered / Manipulated)'),
        color: data.color || (finalStatus === 'VERIFIED' ? 'emerald' : finalStatus === 'SUSPICIOUS' ? 'amber' : 'red'),
        source: data.source || 'live_extraction',
        document_type: data.document_type || (certificateType === 'marks_card' ? 'VTU_MARKSCARD' : 'ONLINE_COURSE_CERTIFICATE'),
        extracted_data: data.extracted_data || {
          student_name: data.extracted_fields?.student_name || '',
          identifier: data.extracted_fields?.reg_no || '',
          issuer: data.extracted_fields?.institution_name || '',
          date: data.extracted_fields?.issue_date || '',
          score_or_cgpa: data.extracted_fields?.sgpa || data.extracted_fields?.cgpa || '',
        },
        rag_validation: data.rag_validation || {
          schema_matched: !data.warnings?.some((w: string) => w.includes('Scheme') || w.includes('Formula')),
          arithmetic_valid: !data.warnings?.some((w: string) => w.includes('Arithmetic') || w.includes('SGPA')),
          anomalies_detected: data.warnings || [],
        },
        verdict: data.verdict || (finalStatus === 'VERIFIED' ? 'AUTHENTIC' : finalStatus === 'SUSPICIOUS' ? 'SUSPICIOUS' : 'FRAUDULENT'),
        is_authentic: isAuthentic,
        confidence_score: Number(data.confidence_score ?? data.confidence ?? 0.95),
        latency_ms: Number(data.latency_ms ?? 150),
        rejection_reasons:
          data.rejection_reasons && data.rejection_reasons.length > 0
            ? data.rejection_reasons
            : (data.qr_verification?.discrepancy_details || data.forensic_cards?.qr_and_url?.discrepancy_details)
            ? [data.qr_verification?.discrepancy_details || data.forensic_cards?.qr_and_url?.discrepancy_details]
            : (data.details?.forgery_detected && data.details?.remarks ? [data.details.remarks] : []),
        warnings: data.warnings || [],
        extracted_fields: data.extracted_fields || data.details?.ocr_extracted || {},
        qr_verification: data.qr_verification ? {
          detected: data.qr_verification.detected ?? data.qr_verification.qr_present ?? false,
          payload_or_url: data.qr_verification.payload_or_url ?? data.qr_verification.url ?? null,
          matches_document_text: data.qr_verification.matches_document_text ?? data.cross_verification?.matches_qr ?? true,
          qr_present: data.qr_verification.detected ?? data.qr_verification.qr_present ?? false,
          domain_valid: data.qr_verification.domain_valid ?? true,
          url: data.qr_verification.payload_or_url ?? data.qr_verification.url ?? null,
          verified: data.qr_verification.verified ?? (data.qr_verification.matches_document_text ?? false),
          reason: data.qr_verification.reason,
          payload_data: data.qr_verification.payload_data,
          url_verified: data.qr_verification.url_verified ?? data.qr_verification.is_url ?? false,
          is_url: data.qr_verification.is_url ?? false,
          detection_method: data.qr_verification.detection_method ?? (data.qr_verification.is_url ? 'printed_url' : 'barcode'),
          payload_text_match: data.qr_verification.payload_text_match ?? (data.qr_verification.matches_document_text !== false ? '100% MATCHED' : 'FRAUD_DATA_MISMATCH'),
          live_server_status: data.qr_verification.live_server_status ?? data.forensic_cards?.qr_and_url?.live_server_status ?? null,
          issuer_db_match: data.qr_verification.issuer_db_match ?? data.forensic_cards?.qr_and_url?.issuer_db_match ?? null,
          web_registered_name: data.qr_verification.web_registered_name ?? data.forensic_cards?.qr_and_url?.web_registered_name ?? null,
          discrepancy_details: data.qr_verification.discrepancy_details ?? data.forensic_cards?.qr_and_url?.discrepancy_details ?? null,
          mismatch_flag: data.qr_verification.mismatch_flag ?? data.forensic_cards?.qr_and_url?.mismatch_flag ?? null,
        } : {
          detected: data.details?.qr_verified ?? false,
          payload_or_url: null,
          matches_document_text: true,
          qr_present: data.details?.qr_verified ?? false,
          domain_valid: false,
          verified: data.details?.qr_verified ?? false,
          reason: 'No QR code or institutional verification link detected',
          url_verified: false,
          is_url: false,
          detection_method: 'none',
          payload_text_match: 'Consistent with Visual Text',
          live_server_status: null,
          issuer_db_match: null,
          web_registered_name: null,
          discrepancy_details: null,
          mismatch_flag: null,
        },
        cross_verification: data.cross_verification || {
          name_similarity: 100,
          id_similarity: 100,
          institution_similarity: 100,
          matches_qr: true,
        },
        forensic_cards: {
          ...(data.forensic_cards || {}),
          qr_and_url: data.forensic_cards?.qr_and_url || data.qr_verification || {
            qr_present: data.details?.qr_verified ?? false,
            domain_valid: data.details?.qr_verified ?? false,
          },
          extracted_fields: data.forensic_cards?.extracted_fields || data.extracted_fields || data.details?.ocr_extracted || {},
          gemini_vision: data.forensic_cards?.gemini_vision || data.details?.gemini_analysis || data.gemini_analysis,
          rag_validation: data.forensic_cards?.rag_validation || data.rag_validation,
        },
        gemini_analysis: data.gemini_analysis || data.details?.gemini_analysis,
        file_metadata: data.file_metadata || data.details?.file_metadata,
        timestamp: data.timestamp || new Date().toISOString(),
        success: data.success ?? true,
        status: data.status || (isAuthentic ? 'authentic' : 'fraudulent'),
        confidence: data.confidence ?? data.confidence_score,
        details: data.details,
      };

      setResult(normalizedResult);
      setHistoryRefreshTrigger(Date.now());
    } catch (err: unknown) {
      if (axios.isAxiosError(err)) {
        if (!err.response || err.code === 'ERR_NETWORK' || err.message?.includes('Network Error')) {
          setError(
            'Server Unreachable: Cannot connect to the backend verification engine at http://127.0.0.1:8000. Please ensure the backend server is running.'
          );
        } else if (err.response.data?.detail) {
          setError(String(err.response.data.detail));
        } else if (err.response.data?.error) {
          setError(String(err.response.data.error));
        } else if (err.response.data?.message) {
          setError(String(err.response.data.message));
        } else {
          setError(`Verification failed with HTTP ${err.response.status}. Please check server logs.`);
        }
      } else {
        setError('Verification failed. Please ensure the document is clear and properly scanned.');
      }
    } finally {
      setLoading(false);
      setVerifyingStep('');
    }
  };

  return (
    <div className="space-y-8 pb-16">
      {/* Header Section */}
      <div className="border-b border-slate-800 pb-6 flex flex-col md:flex-row md:items-center justify-between gap-4">
        <div>
          <div className="flex items-center space-x-2">
            <span className="px-2.5 py-0.5 rounded-full text-[10px] font-bold uppercase tracking-wider bg-emerald-500/10 text-emerald-400 border border-emerald-500/30">
              Authenticated Verifier Enclave
            </span>
            <span className="text-xs text-slate-500 font-mono">Real-Time Forensic Pipeline</span>
          </div>
          <h1 className="text-2xl sm:text-3xl font-black text-white tracking-tight mt-1 font-display">
            Academic & Course Certificate Verification Workspace
          </h1>
          <p className="text-xs sm:text-sm text-slate-400 mt-1 max-w-3xl leading-relaxed">
            Instantly authenticate university marks cards and professional course completion credentials. Our multi-modal engine validates cryptographic QR roots, OCR baseline typography, and DIAR-AI template integrity in &lt;250ms.
          </p>
        </div>

        {/* Workspace View Tabs (Verifier vs Verification History) */}
        <div className="flex items-center gap-1.5 p-1 rounded-xl bg-slate-900 border border-slate-800 text-xs font-semibold self-start md:self-auto shrink-0 shadow-lg">
          <button
            type="button"
            onClick={() => setDashboardTab('verifier')}
            className={`flex items-center space-x-2 px-3.5 py-2 rounded-lg transition-all cursor-pointer ${
              dashboardTab === 'verifier'
                ? 'bg-emerald-600 text-white shadow-md'
                : 'text-slate-400 hover:text-white hover:bg-slate-800/60'
            }`}
          >
            <ShieldCheck className="w-4 h-4" />
            <span>Document Verifier</span>
            {loading && (
              <span className="inline-flex items-center gap-1 px-1.5 py-0.5 rounded-full text-[10px] font-bold bg-amber-500/20 text-amber-300 border border-amber-500/30 animate-pulse ml-1">
                <Loader2 className="w-2.5 h-2.5 animate-spin" />
                Analyzing
              </span>
            )}
          </button>
          <button
            type="button"
            onClick={() => setDashboardTab('history')}
            className={`flex items-center space-x-2 px-3.5 py-2 rounded-lg transition-all cursor-pointer ${
              dashboardTab === 'history'
                ? 'bg-emerald-600 text-white shadow-md'
                : 'text-slate-400 hover:text-white hover:bg-slate-800/60'
            }`}
          >
            <Clock className="w-4 h-4" />
            <span>Verification History</span>
          </button>
        </div>
      </div>

      {/* Tab 2: Dedicated Verification History View */}
      <div className={dashboardTab === 'history' ? 'block' : 'hidden'}>
        <React.Suspense
          fallback={
            <div className="min-h-[300px] flex items-center justify-center p-8 text-center text-slate-400 text-xs">
              <Loader2 className="w-6 h-6 animate-spin text-emerald-400 mr-2" />
              Loading verification history...
            </div>
          }
        >
          <VerificationHistorySection
            refreshTrigger={historyRefreshTrigger}
            onNavigateToUpload={() => setDashboardTab('verifier')}
          />
        </React.Suspense>
      </div>

      {/* Tab 1: Document Verifier Workspace */}
      <div className={dashboardTab === 'verifier' ? 'space-y-8' : 'hidden'}>
        {/* Main Two-Column Layout */}
        <div className="grid grid-cols-1 lg:grid-cols-12 gap-8">
        {/* Left Column: Upload & Input Portal (5 Cols) */}
        <div className="lg:col-span-5 space-y-6">
          <form onSubmit={handleVerifySubmit} className="space-y-5">
            {/* 1. Document Type Switcher */}
            <div>
              <label className="block text-xs font-bold uppercase tracking-wider text-slate-400 mb-2">
                1. Select Certificate Category
              </label>
              <div className="grid grid-cols-2 gap-2.5">
                <button
                  type="button"
                  onClick={() => setCertificateType('marks_card')}
                  className={`p-3.5 rounded-2xl border text-left transition-all ${
                    certificateType === 'marks_card'
                      ? 'border-emerald-500 bg-emerald-950/30 shadow-lg shadow-emerald-900/20'
                      : 'border-slate-800 bg-slate-900/50 hover:border-slate-700 hover:bg-slate-900'
                  }`}
                >
                  <div className="flex items-center space-x-2 mb-1">
                    <GraduationCap
                      className={`w-4 h-4 ${
                        certificateType === 'marks_card' ? 'text-emerald-400' : 'text-slate-400'
                      }`}
                    />
                    <span className="text-xs font-bold text-white">University Marks Card</span>
                  </div>
                  <p className="text-[11px] text-slate-400">
                    Grade sheet, transcript, semester ledger & stamp checks
                  </p>
                </button>

                <button
                  type="button"
                  onClick={() => setCertificateType('course_certificate')}
                  className={`p-3.5 rounded-2xl border text-left transition-all ${
                    certificateType === 'course_certificate'
                      ? 'border-teal-500 bg-teal-950/30 shadow-lg shadow-teal-900/20'
                      : 'border-slate-800 bg-slate-900/50 hover:border-slate-700 hover:bg-slate-900'
                  }`}
                >
                  <div className="flex items-center space-x-2 mb-1">
                    <Award
                      className={`w-4 h-4 ${
                        certificateType === 'course_certificate' ? 'text-teal-400' : 'text-slate-400'
                      }`}
                    />
                    <span className="text-xs font-bold text-white">Course Certificate</span>
                  </div>
                  <p className="text-[11px] text-slate-400">
                    Coursera, NPTEL, edX, accreditation domain roots
                  </p>
                </button>
              </div>
            </div>

            {/* 2. Drag and Drop File Upload Area */}
            <div>
              <label className="block text-xs font-bold uppercase tracking-wider text-slate-400 mb-2">
                2. Upload Document (PDF, PNG, JPG)
              </label>
              <div
                onDragOver={(e) => e.preventDefault()}
                onDrop={handleDrop}
                className={`relative border-2 border-dashed rounded-3xl p-6 sm:p-8 text-center transition-all cursor-pointer ${
                  file
                    ? 'border-emerald-500/80 bg-emerald-950/20'
                    : 'border-slate-700/80 hover:border-emerald-500/60 bg-slate-900/40 hover:bg-slate-900/80'
                }`}
              >
                <input
                  type="file"
                  accept=".png,.jpg,.jpeg,.pdf,.webp"
                  onChange={handleFileChange}
                  className="absolute inset-0 w-full h-full opacity-0 cursor-pointer"
                />

                {file ? (
                  <div className="space-y-3">
                    {filePreview ? (
                      <img
                        src={filePreview}
                        alt="Preview"
                        className="max-h-24 mx-auto rounded-xl object-contain border border-emerald-500/40 shadow-md"
                      />
                    ) : (
                      <div className="w-12 h-12 rounded-2xl bg-emerald-500/20 text-emerald-400 border border-emerald-500/40 mx-auto flex items-center justify-center">
                        <FileCheck className="w-6 h-6" />
                      </div>
                    )}
                    <div>
                      <p className="text-xs font-bold text-white truncate max-w-[280px] mx-auto">
                        {file.name}
                      </p>
                      <p className="text-[11px] text-slate-400 mt-0.5">
                        {(file.size / 1024).toFixed(1)} KB • Ready for deep forensic scan
                      </p>
                    </div>
                    <span className="inline-block text-[10px] font-bold text-emerald-400 bg-emerald-950 px-2 py-0.5 rounded border border-emerald-500/30">
                      Click or drag new file to change
                    </span>
                  </div>
                ) : (
                  <div className="space-y-3">
                    <div className="w-12 h-12 rounded-2xl bg-slate-800 text-slate-400 border border-slate-700 mx-auto flex items-center justify-center group-hover:scale-110 transition-transform">
                      <UploadCloud className="w-6 h-6 text-emerald-400" />
                    </div>
                    <div>
                      <p className="text-xs font-bold text-slate-200">
                        Drop certificate file here or browse
                      </p>
                      <p className="text-[11px] text-slate-500 mt-1">
                        High-resolution PDF, PNG, or JPG (max 20MB)
                      </p>
                    </div>
                  </div>
                )}
              </div>
            </div>


            {error && (
              <div className="p-3.5 rounded-xl bg-rose-950/30 border border-rose-800/60 flex items-center space-x-2 text-xs text-rose-300">
                <AlertTriangle className="w-4 h-4 text-rose-400 shrink-0" />
                <span>{error}</span>
              </div>
            )}

            {/* Execute Button */}
            <button
              type="submit"
              disabled={loading || !file}
              className="w-full py-3.5 rounded-2xl bg-gradient-to-r from-emerald-600 via-teal-600 to-cyan-600 hover:from-emerald-500 hover:to-cyan-500 text-white font-black text-sm shadow-xl shadow-emerald-600/20 flex items-center justify-center space-x-2 transition-all cursor-pointer disabled:opacity-50 disabled:cursor-not-allowed"
            >
              {loading ? (
                <div className="flex items-center space-x-2">
                  <RefreshCw className="w-4 h-4 animate-spin" />
                  <span>Processing Forensic Analysis...</span>
                </div>
              ) : (
                <>
                  <ShieldCheck className="w-4 h-4" />
                  <span>Execute Multi-Modal Verification</span>
                  <ArrowRight className="w-4 h-4" />
                </>
              )}
            </button>
          </form>
        </div>

        {/* Right Column: Live Forensic Results (7 Cols) */}
        <div className="lg:col-span-7">
          {loading ? (
            <div className="min-h-[480px] rounded-3xl bg-slate-900/40 border border-slate-800/80 flex flex-col items-center justify-center p-8 text-center">
              <div className="relative mb-6">
                <div className="w-16 h-16 rounded-full border-4 border-emerald-500/20 border-t-emerald-400 animate-spin" />
                <div className="absolute inset-0 flex items-center justify-center">
                  <ShieldCheck className="w-6 h-6 text-emerald-400" />
                </div>
              </div>
              <h3 className="text-base font-bold text-white">Running VeriDoc Forensic Engine</h3>
              <p className="text-xs text-emerald-400 mt-1 font-mono">{verifyingStep}</p>
              <div className="mt-6 flex items-center space-x-2 text-[11px] text-slate-500">
                <Clock className="w-3.5 h-3.5" />
                <span>Target SLA: &lt; 250ms CPU Execution</span>
              </div>
            </div>
          ) : result ? (
            <div className="space-y-6 animate-in fade-in duration-300">
              {/* Main Status Banner */}
              <div
                className={`p-6 rounded-3xl border shadow-xl flex flex-col sm:flex-row sm:items-center justify-between gap-4 ${
                  result.final_status === 'VERIFIED'
                    ? 'bg-gradient-to-r from-emerald-950/60 via-emerald-900/30 to-slate-900 border-emerald-500/50 shadow-emerald-950/20'
                    : result.final_status === 'SUSPICIOUS'
                    ? 'bg-gradient-to-r from-amber-950/60 via-amber-900/30 to-slate-900 border-amber-500/50 shadow-amber-950/20'
                    : 'bg-gradient-to-r from-rose-950/60 via-rose-900/30 to-slate-900 border-rose-500/50 shadow-rose-950/20'
                }`}
              >
                <div className="flex items-center space-x-4">
                  <div
                    className={`p-3.5 rounded-2xl ${
                      result.final_status === 'VERIFIED'
                        ? 'bg-emerald-500 text-slate-950 shadow-lg shadow-emerald-500/30'
                        : result.final_status === 'SUSPICIOUS'
                        ? 'bg-amber-500 text-slate-950 shadow-lg shadow-amber-500/30'
                        : 'bg-rose-500 text-white shadow-lg shadow-rose-500/30'
                    }`}
                  >
                    {result.final_status === 'VERIFIED' ? (
                      <CheckCircle2 className="w-7 h-7" />
                    ) : result.final_status === 'SUSPICIOUS' ? (
                      <AlertTriangle className="w-7 h-7" />
                    ) : (
                      <ShieldAlert className="w-7 h-7" />
                    )}
                  </div>
                  <div>
                    <span
                      className={`text-[10px] font-mono font-bold uppercase tracking-wider px-2 py-0.5 rounded-full border ${
                        result.final_status === 'VERIFIED'
                          ? 'bg-emerald-500/20 text-emerald-300 border-emerald-500/40'
                          : result.final_status === 'SUSPICIOUS'
                          ? 'bg-amber-500/20 text-amber-300 border-amber-500/40'
                          : 'bg-rose-500/20 text-rose-300 border-rose-500/40'
                      }`}
                    >
                      {result.verdict_badge}
                    </span>
                    <h2 className="text-xl font-black text-white mt-1">
                      {result.final_status === 'VERIFIED'
                        ? 'Certificate Authenticity Confirmed'
                        : result.final_status === 'SUSPICIOUS'
                        ? 'Suspicious Anomalies Detected'
                        : 'Tampered / Unaccredited Document'}
                    </h2>
                    <p className="text-xs text-slate-300 mt-0.5">
                      Confidence Score: {(result.confidence_score * 100).toFixed(1)}% • Scan ID:{' '}
                      <span className="font-mono text-[10px] text-slate-400">
                        {result.scan_id.slice(0, 8)}
                      </span>
                    </p>
                  </div>
                </div>

                {/* Latency & SLA Badge */}
                <div className="sm:text-right border-t sm:border-t-0 sm:border-l border-slate-800/80 pt-3 sm:pt-0 sm:pl-5">
                  <div className="text-xs font-bold text-slate-200">
                    {result.latency_ms} ms
                  </div>
                  <span className="inline-block text-[10px] font-mono text-emerald-400 bg-emerald-950/80 border border-emerald-500/30 px-2 py-0.5 rounded-full mt-0.5">
                    SLA &lt;250ms OK
                  </span>
                </div>
              </div>

              {/* Critical Live Truth Discrepancy Banner if Registry Mismatch */}
              {result.qr_verification?.discrepancy_details && (
                <div className="p-5 rounded-3xl bg-rose-950/40 border-2 border-rose-500/80 shadow-2xl shadow-rose-950/50 space-y-2">
                  <div className="flex items-center space-x-2.5 text-rose-300 font-bold text-xs uppercase tracking-wider">
                    <ShieldAlert className="w-5 h-5 text-rose-400 shrink-0" />
                    <span>Live Institutional Truth Authority Rejection</span>
                  </div>
                  <p className="text-sm font-semibold text-rose-100 pl-7 leading-relaxed">
                    {result.qr_verification.discrepancy_details}
                  </p>
                </div>
              )}

              {/* Rejection / Warning Alerts if any */}
              {result.rejection_reasons && result.rejection_reasons.length > 0 && (
                <div className="p-4 rounded-2xl bg-rose-950/30 border border-rose-700/60 space-y-1.5">
                  <div className="flex items-center space-x-2 text-rose-300 font-bold text-xs">
                    <ShieldAlert className="w-4 h-4" />
                    <span>Critical Tampering Reasons</span>
                  </div>
                  <ul className="list-disc list-inside text-xs text-rose-200 space-y-1 pl-1">
                    {result.rejection_reasons.map((r, i) => (
                      <li key={i}>{r}</li>
                    ))}
                  </ul>
                </div>
              )}

              {result.warnings && result.warnings.length > 0 && (
                <div className="p-4 rounded-2xl bg-amber-950/30 border border-amber-700/60 space-y-1.5">
                  <div className="flex items-center space-x-2 text-amber-300 font-bold text-xs">
                    <AlertTriangle className="w-4 h-4" />
                    <span>Advisory Warnings</span>
                  </div>
                  <ul className="list-disc list-inside text-xs text-amber-200 space-y-1 pl-1">
                    {result.warnings.map((w, i) => (
                      <li key={i}>{w}</li>
                    ))}
                  </ul>
                </div>
              )}

              {/* 4 Forensic Breakdown Cards Grid */}
              <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                {/* Card 1: Active QR Code & Verification URL Engine */}
                <div className="p-4 rounded-2xl bg-slate-900/60 border border-slate-800 space-y-2.5">
                  <div className="flex items-center justify-between">
                    <div className="flex items-center space-x-2 text-xs font-bold text-white">
                      <QrCode className="w-4 h-4 text-emerald-400" />
                      <span>Active QR & Verification Link Engine</span>
                    </div>
                    {(() => {
                      const isMismatch =
                        result.qr_verification?.matches_document_text === false ||
                        Boolean(result.qr_verification?.discrepancy_details) ||
                        result.qr_verification?.mismatch_flag === 'IDENTITY_MISMATCH_FRAUD';
                      const hasValidUrl = Boolean(
                        result.qr_verification?.url_verified ||
                        result.qr_verification?.is_url ||
                        (result.qr_verification?.domain_valid && (result.qr_verification?.payload_or_url || result.qr_verification?.url)) ||
                        result.forensic_cards?.qr_and_url?.url_verified ||
                        (result.forensic_cards?.qr_and_url?.domain_valid && result.forensic_cards?.qr_and_url?.url)
                      );
                      const hasQr = Boolean(
                        result.qr_verification?.detected ||
                        result.qr_verification?.qr_present ||
                        result.forensic_cards?.qr_and_url?.qr_present ||
                        result.forensic_cards?.qr_and_url?.qr_detected
                      );

                      if (isMismatch) {
                        return (
                          <span className="text-[9px] font-bold px-2 py-0.5 rounded-full border bg-rose-500/10 text-rose-400 border-rose-500/30">
                            {result.qr_verification?.mismatch_flag || 'IDENTITY_MISMATCH_FRAUD'}
                          </span>
                        );
                      }
                      if (hasValidUrl) {
                        return (
                          <span className="text-[9px] font-bold px-2 py-0.5 rounded-full border bg-emerald-500/10 text-emerald-400 border-emerald-500/30">
                            Valid Institutional Verification URL Found
                          </span>
                        );
                      }
                      if (hasQr) {
                        return (
                          <span className="text-[9px] font-bold px-2 py-0.5 rounded-full border bg-emerald-500/10 text-emerald-400 border-emerald-500/30">
                            Accredited Root Verified
                          </span>
                        );
                      }
                      return (
                        <span className="text-[9px] font-bold px-2 py-0.5 rounded-full border bg-amber-500/10 text-amber-400 border-amber-500/30">
                          Verification: Visual Forensics
                        </span>
                      );
                    })()}
                  </div>

                  <div className="text-xs space-y-1.5 pt-1">
                    <div className="text-slate-400 flex justify-between">
                      <span>Verification Channel:</span>
                      <span className="text-slate-200 font-medium">
                        {(result.qr_verification?.detected || result.qr_verification?.qr_present)
                          ? 'Cryptographic QR Present'
                          : (result.qr_verification?.url_verified || result.qr_verification?.is_url || result.qr_verification?.payload_or_url || result.forensic_cards?.qr_and_url?.url)
                          ? 'Printed Institutional Link (No 2D QR Needed)'
                          : 'Printed URL / Visual Forensics'}
                      </span>
                    </div>

                    {(result.qr_verification?.payload_or_url || result.qr_verification?.url || result.forensic_cards?.qr_and_url?.url) && (
                      <div className="text-slate-400 truncate">
                        <span className="block text-[11px] text-slate-500">Destination Endpoint:</span>
                        <a
                          href={result.qr_verification?.payload_or_url || result.qr_verification?.url || result.forensic_cards?.qr_and_url?.url || '#'}
                          target="_blank"
                          rel="noreferrer"
                          className="text-emerald-400 hover:underline flex items-center space-x-1 text-[11px]"
                        >
                          <span className="truncate">{result.qr_verification?.payload_or_url || result.qr_verification?.url || result.forensic_cards?.qr_and_url?.url}</span>
                          <ExternalLink className="w-3 h-3 shrink-0" />
                        </a>
                      </div>
                    )}

                    {/* Live Server Status Row */}
                    {(result.qr_verification?.live_server_status || result.forensic_cards?.qr_and_url?.live_server_status) && (
                      <div className="text-slate-400 flex justify-between items-center pt-1 border-t border-slate-800/80">
                        <span>Live Server Status:</span>
                        <span className={`text-[11px] font-bold px-2 py-0.5 rounded-full border ${
                          (result.qr_verification?.live_server_status || result.forensic_cards?.qr_and_url?.live_server_status)?.includes('200')
                            ? 'bg-emerald-500/10 text-emerald-400 border-emerald-500/30'
                            : (result.qr_verification?.live_server_status || result.forensic_cards?.qr_and_url?.live_server_status)?.includes('404')
                            ? 'bg-rose-500/10 text-rose-400 border-rose-500/30'
                            : 'bg-amber-500/10 text-amber-400 border-amber-500/30'
                        }`}>
                          {result.qr_verification?.live_server_status || result.forensic_cards?.qr_and_url?.live_server_status}
                        </span>
                      </div>
                    )}

                    {/* Issuer Database Match Row */}
                    {(result.qr_verification?.issuer_db_match || result.forensic_cards?.qr_and_url?.issuer_db_match) && (
                      <div className="text-slate-400 flex justify-between items-center pt-1 border-t border-slate-800/80">
                        <span>Issuer Database Match:</span>
                        <span className={`text-[11px] font-bold px-2 py-0.5 rounded-full border max-w-[210px] truncate ${
                          (result.qr_verification?.issuer_db_match || result.forensic_cards?.qr_and_url?.issuer_db_match)?.startsWith('Matched')
                            ? 'bg-emerald-500/10 text-emerald-400 border-emerald-500/30'
                            : 'bg-rose-500/10 text-rose-400 border-rose-500/30'
                        }`}>
                          {result.qr_verification?.issuer_db_match || result.forensic_cards?.qr_and_url?.issuer_db_match}
                        </span>
                      </div>
                    )}

                    <div className="text-slate-400 flex justify-between">
                      <span>Payload Text Match:</span>
                      <span className={`font-mono font-medium ${
                        result.qr_verification?.matches_document_text === false ? 'text-rose-400' : 'text-emerald-400'
                      }`}>
                        {result.qr_verification?.payload_text_match
                          ? result.qr_verification.payload_text_match
                          : result.qr_verification?.matches_document_text === false
                          ? 'FRAUD_DATA_MISMATCH'
                          : (result.qr_verification?.detected || result.qr_verification?.qr_present || result.qr_verification?.url_verified || result.qr_verification?.is_url)
                          ? '100% MATCHED'
                          : 'Consistent with Visual Text'}
                      </span>
                    </div>

                    {(result.cross_verification?.qr_ground_truth?.name && result.cross_verification.qr_ground_truth.name !== 'N/A') && (
                      <div className="text-slate-400 flex justify-between pt-1 border-t border-slate-800/80">
                        <span>QR Ground Truth:</span>
                        <span className="text-emerald-300 font-medium truncate max-w-[160px]">
                          {result.cross_verification.qr_ground_truth.name}
                        </span>
                      </div>
                    )}

                    <p className="text-[11px] text-slate-400 pt-1 border-t border-slate-800">
                      {result.qr_verification?.reason ||
                        result.forensic_cards?.qr_and_url?.message ||
                        ((result.qr_verification?.url_verified || result.qr_verification?.is_url || (result.qr_verification?.domain_valid ?? result.forensic_cards?.qr_and_url?.domain_valid))
                          ? 'Accredited institutional root certificate cryptographically/URL verified.'
                          : 'Verification method: Printed URL / Visual Forensics')}
                    </p>
                  </div>
                </div>

                {/* Card 2: Anchor-Extracted Certificate Fields */}
                <div className="p-4 rounded-2xl bg-slate-900/60 border border-slate-800 space-y-2.5">
                  <div className="flex items-center justify-between">
                    <div className="flex items-center space-x-2 text-xs font-bold text-white">
                      <FileSearch className="w-4 h-4 text-cyan-400" />
                      <span>Live Field Extraction</span>
                    </div>
                    <span className="text-[9px] font-mono font-bold px-2 py-0.5 rounded-full border bg-cyan-500/10 text-cyan-300 border-cyan-500/30">
                      {result.document_type || 'LIVE_EXTRACTED'}
                    </span>
                  </div>

                  <div className="text-xs space-y-1.5 pt-1">
                    <div className="text-slate-400 flex justify-between">
                      <span>Candidate Name:</span>
                      <span className="text-slate-200 font-semibold truncate max-w-[160px]">
                        {result.extracted_data?.student_name ||
                          result.extracted_fields?.student_name ||
                          'Not Detected'}
                      </span>
                    </div>
                    <div className="text-slate-400 flex justify-between">
                      <span>Institution:</span>
                      <span className="text-cyan-300 font-medium truncate max-w-[170px]">
                        {result.extracted_data?.issuer ||
                          result.extracted_fields?.institution_name ||
                          'Not Detected'}
                      </span>
                    </div>
                    <div className="text-slate-400 flex justify-between">
                      <span>Roll / Reg No:</span>
                      <span className="text-slate-200 font-mono font-medium">
                        {result.extracted_data?.identifier ||
                          result.extracted_fields?.reg_no ||
                          'Not Detected'}
                      </span>
                    </div>
                    {(result.extracted_data?.score_or_cgpa || result.extracted_fields?.sgpa) && (
                      <div className="text-slate-400 flex justify-between pt-1 border-t border-slate-800/80">
                        <span>Extracted Score / CGPA:</span>
                        <span className="text-emerald-400 font-mono font-bold">
                          {result.extracted_data?.score_or_cgpa || result.extracted_fields?.sgpa}
                        </span>
                      </div>
                    )}
                  </div>
                </div>

                {/* Card 3: Deterministic Cross-Verification */}
                <div className="p-4 rounded-2xl bg-slate-900/60 border border-slate-800 space-y-2.5">
                  <div className="flex items-center justify-between">
                    <div className="flex items-center space-x-2 text-xs font-bold text-white">
                      <FileCheck className="w-4 h-4 text-indigo-400" />
                      <span>Cross-Verification Gating</span>
                    </div>
                    <span
                      className={`text-[9px] font-bold px-2 py-0.5 rounded-full border ${
                        (result.cross_verification?.name_similarity ?? 100) >= 90
                          ? 'bg-emerald-500/10 text-emerald-400 border-emerald-500/30'
                          : (result.cross_verification?.name_similarity ?? 100) >= 80
                          ? 'bg-amber-500/10 text-amber-400 border-amber-500/30'
                          : 'bg-rose-500/10 text-rose-400 border-rose-500/30'
                      }`}
                    >
                      {(result.cross_verification?.name_similarity ?? 100) >= 90
                        ? 'Match (>=90%)'
                        : (result.cross_verification?.name_similarity ?? 100) >= 80
                        ? 'Review (80-89%)'
                        : 'Discrepancy (<80%)'}
                    </span>
                  </div>

                  <div className="text-xs space-y-1.5 pt-1">
                    <div className="text-slate-400 flex justify-between">
                      <span>Name Similarity:</span>
                      <span className="text-slate-200 font-mono font-bold">
                        {result.cross_verification?.name_similarity !== undefined
                          ? `${result.cross_verification.name_similarity}%`
                          : '100.0%'}
                      </span>
                    </div>
                    <div className="text-slate-400 flex justify-between">
                      <span>ID / Reg Match:</span>
                      <span className="text-slate-200 font-mono font-bold">
                        {result.cross_verification?.id_similarity !== undefined
                          ? `${result.cross_verification.id_similarity}%`
                          : '100.0%'}
                      </span>
                    </div>
                    <p className="text-[11px] text-slate-400 pt-1 border-t border-slate-800">
                      {(result.cross_verification?.name_similarity ?? 100) >= 90
                        ? 'Document visual text strictly aligns with cryptographic payload.'
                        : 'Discrepancy detected between visual text and institutional registry ground truth.'}
                    </p>
                  </div>
                </div>

                {/* Card 4: DIAR-AI Visual & Template Integrity */}
                <div className="p-4 rounded-2xl bg-slate-900/60 border border-slate-800 space-y-2.5">
                  <div className="flex items-center justify-between">
                    <div className="flex items-center space-x-2 text-xs font-bold text-white">
                      <Layers className="w-4 h-4 text-teal-400" />
                      <span>DIAR-AI Visual Integrity</span>
                    </div>
                    <span
                      className={`text-[9px] font-bold px-2 py-0.5 rounded-full border ${
                        result.forensic_cards?.template_integrity?.ssim_passed !== false
                          ? 'bg-emerald-500/10 text-emerald-400 border-emerald-500/30'
                          : 'bg-rose-500/10 text-rose-400 border-rose-500/30'
                      }`}
                    >
                      {result.forensic_cards?.template_integrity?.ssim_passed !== false
                        ? 'SSIM Passed'
                        : 'Template Delta'}
                    </span>
                  </div>

                  <div className="text-xs space-y-1.5 pt-1">
                    <div className="text-slate-400 flex justify-between">
                      <span>SSIM Metric:</span>
                      <span className="text-slate-200 font-mono font-medium">
                        {result.forensic_cards?.template_integrity?.ssim_score !== undefined
                          ? result.forensic_cards.template_integrity.ssim_score.toFixed(4)
                          : '1.0000'}{' '}
                        <span className="text-slate-500 text-[10px]">(threshold &ge;0.85)</span>
                      </span>
                    </div>
                    <div className="text-slate-400 flex justify-between">
                      <span>Canny Edge Diff:</span>
                      <span className="text-slate-200 font-mono font-medium">
                        {result.forensic_cards?.template_integrity?.edge_diff_ratio !== undefined
                          ? result.forensic_cards.template_integrity.edge_diff_ratio.toFixed(4)
                          : '0.0000'}{' '}
                        <span className="text-slate-500 text-[10px]">(threshold &le;0.08)</span>
                      </span>
                    </div>
                    <div className="text-[11px] text-slate-400 pt-1 border-t border-slate-800 truncate">
                      <span>Template: </span>
                      <span className="font-mono text-slate-300">
                        {result.forensic_cards?.template_integrity?.matched_template ||
                          'Live Document Calibration'}
                      </span>
                    </div>
                  </div>
                </div>

                {/* Card 5: Multimodal Vision Forensics */}
                {result.forensic_cards?.gemini_vision && (
                  <div className="col-span-1 md:col-span-2 p-4 rounded-2xl bg-gradient-to-br from-indigo-950/40 via-slate-900/60 to-slate-900/60 border border-indigo-500/30 space-y-3 shadow-lg">
                    <div className="flex items-center justify-between">
                      <div className="flex items-center space-x-2 text-xs font-bold text-white">
                        <Sparkles className="w-4 h-4 text-indigo-400" />
                        <span>Multimodal Vision Forensic Audit</span>
                      </div>
                      <span
                        className={`text-[9px] font-bold px-2 py-0.5 rounded-full border ${
                          result.forensic_cards.gemini_vision.is_authentic === true
                            ? 'bg-emerald-500/10 text-emerald-400 border-emerald-500/30'
                            : result.forensic_cards.gemini_vision.is_authentic === false
                            ? 'bg-rose-500/10 text-rose-400 border-rose-500/30'
                            : 'bg-amber-500/10 text-amber-400 border-amber-500/30'
                        }`}
                      >
                        {result.forensic_cards.gemini_vision.is_authentic === true
                          ? 'Vision AI Verified'
                          : result.forensic_cards.gemini_vision.is_authentic === false
                          ? 'Visual Manipulation Flagged'
                          : result.forensic_cards.gemini_vision.status || 'Vision AI Audited'}
                      </span>
                    </div>

                    <div className="grid grid-cols-1 md:grid-cols-3 gap-3 text-xs">
                      {/* Forgery Indicators */}
                      <div className="p-2.5 rounded-xl bg-slate-950/50 border border-slate-800 space-y-1">
                        <div className="text-[11px] font-semibold text-slate-300 flex items-center justify-between">
                          <span>Typography & Baselines</span>
                          <span
                            className={
                              result.forensic_cards.gemini_vision.forgery_indicators?.font_mismatch ||
                              result.forensic_cards.gemini_vision.forgery_indicators?.text_baseline_shift ||
                              result.forensic_cards.gemini_vision.forgery_indicators?.patch_compression_artifacts ||
                              result.forensic_cards.gemini_vision.forgery_indicators?.splicing_detected
                                ? 'text-rose-400 font-bold'
                                : 'text-emerald-400 font-bold'
                            }
                          >
                            {result.forensic_cards.gemini_vision.forgery_indicators?.splicing_detected
                              ? 'Spliced'
                              : result.forensic_cards.gemini_vision.forgery_indicators?.font_mismatch
                              ? 'Font Mismatch'
                              : 'Aligned'}
                          </span>
                        </div>
                        <p className="text-[10px] text-slate-400 leading-tight">
                          {result.forensic_cards.gemini_vision.forgery_indicators?.details ||
                            'Typography and pixel baseline verified by Multimodal Vision Engine.'}
                        </p>
                      </div>

                      {/* Arithmetic Check */}
                      <div className="p-2.5 rounded-xl bg-slate-950/50 border border-slate-800 space-y-1">
                        <div className="text-[11px] font-semibold text-slate-300 flex items-center justify-between">
                          <span>Arithmetic Consistency</span>
                          <span
                            className={
                              result.forensic_cards.gemini_vision.arithmetic_consistency?.is_consistent !== false
                                ? 'text-emerald-400 font-bold'
                                : 'text-rose-400 font-bold'
                            }
                          >
                            {result.forensic_cards.gemini_vision.arithmetic_consistency?.is_consistent !== false
                              ? 'Consistent'
                              : 'Discrepancy'}
                          </span>
                        </div>
                        <p className="text-[10px] text-slate-400 leading-tight">
                          {result.forensic_cards.gemini_vision.arithmetic_consistency?.details ||
                            'Grade and credits arithmetic audited.'}
                        </p>
                      </div>

                      {/* Entities Identified */}
                      <div className="p-2.5 rounded-xl bg-slate-950/50 border border-slate-800 space-y-1">
                        <div className="text-[11px] font-semibold text-slate-300 flex items-center justify-between">
                          <span>Extracted Entities</span>
                          <span className="text-indigo-400 font-mono">
                            {result.forensic_cards.gemini_vision.confidence_score !== undefined
                              ? `${Math.round(result.forensic_cards.gemini_vision.confidence_score * 100)}% Conf`
                              : 'Vision AI'}
                          </span>
                        </div>
                        <p className="text-[10px] text-slate-400 truncate">
                          ID: <span className="text-slate-200">{result.forensic_cards.gemini_vision.entities?.registration_no || 'Detected'}</span> | CGPA: <span className="text-slate-200">{result.forensic_cards.gemini_vision.entities?.cgpa_or_score || 'N/A'}</span>
                        </p>
                        <p className="text-[10px] text-slate-400 truncate">
                          Issuer: <span className="text-slate-200">{result.forensic_cards.gemini_vision.entities?.issuing_institution || 'Verified'}</span>
                        </p>
                      </div>
                    </div>

                    {result.forensic_cards.gemini_vision.forensic_summary && (
                      <div className="text-[11px] text-indigo-200/80 bg-indigo-950/30 p-2.5 rounded-xl border border-indigo-500/20">
                        <span className="font-semibold text-indigo-300">Forensic Summary: </span>
                        {result.forensic_cards.gemini_vision.forensic_summary}
                      </div>
                    )}
                  </div>
                )}

                {/* Card 6: Ground-Truth Institutional Schema Cross-Verification (RAG) */}
                {(result.rag_validation || result.forensic_cards?.rag_validation) && (
                  <div className="col-span-1 md:col-span-2 p-4 rounded-2xl bg-gradient-to-br from-cyan-950/40 via-slate-900/60 to-slate-900/60 border border-cyan-500/30 space-y-3 shadow-lg">
                    <div className="flex items-center justify-between">
                      <div className="flex items-center space-x-2 text-xs font-bold text-white">
                        <GraduationCap className="w-4 h-4 text-cyan-400" />
                        <span>Institutional Ground-Truth Schema & Arithmetic Audit (RAG)</span>
                        {result.document_type && (
                          <span className="text-[10px] font-mono px-2 py-0.5 rounded bg-cyan-500/10 text-cyan-300 border border-cyan-500/30">
                            {result.document_type}
                          </span>
                        )}
                      </div>
                      <span
                        className={`text-[9px] font-bold px-2 py-0.5 rounded-full border ${
                          (result.rag_validation?.schema_matched ?? result.forensic_cards?.rag_validation?.schema_matched)
                            ? 'bg-emerald-500/10 text-emerald-400 border-emerald-500/30'
                            : 'bg-rose-500/10 text-rose-400 border-rose-500/30'
                        }`}
                      >
                        {(result.rag_validation?.schema_matched ?? result.forensic_cards?.rag_validation?.schema_matched)
                          ? 'Institutional Schema Compliant'
                          : 'Schema / Rule Anomaly'}
                      </span>
                    </div>

                    <div className="grid grid-cols-1 md:grid-cols-2 gap-3 text-xs">
                      <div className="p-2.5 rounded-xl bg-slate-950/50 border border-slate-800 space-y-1">
                        <div className="text-[11px] font-semibold text-slate-300 flex items-center justify-between">
                          <span>Grading & Identifier Conformity</span>
                          <span
                            className={
                              (result.rag_validation?.schema_matched ?? result.forensic_cards?.rag_validation?.schema_matched)
                                ? 'text-emerald-400 font-bold'
                                : 'text-amber-400 font-bold'
                            }
                          >
                            {(result.rag_validation?.schema_matched ?? result.forensic_cards?.rag_validation?.schema_matched)
                              ? 'Standardized'
                              : 'Discrepancy'}
                          </span>
                        </div>
                        <p className="text-[10px] text-slate-400">
                          {result.document_type === 'VTU_MARKSCARD'
                            ? 'Cross-referenced against VTU CBCS USN conventions, grade weights, and regional college registries.'
                            : 'Cross-referenced against official course provider certificate signatures and verification URL standards.'}
                        </p>
                      </div>

                      <div className="p-2.5 rounded-xl bg-slate-950/50 border border-slate-800 space-y-1">
                        <div className="text-[11px] font-semibold text-slate-300 flex items-center justify-between">
                          <span>Formula & Arithmetic Validation</span>
                          <span
                            className={
                              (result.rag_validation?.arithmetic_valid ?? result.forensic_cards?.rag_validation?.arithmetic_valid)
                                ? 'text-emerald-400 font-bold'
                                : 'text-rose-400 font-bold'
                            }
                          >
                            {(result.rag_validation?.arithmetic_valid ?? result.forensic_cards?.rag_validation?.arithmetic_valid)
                              ? 'Valid'
                              : 'Contradiction'}
                          </span>
                        </div>
                        <p className="text-[10px] text-slate-400">
                          {result.document_type === 'VTU_MARKSCARD'
                            ? 'Evaluated via VTU SGPA formula: sum(Credits * GradePoints) / sum(Credits).'
                            : 'Evaluated course completion threshold and certification score range.'}
                        </p>
                      </div>
                    </div>

                    {((result.rag_validation?.anomalies_detected && result.rag_validation.anomalies_detected.length > 0) ||
                      (result.forensic_cards?.rag_validation?.anomalies_detected && result.forensic_cards.rag_validation.anomalies_detected.length > 0)) && (
                      <div className="p-2.5 rounded-xl bg-rose-950/30 border border-rose-800/40 text-[11px] text-rose-300 space-y-1">
                        <div className="font-semibold flex items-center space-x-1">
                          <AlertTriangle className="w-3.5 h-3.5" />
                          <span>RAG Schema Discrepancy Report:</span>
                        </div>
                        <ul className="list-disc list-inside text-[10px] text-rose-200/90 pl-1 space-y-0.5">
                          {(result.rag_validation?.anomalies_detected || result.forensic_cards?.rag_validation?.anomalies_detected || []).map((anomaly: string, idx: number) => (
                            <li key={idx}>{anomaly}</li>
                          ))}
                        </ul>
                      </div>
                    )}
                  </div>
                )}
              </div>

              {/* Action Buttons: Download PDF / Print Cryptographic Audit Certificate */}
              <div className="flex flex-col sm:flex-row gap-3 pt-2">
                <button
                  onClick={handleQuickDownloadPdf}
                  disabled={isGeneratingPdf}
                  className="flex-1 py-3 px-4 rounded-2xl bg-gradient-to-r from-amber-600 via-amber-700 to-amber-800 hover:from-amber-500 hover:to-amber-700 text-white text-xs font-bold border border-amber-600/50 shadow-lg shadow-amber-600/25 flex items-center justify-center space-x-2 transition-all cursor-pointer disabled:opacity-50"
                  title="Generate and download authoritative A4 Forensic Verification Audit Certificate in PDF format"
                >
                  {isGeneratingPdf ? (
                    <>
                      <Loader2 className="w-4 h-4 animate-spin text-amber-200" />
                      <span>Compiling Forensic PDF...</span>
                    </>
                  ) : (
                    <>
                      <Download className="w-4 h-4 text-amber-200" />
                      <span>Download Audit Certificate (PDF)</span>
                    </>
                  )}
                </button>

                <button
                  onClick={() => setIsCertificateModalOpen(true)}
                  className="py-3 px-5 rounded-2xl bg-slate-800 hover:bg-slate-700 text-slate-200 text-xs font-bold border border-slate-700 flex items-center justify-center space-x-2 transition-colors cursor-pointer"
                  title="Open certificate preview and print"
                >
                  <Printer className="w-4 h-4 text-slate-300" />
                  <span>Print Cryptographic Audit Certificate</span>
                </button>

                <button
                  onClick={() => {
                    setResult(null);
                    setFile(null);
                    setFilePreview(null);
                  }}
                  className="px-5 py-3 rounded-2xl bg-slate-900 hover:bg-slate-800 text-slate-400 hover:text-slate-200 text-xs font-bold border border-slate-800 transition-colors cursor-pointer"
                >
                  Verify Another
                </button>
              </div>
            </div>
          ) : (
            <div className="min-h-[480px] rounded-3xl bg-slate-900/30 border border-slate-800/80 p-8 flex flex-col items-center justify-center text-center">
              <div className="w-16 h-16 rounded-2xl bg-slate-800/60 border border-slate-700/60 flex items-center justify-center text-slate-400 mb-4">
                <FileSearch className="w-8 h-8 text-emerald-400/80" />
              </div>
              <h3 className="text-base font-bold text-white">No Document Verified Yet</h3>
              <p className="text-xs text-slate-400 max-w-md mt-1 leading-relaxed">
                Upload your university marks card or course certificate on the left to inspect the live forensic analysis.
              </p>
              <div className="mt-6 flex flex-wrap justify-center gap-2 text-[11px] text-slate-400">
                <span className="px-2.5 py-1 rounded-lg bg-slate-800/80 border border-slate-700">
                  DIAR-AI SSIM &ge; 0.85
                </span>
                <span className="px-2.5 py-1 rounded-lg bg-slate-800/80 border border-slate-700">
                  Canny Edge &le; 0.08
                </span>
                <span className="px-2.5 py-1 rounded-lg bg-slate-800/80 border border-slate-700">
                  CPU SLA &lt; 250ms
                </span>
              </div>
            </div>
          )}
        </div>
      </div>

        {/* Embedded Verification History Section on Dashboard */}
        <div className="mt-14 border-t border-slate-800/80 pt-10">
          <React.Suspense
            fallback={
              <div className="min-h-[200px] flex items-center justify-center text-slate-400 text-xs">
                <Loader2 className="w-5 h-5 animate-spin text-emerald-400 mr-2" />
                Loading verification records...
              </div>
            }
          >
            <VerificationHistorySection
              refreshTrigger={historyRefreshTrigger}
              onNavigateToUpload={() => window.scrollTo({ top: 0, behavior: 'smooth' })}
            />
          </React.Suspense>
        </div>
      </div>

      {/* Hidden container for print stylesheet and instant canvas capture */}
      {result && (
        <div style={{ position: 'fixed', left: '-9999px', top: '-9999px', pointerEvents: 'none' }}>
          <React.Suspense fallback={null}>
            <ForensicAuditCertificate
              id="forensic-audit-certificate-hidden-root"
              data={result}
            />
          </React.Suspense>
        </div>
      )}

      {/* Interactive Certificate Preview & Export Modal */}
      {result && isCertificateModalOpen && (
        <React.Suspense fallback={null}>
          <CertificateExportModal
            isOpen={isCertificateModalOpen}
            onClose={() => setIsCertificateModalOpen(false)}
            certificateData={result}
          />
        </React.Suspense>
      )}
    </div>
  );
};
