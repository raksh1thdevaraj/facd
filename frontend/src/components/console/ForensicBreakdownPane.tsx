import React from 'react';
import {
  CheckCircle2,
  AlertTriangle,
  XCircle,
  Calculator,
  ShieldCheck,
  User,
  Layers,
  Scale,
  Award,
} from 'lucide-react';

export interface SubjectMarksRecord {
  code: string;
  title: string;
  credits: number; // C_i
  grade: string; // e.g., 'A+', 'A', 'B+'
  gradePoints: number; // G_i
  qualityPoints: number; // C_i * G_i
  status?: 'PASS' | 'FAIL' | 'WITHHELD';
  tamperFlag?: boolean;
}

export interface StudentMetadata {
  name: string;
  usn: string;
  collegeName: string;
  collegeCode: string;
  semester: string;
  examinationCycle: string;
  degree: string;
  branch: string;
  fontConsistencyStatus: 'CONSISTENT' | 'SUSPICIOUS_KERNING' | 'BASELINE_SHIFT';
  fontAnomaliesDetected?: string[];
}

export interface SecuritySealInspection {
  crestResolution: 'PASS' | 'BLURRED' | 'SUSPICIOUS_ARTIFACT';
  crestScore: number;
  registrarSignature: 'PASS' | 'EDGE_TAMPERING' | 'MISSING';
  signatureScore: number;
  watermarkPresent: boolean;
  tamperingScore: number; // 0 to 100
  verdict: 'AUTHENTIC' | 'SUSPICIOUS' | 'FRAUDULENT';
  verdictReason: string;
}

export interface ArithmeticInspection {
  printedSgpa: number;
  calculatedSgpa: number;
  delta: number;
  totalCredits: number;
  totalQualityPoints: number;
  isDiscrepancy: boolean;
  verdictDetail: string;
}

interface ForensicBreakdownPaneProps {
  metadata?: StudentMetadata | null;
  subjectLedger?: SubjectMarksRecord[];
  arithmetic?: ArithmeticInspection | null;
  securitySeal?: SecuritySealInspection | null;
  onHoverRoi?: (roiId: string | null) => void;
  isEvaluating?: boolean;
}

