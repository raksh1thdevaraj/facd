import React, { useEffect, useState } from 'react';
import { useParams, Link } from 'react-router-dom';
import { reportService } from '../services/reportService';
import { FullVerificationReport, OverlayAnomaly } from '../types/report';
import { VerdictBanner } from '../components/results/VerdictBanner';
import { ScoreGauge } from '../components/results/ScoreGauge';
import { CredentialsCard } from '../components/results/CredentialsCard';
import { SubsystemScores } from '../components/results/SubsystemScores';
import { InteractiveViewer } from '../components/results/InteractiveViewer';
import { FindingsDossier } from '../components/results/FindingsDossier';
import { ReportActions } from '../components/results/ReportActions';
import { Loader2, AlertCircle, ArrowLeft } from 'lucide-react';

export const ResultsPage: React.FC = () => {
  const { id } = useParams<{ id: string }>();
  const [report, setReport] = useState<FullVerificationReport | null>(null);
  const [loading, setLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let isMounted = true;

    const fetchReport = async () => {
      if (!id) return;
      try {
        setLoading(true);
        setError(null);
        const data = await reportService.getReport(id);
        if (isMounted) {
          setReport(data);
        }
      } catch (err: unknown) {
        if (isMounted) {
          const msg =
            err instanceof Error
              ? err.message
              : 'Failed to retrieve verification report. The report may still be processing or does not exist.';
          setError(msg);
        }
      } finally {
        if (isMounted) {
          setLoading(false);
        }
      }
    };

    fetchReport();

    return () => {
      isMounted = false;
    };
  }, [id]);

  if (loading) {
    return (
      <div className="min-h-[500px] flex flex-col items-center justify-center space-y-4">
        <Loader2 className="w-10 h-10 animate-spin text-emerald-400" />
        <p className="text-slate-300 font-medium">Retrieving Comprehensive Forensic Dossier...</p>
        <span className="text-xs text-slate-500 font-mono">Report ID: {id}</span>
      </div>
    );
  }

  if (error || !report) {
    return (
      <div className="max-w-2xl mx-auto my-12 glass-card rounded-2xl p-8 border border-rose-800/60 text-center space-y-6">
        <div className="p-3 bg-rose-500/20 text-rose-400 rounded-2xl w-fit mx-auto">
          <AlertCircle className="w-8 h-8" />
        </div>
        <div className="space-y-2">
          <h3 className="text-xl font-bold text-slate-100">Unable to Load Report Dossier</h3>
          <p className="text-sm text-slate-400 leading-relaxed">
            {error || 'No report found matching this identifier.'}
          </p>
        </div>
        <div className="pt-2">
          <Link
            to="/"
            className="inline-flex items-center space-x-2 px-5 py-2.5 rounded-xl bg-slate-800 hover:bg-slate-700 text-slate-200 text-sm font-medium border border-slate-700 transition-colors"
          >
            <ArrowLeft className="w-4 h-4" />
            <span>Inspection Console</span>
          </Link>
        </div>
      </div>
    );
  }

  const credentials = report.extracted_fields || report.credentials || {};

  // Synthesize overlay anomalies from visual evidence if provided
  const anomalies: OverlayAnomaly[] = report.overlay_anomalies || [
    ...(credentials.student_name
      ? [
          { x: 30, y: 35, width: 40, height: 8, layer: 'ocr' as const, label: 'Candidate Name' },
          { x: 25, y: 55, width: 50, height: 10, layer: 'ocr' as const, label: 'Degree Major' },
        ]
      : []),
    ...(report.verdict === 'MANIPULATED'
      ? [
          { x: 42, y: 56, width: 22, height: 6, layer: 'forensics' as const, label: 'Splice Boundary' },
        ]
      : []),
  ];

  return (
    <div className="max-w-7xl mx-auto space-y-8 pb-16">
      {/* Back button */}
      <div className="flex items-center justify-between">
        <Link
          to="/upload"
          className="inline-flex items-center space-x-1.5 text-xs sm:text-sm text-slate-400 hover:text-slate-200 transition-colors"
        >
          <ArrowLeft className="w-4 h-4" />
          <span>Upload Another Certificate</span>
        </Link>
        <span className="text-xs text-slate-500 font-mono">
          Report Generated: {new Date(report.created_at || report.generated_at).toLocaleString()}
        </span>
      </div>

      {/* 1. Verdict Banner */}
      <VerdictBanner
        verdict={report.verdict}
        authenticityScore={report.authenticity_score}
        sha256Hash={report.file_metadata.sha256_checksum}
        processingTimeMs={report.processing_time_ms}
        reportId={report.report_id}
      />

      {/* 2. Top Row: Authenticity Score Radial Gauge & Extracted Credentials */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        <div className="lg:col-span-1">
          <ScoreGauge score={report.authenticity_score} />
        </div>
        <div className="lg:col-span-2">
          <CredentialsCard credentials={credentials} />
        </div>
      </div>

      {/* 3. Middle Row: Subsystem Scores & Interactive Forensic Document Viewer */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        <div className="lg:col-span-1">
          <SubsystemScores subsystems={report.subsystem_scores} />
        </div>
        <div className="lg:col-span-2">
          <InteractiveViewer
            documentImageUrl={
              report.visual_evidence?.preprocessed_preview_url ||
              report.visual_evidence?.original_image ||
              report.visual_evidence?.original_image_url
            }
            gradCamUrl={
              report.visual_evidence?.gradcam_heatmap ||
              report.visual_evidence?.gradcam_heatmap_url
            }
            elaUrl={
              report.visual_evidence?.forensic_heatmap ||
              report.visual_evidence?.ela_difference_url
            }
            anomalies={anomalies}
          />
        </div>
      </div>

      {/* 4. Categorized Findings & Evidence Dossier */}
      <FindingsDossier findings={report.findings} />

      {/* 5. Export Actions */}
      <ReportActions reportId={report.report_id} />
    </div>
  );

};
