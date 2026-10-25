import React from 'react';
import {
  Calculator,
  Award,
  X,
  Building2,
} from 'lucide-react';

interface SchemeMatrixModalProps {
  isOpen: boolean;
  onClose: () => void;
  selectedScheme?: string;
}

export const SchemeMatrixModal: React.FC<SchemeMatrixModalProps> = ({
  isOpen,
  onClose,
  selectedScheme: _selectedScheme,
}) => {
  if (!isOpen) return null;

  const gradingTiers = [
    { grade: 'O', label: 'Outstanding', marks: '90 - 100', points: 10, bg: 'bg-emerald-50 text-emerald-900 border-emerald-200' },
    { grade: 'A+', label: 'Excellent', marks: '80 - 89', points: 9, bg: 'bg-emerald-50 text-emerald-800 border-emerald-200' },
    { grade: 'A', label: 'Very Good', marks: '70 - 79', points: 8, bg: 'bg-blue-50 text-blue-800 border-blue-200' },
    { grade: 'B+', label: 'Good', marks: '60 - 69', points: 7, bg: 'bg-indigo-50 text-indigo-800 border-indigo-200' },
    { grade: 'B', label: 'Above Average', marks: '55 - 59', points: 6, bg: 'bg-slate-50 text-slate-800 border-slate-200' },
    { grade: 'C', label: 'Average', marks: '50 - 54', points: 5, bg: 'bg-amber-50 text-amber-800 border-amber-200' },
    { grade: 'P', label: 'Pass', marks: '40 - 49', points: 4, bg: 'bg-amber-100 text-amber-900 border-amber-300' },
    { grade: 'F', label: 'Fail', marks: '0 - 39', points: 0, bg: 'bg-rose-50 text-rose-800 border-rose-200' },
  ];

  const regionalCodes = [
    { code: '1', region: 'Bengaluru Region (e.g., 1MS, 1RV, 1BY, 1DS)' },
    { code: '2', region: 'Belagavi Region (e.g., 2GI, 2BV, 2KA)' },
    { code: '3', region: 'Kalaburagi Region (e.g., 3PD, 3BK, 3GN)' },
    { code: '4', region: 'Mysuru Region (e.g., 4MC, 4NI, 4VV)' },
  ];

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-slate-900/40 backdrop-blur-xs">
      <div className="bg-white border border-slate-200 rounded-xl max-w-2xl w-full shadow-2xl overflow-hidden flex flex-col max-h-[90vh]">
        {/* Header */}
        <div className="px-5 py-4 border-b border-slate-200 bg-slate-50 flex items-center justify-between">
          <div className="flex items-center space-x-2">
            <Building2 className="w-5 h-5 text-indigo-800" />
            <div>
              <h3 className="font-bold text-sm text-slate-900">
                VTU CBCS Grading & Schema Reference
              </h3>
              <p className="text-[11px] text-slate-500">
                Authoritative parameters for algorithmic cross-examination
              </p>
            </div>
          </div>
          <button
            onClick={onClose}
            className="p-1 rounded-lg text-slate-400 hover:text-slate-600 hover:bg-slate-200 transition-colors"
          >
            <X className="w-4 h-4" />
          </button>
        </div>

        {/* Modal Body */}
        <div className="p-5 overflow-y-auto space-y-5 text-xs">
          {/* Institutional Mathematical Formulas */}
          <div className="p-3.5 rounded-lg bg-indigo-50/60 border border-indigo-100 space-y-2">
            <div className="font-bold text-indigo-950 text-xs flex items-center space-x-1.5">
              <Calculator className="w-4 h-4 text-indigo-700" />
              <span>Programmatic Verification Formulas (Deterministic Cross-Check)</span>
            </div>
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-3 pt-1">
              <div className="p-2.5 rounded bg-white border border-indigo-200 font-mono">
                <div className="text-[10px] text-slate-500 uppercase font-sans font-semibold">
                  Semester Grade Point Average (SGPA)
                </div>
                <div className="text-xs font-bold text-indigo-900 mt-1">
                  SGPA = Σ(Ci × Gi) / ΣCi
                </div>
                <div className="text-[10px] text-slate-500 mt-0.5 font-sans">
                  Sum of Quality Points divided by Total Earned Credits.
                </div>
              </div>

              <div className="p-2.5 rounded bg-white border border-indigo-200 font-mono">
                <div className="text-[10px] text-slate-500 uppercase font-sans font-semibold">
                  Cumulative Grade Point Average (CGPA)
                </div>
                <div className="text-xs font-bold text-indigo-900 mt-1">
                  CGPA = Σ(Sj × Cj) / ΣCj
                </div>
                <div className="text-[10px] text-slate-500 mt-0.5 font-sans">
                  Weighted average of SGPAs across all enrolled semesters.
                </div>
              </div>
            </div>
          </div>

          {/* Grading Tiers Table */}
          <div>
            <div className="font-bold text-slate-900 mb-2 flex items-center space-x-1.5">
              <Award className="w-4 h-4 text-indigo-700" />
              <span>Institutional Letter Grades & Grade Points Scale</span>
            </div>
            <div className="border border-slate-200 rounded-lg overflow-hidden">
              <table className="w-full text-left border-collapse">
                <thead>
                  <tr className="bg-slate-50 border-b border-slate-200 text-[10px] font-semibold text-slate-600 uppercase">
                    <th className="py-2 px-3">Grade</th>
                    <th className="py-2 px-3">Evaluation Tier</th>
                    <th className="py-2 px-3">Percentage Range</th>
                    <th className="py-2 px-3 text-right">Grade Points (Gi)</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-100 font-mono text-xs">
                  {gradingTiers.map((tier) => (
                    <tr key={tier.grade} className="hover:bg-slate-50">
                      <td className="py-2 px-3 font-bold text-indigo-950">
                        <span className={`px-2 py-0.5 rounded border ${tier.bg}`}>
                          {tier.grade}
                        </span>
                      </td>
                      <td className="py-2 px-3 font-sans text-slate-700">{tier.label}</td>
                      <td className="py-2 px-3 text-slate-600">{tier.marks}</td>
                      <td className="py-2 px-3 text-right font-bold text-slate-900">
                        {tier.points}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>

          {/* USN Anatomy & Regional Centers */}
          <div className="p-3.5 rounded-lg bg-slate-50 border border-slate-200 space-y-2">
            <div className="font-bold text-slate-900 text-xs">
              University Seat Number (USN) 10-Character Syntax Schema:
            </div>
            <div className="font-mono text-xs p-2 rounded bg-white border border-slate-200 text-indigo-950 font-bold">
              [Region: 1][College: MS][Year: 21][Branch: CS][Roll: 045] &rarr; 1MS21CS045
            </div>
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-1.5 text-[11px] text-slate-600 pt-1">
              {regionalCodes.map((rc) => (
                <div key={rc.code} className="flex items-center space-x-1.5">
                  <span className="font-mono font-bold text-slate-900 bg-white px-1.5 py-0.5 rounded border border-slate-200 text-[10px]">
                    Region {rc.code}
                  </span>
                  <span>{rc.region}</span>
                </div>
              ))}
            </div>
          </div>
        </div>

        {/* Footer */}
        <div className="px-5 py-3 border-t border-slate-200 bg-slate-50 flex items-center justify-end">
          <button
            onClick={onClose}
            className="px-4 py-2 bg-indigo-900 hover:bg-indigo-800 text-white text-xs font-semibold rounded-lg shadow-sm transition-all"
          >
            Close Schema Matrix
          </button>
        </div>
      </div>
    </div>
  );
};