export const ForensicBreakdownPane: React.FC<ForensicBreakdownPaneProps> = ({
  metadata,
  subjectLedger = [],
  arithmetic,
  securitySeal,
  onHoverRoi,
  isEvaluating: _isEvaluating = false,
}) => {
  if (!metadata && !subjectLedger.length && !arithmetic && !securitySeal) {
    return (
      <div className="h-full bg-white border border-slate-200 rounded-xl p-8 flex flex-col items-center justify-center text-center">
        <div className="w-12 h-12 rounded-xl bg-slate-50 border border-slate-200 text-slate-400 flex items-center justify-center mb-3">
          <Calculator className="w-6 h-6 text-slate-400" />
        </div>
        <h4 className="text-sm font-bold text-slate-800 mb-1">
          Forensic Breakdown Ready
        </h4>
        <p className="text-xs text-slate-500 max-w-xs leading-relaxed">
          Ingest a VTU marks card scan or select a pre-loaded test sample on the left to activate the real-time tabular analysis.
        </p>
      </div>
    );
  }

  // Verdict style mapping
  const verdictStyle =
    securitySeal?.verdict === 'AUTHENTIC'
      ? {
          badge: 'bg-emerald-50 text-emerald-800 border-emerald-200',
          icon: CheckCircle2,
          iconColor: 'text-emerald-700',
          label: 'AUTHENTIC (Cryptographically & Arithmetically Verified)',
        }
      : securitySeal?.verdict === 'SUSPICIOUS'
      ? {
          badge: 'bg-amber-50 text-amber-800 border-amber-200',
          icon: AlertTriangle,
          iconColor: 'text-amber-700',
          label: 'SUSPICIOUS (Requires Institutional Manual Review)',
        }
      : {
          badge: 'bg-rose-50 text-rose-800 border-rose-200',
          icon: XCircle,
          iconColor: 'text-rose-700',
          label: 'FRAUDULENT (Discrepancy / Manipulation Detected)',
        };

  return (
    <div className="h-full bg-white border border-slate-200 rounded-xl shadow-xs flex flex-col overflow-hidden">
      {/* Pane Header: Final Verdict & Score */}
      <div className="px-5 py-3.5 border-b border-slate-200 bg-slate-50 flex items-center justify-between shrink-0">
        <div className="flex items-center space-x-2">
          <ShieldCheck className="w-4 h-4 text-indigo-700" />
          <span className="font-semibold text-xs text-slate-900">
            Real-Time Institutional Forensic Ledger
          </span>
        </div>

        {securitySeal && (
          <div
            className={`inline-flex items-center space-x-1.5 px-3 py-1 rounded-md border text-xs font-bold ${verdictStyle.badge}`}
          >
            <verdictStyle.icon className={`w-3.5 h-3.5 ${verdictStyle.iconColor}`} />
            <span>{securitySeal.verdict}</span>
            <span className="font-mono text-[10px] opacity-75">
              (Tamper Index: {securitySeal.tamperingScore}%)
            </span>
          </div>
        )}
      </div>

      {/* Scrollable Forensic Cards Area */}
      <div className="flex-1 overflow-y-auto p-4 space-y-4">
        {/* Card 1: Extracted Student Metadata */}
        {metadata && (
          <div
            onMouseEnter={() => onHoverRoi && onHoverRoi('b1')}
            onMouseLeave={() => onHoverRoi && onHoverRoi(null)}
            className="border border-slate-200 hover:border-indigo-300 transition-colors rounded-lg p-3.5 bg-white shadow-2xs cursor-pointer"
          >
            <div className="flex items-center justify-between mb-3 border-b border-slate-100 pb-2">
              <div className="flex items-center space-x-2">
                <User className="w-3.5 h-3.5 text-indigo-700" />
                <h4 className="text-xs font-bold text-slate-800 uppercase tracking-wide">
                  Candidate Identity & Institutional Origin
                </h4>
              </div>
              <span
                className={`text-[10px] font-mono px-2 py-0.5 rounded border font-semibold ${
                  metadata.fontConsistencyStatus === 'CONSISTENT'
                    ? 'bg-emerald-50 text-emerald-800 border-emerald-200'
                    : 'bg-rose-50 text-rose-800 border-rose-200'
                }`}
              >
                Typography: {metadata.fontConsistencyStatus}
              </span>
            </div>

            <div className="grid grid-cols-2 sm:grid-cols-3 gap-2.5 text-xs">
              <div className="p-2 rounded bg-slate-50 border border-slate-100">
                <div className="text-[10px] text-slate-500 font-medium">Candidate Name</div>
                <div className="font-semibold text-slate-900 truncate" title={metadata.name}>
                  {metadata.name}
                </div>
              </div>

              <div className="p-2 rounded bg-slate-50 border border-slate-100">
                <div className="text-[10px] text-slate-500 font-medium">University Seat No (USN)</div>
                <div className="font-mono font-bold text-indigo-900">{metadata.usn}</div>
              </div>

              <div className="p-2 rounded bg-slate-50 border border-slate-100">
                <div className="text-[10px] text-slate-500 font-medium">College Code / Institution</div>
                <div className="font-semibold text-slate-900 truncate" title={metadata.collegeName}>
                  [{metadata.collegeCode}] {metadata.collegeName}
                </div>
              </div>

              <div className="p-2 rounded bg-slate-50 border border-slate-100">
                <div className="text-[10px] text-slate-500 font-medium">Branch / Specialization</div>
                <div className="font-medium text-slate-800 truncate">{metadata.branch}</div>
              </div>

              <div className="p-2 rounded bg-slate-50 border border-slate-100">
                <div className="text-[10px] text-slate-500 font-medium">Semester</div>
                <div className="font-medium text-slate-800">{metadata.semester}</div>
              </div>

              <div className="p-2 rounded bg-slate-50 border border-slate-100">
                <div className="text-[10px] text-slate-500 font-medium">Exam Session</div>
                <div className="font-medium text-slate-800">{metadata.examinationCycle}</div>
              </div>
            </div>

            {metadata.fontAnomaliesDetected && metadata.fontAnomaliesDetected.length > 0 && (
              <div className="mt-2.5 p-2 rounded bg-amber-50 border border-amber-200 text-amber-900 text-[11px] flex items-start space-x-1.5">
                <AlertTriangle className="w-3.5 h-3.5 text-amber-700 shrink-0 mt-0.5" />
                <div>
                  <span className="font-bold">Typography Anomaly: </span>
                  {metadata.fontAnomaliesDetected.join('; ')}
                </div>
              </div>
            )}
          </div>
        )}

        {/* Card 2: Deterministic Grade Point Calculation Engine (Tier 2 Verification) */}
        {arithmetic && (
          <div
            onMouseEnter={() => onHoverRoi && onHoverRoi('b4')}
            onMouseLeave={() => onHoverRoi && onHoverRoi(null)}
            className={`border rounded-lg p-3.5 transition-all cursor-pointer hover:border-indigo-300 ${
              arithmetic.isDiscrepancy
                ? 'bg-rose-50/50 border-rose-300 ring-1 ring-rose-400'
                : 'bg-white border-slate-200 shadow-2xs'
            }`}
          >
            <div className="flex items-center justify-between mb-3 border-b border-slate-100 pb-2">
              <div className="flex items-center space-x-2">
                <Scale className="w-3.5 h-3.5 text-indigo-700" />
                <h4 className="text-xs font-bold text-slate-800 uppercase tracking-wide">
                  Deterministic Institutional Arithmetic Engine
                </h4>
              </div>
              <span className="text-[10px] font-mono text-slate-500">
                Formula: SGPA = Σ(Ci × Gi) / ΣCi
              </span>
            </div>

            {/* SGPA Comparison Grid */}
            <div className="grid grid-cols-3 gap-3 text-center mb-3">
              <div className="p-2.5 rounded-lg bg-slate-50 border border-slate-200">
                <div className="text-[10px] uppercase font-semibold text-slate-500">
                  Printed SGPA
                </div>
                <div className="text-lg font-mono font-extrabold text-slate-900 mt-0.5">
                  {arithmetic.printedSgpa.toFixed(2)}
                </div>
                <div className="text-[9px] text-slate-400 font-mono">Scan Value</div>
              </div>

              <div
                className={`p-2.5 rounded-lg border ${
                  arithmetic.isDiscrepancy
                    ? 'bg-rose-50 border-rose-200 text-rose-900'
                    : 'bg-emerald-50 border-emerald-200 text-emerald-900'
                }`}
              >
                <div className="text-[10px] uppercase font-semibold text-slate-600">
                  Calculated SGPA
                </div>
                <div className="text-lg font-mono font-extrabold mt-0.5">
                  {arithmetic.calculatedSgpa.toFixed(2)}
                </div>
                <div className="text-[9px] opacity-75 font-mono">
                  {arithmetic.totalQualityPoints} / {arithmetic.totalCredits} Credits
                </div>
              </div>

              <div
                className={`p-2.5 rounded-lg border ${
                  arithmetic.isDiscrepancy
                    ? 'bg-rose-100 border-rose-300 text-rose-950 font-bold'
                    : 'bg-emerald-100 border-emerald-300 text-emerald-950 font-bold'
                }`}
              >
                <div className="text-[10px] uppercase font-semibold text-slate-600">
                  Arithmetic Delta (Δ)
                </div>
                <div className="text-lg font-mono font-extrabold mt-0.5">
                  {arithmetic.delta > 0 ? `+${arithmetic.delta.toFixed(2)}` : arithmetic.delta.toFixed(2)}
                </div>
                <div className="text-[9px] font-mono">
                  {arithmetic.delta <= 0.01 ? 'Zero Delta (Exact)' : 'Δ > 0.01 (Fraud!)'}
                </div>
              </div>
            </div>

            {/* Arithmetic Discrepancy Alert */}
            {arithmetic.isDiscrepancy ? (
              <div className="p-2.5 rounded bg-rose-100 border border-rose-300 text-rose-900 text-xs flex items-center space-x-2">
                <XCircle className="w-4 h-4 text-rose-700 shrink-0" />
                <div>
                  <span className="font-bold">CRITICAL ARITHMETIC DISCREPANCY: </span>
                  {arithmetic.verdictDetail}
                </div>
              </div>
            ) : (
              <div className="p-2 rounded bg-emerald-50 border border-emerald-200 text-emerald-900 text-[11px] flex items-center space-x-2">
                <CheckCircle2 className="w-3.5 h-3.5 text-emerald-700 shrink-0" />
                <span>Institutional credit-point calculations verified exact against printed SGPA.</span>
              </div>
            )}
          </div>
        )}

        {/* Card 3: Subject Marks Ledger */}
        {subjectLedger.length > 0 && (
          <div
            onMouseEnter={() => onHoverRoi && onHoverRoi('b3')}
            onMouseLeave={() => onHoverRoi && onHoverRoi(null)}
            className="border border-slate-200 hover:border-indigo-300 transition-colors rounded-lg p-3.5 bg-white shadow-2xs cursor-pointer"
          >
            <div className="flex items-center justify-between mb-2.5 border-b border-slate-100 pb-2">
              <div className="flex items-center space-x-2">
                <Layers className="w-3.5 h-3.5 text-indigo-700" />
                <h4 className="text-xs font-bold text-slate-800 uppercase tracking-wide">
                  Subject Marks & Quality Points Ledger
                </h4>
              </div>
              <span className="text-[10px] font-mono text-slate-500">
                {subjectLedger.length} Subjects Evaluated
              </span>
            </div>

            <div className="overflow-x-auto">
              <table className="w-full text-left text-xs border-collapse">
                <thead>
                  <tr className="border-b border-slate-200 bg-slate-50 text-[10px] font-semibold text-slate-600 uppercase tracking-wider">
                    <th className="py-1.5 px-2">Course Code</th>
                    <th className="py-1.5 px-2">Subject Title</th>
                    <th className="py-1.5 px-2 text-center">Credits (Ci)</th>
                    <th className="py-1.5 px-2 text-center">Grade</th>
                    <th className="py-1.5 px-2 text-center">Points (Gi)</th>
                    <th className="py-1.5 px-2 text-right">Quality (Ci×Gi)</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-100 font-mono text-[11px]">
                  {subjectLedger.map((sub, idx) => (
                    <tr
                      key={idx}
                      className={`hover:bg-slate-50 transition-colors ${
                        sub.tamperFlag ? 'bg-rose-50/70 font-semibold text-rose-900' : 'text-slate-700'
                      }`}
                    >
                      <td className="py-1.5 px-2 font-bold text-indigo-900">{sub.code}</td>
                      <td className="py-1.5 px-2 font-sans text-slate-800">{sub.title}</td>
                      <td className="py-1.5 px-2 text-center font-semibold">{sub.credits}</td>
                      <td className="py-1.5 px-2 text-center">
                        <span
                          className={`px-1.5 py-0.5 rounded text-[10px] font-bold ${
                            sub.grade === 'F'
                              ? 'bg-rose-100 text-rose-800'
                              : sub.grade === 'O' || sub.grade === 'A+'
                              ? 'bg-emerald-100 text-emerald-800'
                              : 'bg-slate-100 text-slate-700'
                          }`}
                        >
                          {sub.grade}
                        </span>
                      </td>
                      <td className="py-1.5 px-2 text-center">{sub.gradePoints}</td>
                      <td className="py-1.5 px-2 text-right font-bold text-slate-900">
                        {sub.qualityPoints}
                      </td>
                    </tr>
                  ))}
                </tbody>
                <tfoot>
                  <tr className="border-t-2 border-slate-200 font-mono text-xs font-bold text-slate-900 bg-slate-50">
                    <td colSpan={2} className="py-2 px-2 text-right font-sans">
                      Cumulative Ledger Totals:
                    </td>
                    <td className="py-2 px-2 text-center">
                      {subjectLedger.reduce((acc, cur) => acc + cur.credits, 0)}
                    </td>
                    <td colSpan={2} />
                    <td className="py-2 px-2 text-right text-indigo-900">
                      {subjectLedger.reduce((acc, cur) => acc + cur.qualityPoints, 0)}
                    </td>
                  </tr>
                </tfoot>
              </table>
            </div>
          </div>
        )}

        {/* Card 4: Institutional Security Mark Forensics (Tier 3) */}
        {securitySeal && (
          <div className="border border-slate-200 rounded-lg p-3.5 bg-white shadow-2xs space-y-3">
            <div className="flex items-center space-x-2 border-b border-slate-100 pb-2">
              <Award className="w-3.5 h-3.5 text-indigo-700" />
              <h4 className="text-xs font-bold text-slate-800 uppercase tracking-wide">
                Institutional Security Marks & Cryptographic Audit
              </h4>
            </div>

            <div className="grid grid-cols-3 gap-2.5 text-xs">
              <div className="p-2 rounded bg-slate-50 border border-slate-100">
                <div className="text-[10px] text-slate-500 font-medium">VTU Crest Integrity</div>
                <div className="font-semibold text-slate-900 mt-0.5 flex items-center space-x-1">
                  {securitySeal.crestResolution === 'PASS' ? (
                    <CheckCircle2 className="w-3.5 h-3.5 text-emerald-600" />
                  ) : (
                    <AlertTriangle className="w-3.5 h-3.5 text-amber-600" />
                  )}
                  <span>{securitySeal.crestResolution}</span>
                </div>
                <div className="text-[9px] text-slate-400 font-mono">
                  Sharpness Index: {securitySeal.crestScore}%
                </div>
              </div>

              <div className="p-2 rounded bg-slate-50 border border-slate-100">
                <div className="text-[10px] text-slate-500 font-medium">Registrar Signature ROI</div>
                <div className="font-semibold text-slate-900 mt-0.5 flex items-center space-x-1">
                  {securitySeal.registrarSignature === 'PASS' ? (
                    <CheckCircle2 className="w-3.5 h-3.5 text-emerald-600" />
                  ) : (
                    <XCircle className="w-3.5 h-3.5 text-rose-600" />
                  )}
                  <span>{securitySeal.registrarSignature}</span>
                </div>
                <div className="text-[9px] text-slate-400 font-mono">
                  Ink Density: {securitySeal.signatureScore}%
                </div>
              </div>

              <div className="p-2 rounded bg-slate-50 border border-slate-100">
                <div className="text-[10px] text-slate-500 font-medium">Security Watermark</div>
                <div className="font-semibold text-slate-900 mt-0.5 flex items-center space-x-1">
                  {securitySeal.watermarkPresent ? (
                    <CheckCircle2 className="w-3.5 h-3.5 text-emerald-600" />
                  ) : (
                    <AlertTriangle className="w-3.5 h-3.5 text-amber-600" />
                  )}
                  <span>{securitySeal.watermarkPresent ? 'DETECTED' : 'UNVERIFIED'}</span>
                </div>
                <div className="text-[9px] text-slate-400 font-mono">VTU Background Pattern</div>
              </div>
            </div>

            <div className="p-2.5 rounded bg-slate-50 border border-slate-200 text-xs">
              <div className="font-bold text-slate-800 text-[11px] mb-0.5">
                Forensic Examiner Dossier Summary:
              </div>
              <p className="text-slate-600 text-[11px] leading-relaxed">
                {securitySeal.verdictReason}
              </p>
            </div>
          </div>
        )}
      </div>
    </div>
  );
};
