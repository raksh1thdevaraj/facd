import React, { useEffect, useState } from 'react';
import { adminService } from '../../services/adminService';
import { TemplateItem } from '../../types/admin';
import { TemplatePreviewModal } from '../../components/admin/TemplatePreviewModal';
import { Stamp, Eye, Loader2, Sparkles } from 'lucide-react';

export const TemplatesManager: React.FC = () => {
  const [templates, setTemplates] = useState<TemplateItem[]>([]);
  const [loading, setLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);
  const [selectedTemplate, setSelectedTemplate] = useState<TemplateItem | null>(null);

  const fetchTemplates = async () => {
    try {
      setLoading(true);
      setError(null);
      const res = await adminService.listTemplates();
      setTemplates(res);
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : 'Failed to fetch templates');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchTemplates();
  }, []);

  return (
    <div className="space-y-6">
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h3 className="text-lg font-bold text-slate-100">Master Certificate Templates & Seal ROIs</h3>
          <p className="text-xs text-slate-400">
            Official degree templates used for geometric homography rectification and seal verification
          </p>
        </div>

        <div className="inline-flex items-center space-x-1.5 px-3 py-1.5 rounded-lg bg-slate-800 border border-slate-700 text-xs text-slate-300">
          <Sparkles className="w-3.5 h-3.5 text-amber-400" />
          <span>{templates.length} Registered Templates</span>
        </div>
      </div>

      {loading && templates.length === 0 ? (
        <div className="min-h-[300px] flex flex-col items-center justify-center space-y-3">
          <Loader2 className="w-8 h-8 animate-spin text-emerald-400" />
          <span className="text-xs text-slate-400">Loading master template catalog...</span>
        </div>
      ) : error ? (
        <div className="p-6 rounded-2xl bg-rose-950/20 border border-rose-800/60 text-center text-sm text-rose-300">
          {error}
        </div>
      ) : templates.length === 0 ? (
        <div className="glass-card rounded-2xl p-12 border border-slate-800 text-center space-y-4">
          <Stamp className="w-12 h-12 text-slate-600 mx-auto" />
          <h4 className="text-base font-semibold text-slate-300">No Master Templates Uploaded</h4>
          <p className="text-xs text-slate-400 max-w-sm mx-auto">
            Upload institutional degree templates to activate automated template layout matching.
          </p>
        </div>
      ) : (
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-6">
          {templates.map((tpl) => (
            <div
              key={tpl.template_id}
              className="glass-card rounded-2xl p-5 border border-slate-800 hover:border-slate-700 transition-all flex flex-col justify-between space-y-4 group"
            >
              <div className="space-y-3">
                <div className="flex items-start justify-between gap-2">
                  <div className="p-2.5 rounded-xl bg-blue-500/10 text-blue-400 border border-blue-500/20 shrink-0">
                    <Stamp className="w-5 h-5" />
                  </div>
                  <span className="px-2 py-0.5 rounded text-[10px] font-mono bg-slate-800 border border-slate-700 text-slate-400">
                    ID: {tpl.template_id.slice(0, 8)}...
                  </span>
                </div>

                <div>
                  <h4 className="text-sm font-bold text-slate-100 group-hover:text-emerald-400 transition-colors">
                    {tpl.template_name}
                  </h4>
                  <p className="text-xs text-slate-400 mt-0.5">{tpl.institution_name}</p>
                </div>

                <div className="p-2.5 rounded-xl bg-slate-900/60 border border-slate-800/80 text-xs text-slate-300">
                  <span className="text-[10px] uppercase text-slate-500 block font-semibold">Program</span>
                  <span className="font-medium">{tpl.degree_program || 'All Conferred Degrees'}</span>
                </div>
              </div>

              <div className="pt-2 border-t border-slate-800 flex items-center justify-between">
                <span className="text-[11px] text-slate-500">
                  {new Date(tpl.uploaded_at).toLocaleDateString()}
                </span>

                <button
                  onClick={() => setSelectedTemplate(tpl)}
                  className="inline-flex items-center space-x-1.5 px-3 py-1.5 rounded-lg bg-slate-800 hover:bg-slate-700 text-emerald-400 text-xs font-semibold border border-slate-700 transition-colors"
                >
                  <Eye className="w-3.5 h-3.5" />
                  <span>Inspect Seal ROI</span>
                </button>
              </div>
            </div>
          ))}
        </div>
      )}

      {/* Template Preview / Seal ROI Inspector Modal */}
      <TemplatePreviewModal
        template={selectedTemplate}
        onClose={() => setSelectedTemplate(null)}
      />
    </div>
  );
};
