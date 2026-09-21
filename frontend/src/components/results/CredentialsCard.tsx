import React from 'react';
import { GraduationCap, AlertCircle, CheckCircle, Award, Calendar, Hash, Building2, User } from 'lucide-react';
import { AcademicCredentials } from '../../types/report';

interface CredentialsCardProps {
  credentials: AcademicCredentials;
}

export const CredentialsCard: React.FC<CredentialsCardProps> = ({ credentials }) => {
  const fields = [
    {
      label: 'Student Name',
      value: credentials.student_name,
      confidence:
        credentials.student_name_confidence ??
        credentials.ocr_confidence_scores?.student_name,
      icon: User,
    },
    {
      label: 'Institution Name',
      value: credentials.institution_name,
      confidence:
        credentials.institution_name_confidence ??
        credentials.ocr_confidence_scores?.institution_name,
      icon: Building2,
    },
    {
      label: 'Degree Title / Major',
      value: credentials.course_degree || credentials.degree_title,
      confidence:
        credentials.course_degree_confidence ??
        credentials.degree_title_confidence ??
        credentials.ocr_confidence_scores?.degree_title,
      icon: GraduationCap,
    },
    {
      label: 'Graduation / Issue Date',
      value: credentials.issue_date || credentials.graduation_date,
      confidence:
        credentials.issue_date_confidence ??
        credentials.graduation_date_confidence ??
        credentials.ocr_confidence_scores?.graduation_date,
      icon: Calendar,
    },
    {
      label: 'Certificate / Serial ID',
      value: credentials.certificate_number || credentials.register_number,
      confidence:
        credentials.certificate_number_confidence ??
        credentials.register_number_confidence ??
        credentials.ocr_confidence_scores?.certificate_number,
      icon: Hash,
    },
    {
      label: 'GPA / Honors Classification',
      value: credentials.grade_or_marks || credentials.gpa_or_grade,
      confidence:
        credentials.grade_or_marks_confidence ??
        credentials.gpa_or_grade_confidence ??
        credentials.ocr_confidence_scores?.gpa_or_grade,
      icon: Award,
    },
  ];


  const avgConfidence = credentials.overall_ocr_confidence ?? 0.88;

  return (
    <div className="glass-card rounded-2xl p-6 border border-slate-800 shadow-xl space-y-6">
      <div className="flex items-center justify-between border-b border-slate-800 pb-4">
        <div className="flex items-center space-x-3">
          <div className="p-2 rounded-xl bg-slate-800 text-emerald-400 border border-slate-700">
            <GraduationCap className="w-5 h-5" />
          </div>
          <div>
            <h3 className="text-base font-bold text-slate-100">Extracted Academic Credentials</h3>
            <p className="text-xs text-slate-400">Structured data recovered by dual OCR engines</p>
          </div>
        </div>

        <div className="flex items-center space-x-1.5 text-xs bg-slate-800/80 px-3 py-1.5 rounded-lg border border-slate-700">
          <span className="text-slate-400">Avg OCR Confidence:</span>
          <span className={`font-mono font-bold ${avgConfidence >= 0.75 ? 'text-emerald-400' : 'text-amber-400'}`}>
            {(avgConfidence * 100).toFixed(0)}%
          </span>
        </div>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        {fields.map((field) => {
          const Icon = field.icon;
          const conf = field.confidence !== undefined ? field.confidence : null;
          const isLowConfidence = conf !== null && conf < 0.70;

          return (
            <div
              key={field.label}
              className={`p-3.5 rounded-xl border transition-all ${
                isLowConfidence
                  ? 'bg-amber-950/20 border-amber-800/50'
                  : 'bg-slate-900/40 border-slate-800/80'
              }`}
            >
              <div className="flex items-center justify-between">
                <span className="text-xs font-medium text-slate-400 flex items-center space-x-1.5">
                  <Icon className="w-3.5 h-3.5 text-slate-500" />
                  <span>{field.label}</span>
                </span>
                {conf !== null && (
                  <span
                    className={`inline-flex items-center space-x-1 text-[11px] px-2 py-0.5 rounded font-mono ${
                      isLowConfidence
                        ? 'bg-amber-500/20 text-amber-300 border border-amber-500/30'
                        : 'bg-emerald-500/10 text-emerald-400 border border-emerald-500/20'
                    }`}
                  >
                    {isLowConfidence ? (
                      <AlertCircle className="w-3 h-3 text-amber-400 mr-0.5" />
                    ) : (
                      <CheckCircle className="w-3 h-3 text-emerald-400 mr-0.5" />
                    )}
                    <span>{(conf * 100).toFixed(0)}% OCR</span>
                  </span>
                )}
              </div>

              <div className="mt-2">
                <span
                  className={`text-sm font-semibold block break-words ${
                    field.value ? 'text-slate-200' : 'text-slate-500 italic'
                  }`}
                >
                  {field.value || 'Not detected'}
                </span>
              </div>
            </div>
          );
        })}
      </div>

      {credentials.qr_code_data && (
        <div className="p-3 rounded-xl bg-slate-900/60 border border-slate-800 text-xs">
          <span className="font-semibold text-slate-300 block mb-1">Embedded QR / Barcode Payload:</span>
          <code className="text-emerald-400 break-all font-mono">{credentials.qr_code_data}</code>
        </div>
      )}
    </div>
  );
};
