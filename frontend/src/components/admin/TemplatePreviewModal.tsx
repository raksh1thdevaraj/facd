import React from 'react';
import { X, Stamp, ShieldCheck } from 'lucide-react';
import { TemplateItem } from '../../types/admin';

interface TemplatePreviewModalProps {
  template: TemplateItem | null;
  onClose: () => void;
}

export const TemplatePreviewModal: React.FC<TemplatePreviewModalProps> = ({ template, onClose }) => {
  if (!template) return null;

  // Default seal ROI coordinate box if not explicitly set
  const sealRoi = template.seal_roi || { x: 75, y: 70, width: 18, height: 22 };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/80 backdrop-blur-sm animate-fadeIn">
      <div className="glass-card rounded-2xl max-w-2xl w-full border border-slate-700/80 shadow-2xl overflow-hidden flex flex-col max-h-[90vh]">
        {/* Modal Header */}
        <div className="flex items-center justify-between p-4 border-b border-slate-800 bg-slate-900/60">
          <div className="flex items-center space-x-2.5">
            <div className="p-2 rounded-xl bg-blue-500/10 text-blue-400 border border-blue-500/20">
              <Stamp className="w-4 h-4" />
            </div>
            <div>
              <h3 className="text-sm font-bold text-slate-100">{template.template_name}</h3>
              <p className="text-xs text-slate-400">{template.institution_name}</p>
            </div>
          </div>
          <button
            onClick={onClose}
            className="p-1.5 rounded-lg text-slate-400 hover:text-white hover:bg-slate-800 transition-colors"
          >
            <X className="w-5 h-5" />
          </button>
        </div>

        {/* Modal Body / Canvas preview with Seal ROI Overlay */}
        <div className="p-6 overflow-y-auto space-y-4">
          <div className="relative w-full h-80 bg-slate-950 rounded-xl border border-slate-800 flex items-center justify-center overflow-hidden">
            {/* Synthetic master template certificate canvas */}
            <div className="relative w-full h-full p-6 flex flex-col justify-between select-none bg-[#fbfbf9] text-slate-900 border-8 border-[#0f4c81]">
              <div className="text-center space-y-1">
                <h4 className="font-serif font-bold text-base tracking-wider uppercase">
                  {template.institution_name}
                </h4>
                <p className="font-serif italic text-xs">Official Conferred Diploma Template</p>
              </div>

              <div className="text-center space-y-1">
                <p className="text-[10px] uppercase tracking-widest text-slate-500">Degree Conferred</p>
                <p className="font-serif font-bold text-sm text-slate-800">
                  {template.degree_program || 'Bachelor of Science / Arts'}
                </p>
              </div>

              <div className="flex justify-between items-end text-[10px] text-slate-500">
                <span>Registrar Signature Area</span>
                <span>Dean Signature Area</span>
              </div>

              {/* Seal ROI Bounding Box Overlay */}
              <div
                className="absolute border-2 border-blue-500 bg-blue-500/20 rounded flex items-center justify-center pointer-events-none"
                style={{
                  left: `${sealRoi.x}%`,
                  top: `${sealRoi.y}%`,
                  width: `${sealRoi.width}%`,
                  height: `${sealRoi.height}%`,
                }}
              >
                <span className="text-[9px] font-mono font-bold text-blue-600 bg-white/90 px-1 py-0.5 rounded shadow">
                  SEAL ROI
                </span>
              </div>
            </div>
          </div>

          {/* Details Row */}
          <div className="grid grid-cols-2 gap-4 text-xs">
            <div className="p-3 rounded-xl bg-slate-900/60 border border-slate-800 space-y-1">
              <span className="text-slate-500 font-semibold block text-[10px] uppercase">Template ID</span>
              <code className="text-slate-300 font-mono text-[11px] break-all">{template.template_id}</code>
            </div>
            <div className="p-3 rounded-xl bg-slate-900/60 border border-slate-800 space-y-1">
              <span className="text-slate-500 font-semibold block text-[10px] uppercase">Registered Date</span>
              <span className="text-slate-300">{new Date(template.uploaded_at).toLocaleDateString()}</span>
            </div>
          </div>

          <div className="flex items-center space-x-2 text-xs text-slate-400 p-3 rounded-xl bg-emerald-950/20 border border-emerald-800/40">
            <ShieldCheck className="w-4 h-4 text-emerald-400 shrink-0" />
            <span>Master homography reference and seal ROI active for automated SIFT/ORB matching.</span>
          </div>
        </div>

        {/* Modal Footer */}
        <div className="p-3 border-t border-slate-800 bg-slate-900/40 text-right">
          <button
            onClick={onClose}
            className="px-4 py-2 rounded-xl bg-slate-800 hover:bg-slate-700 text-slate-200 text-xs font-semibold transition-colors"
          >
            Close Inspector
          </button>
        </div>
      </div>
    </div>
  );
};
