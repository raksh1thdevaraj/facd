import React, { useEffect, useState, useCallback } from 'react';
import { adminService } from '../../services/adminService';
import { Institution, InstitutionCreate } from '../../types/admin';
import { Building2, Plus, Loader2, CheckCircle2, XCircle, X } from 'lucide-react';

export const InstitutionsManager: React.FC = () => {
  const [institutions, setInstitutions] = useState<Institution[]>([]);
  const [total, setTotal] = useState<number>(0);
  const [page, setPage] = useState<number>(1);
  const [loading, setLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);

  // Modal form state
  const [isModalOpen, setIsModalOpen] = useState<boolean>(false);
  const [formName, setFormName] = useState<string>('');
  const [formCode, setFormCode] = useState<string>('');
  const [formEmail, setFormEmail] = useState<string>('');
  const [isSubmitting, setIsSubmitting] = useState<boolean>(false);
  const [formError, setFormError] = useState<string | null>(null);

  const fetchInstitutions = useCallback(async () => {
    try {
      setLoading(true);
      setError(null);
      const res = await adminService.listInstitutions(page, 15);
      setInstitutions(res.items);
      setTotal(res.total);
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : 'Failed to fetch institutions');
    } finally {
      setLoading(false);
    }
  }, [page]);

  useEffect(() => {
    fetchInstitutions();
  }, [fetchInstitutions]);

  const handleToggleStatus = async (inst: Institution) => {
    try {
      const updated = await adminService.toggleInstitutionStatus(inst.id);
      setInstitutions((prev) =>
        prev.map((item) => (item.id === inst.id ? { ...item, is_active: updated.is_active } : item))
      );
    } catch {
      alert('Failed to toggle institution status.');
    }
  };

  const handleCreateSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setFormError(null);
    setIsSubmitting(true);

    try {
      const payload: InstitutionCreate = {
        name: formName,
        code: formCode.toUpperCase(),
        contact_email: formEmail,
      };
      const created = await adminService.registerInstitution(payload);
      setInstitutions((prev) => [created, ...prev]);
      setTotal((prev) => prev + 1);
      setIsModalOpen(false);
      setFormName('');
      setFormCode('');
      setFormEmail('');
    } catch (err: unknown) {
      setFormError(err instanceof Error ? err.message : 'Failed to register institution');
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <div className="space-y-6">
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <div className="flex items-center space-x-2">
            <h3 className="text-lg font-bold text-slate-100">Accredited Universities & Partner Registrars</h3>
            <span className="text-xs text-slate-400 font-mono">({total} registered)</span>
          </div>
          <p className="text-xs text-slate-400">
            Manage partner institutions, view template counts, and configure access permissions
          </p>
        </div>

        <button
          onClick={() => setIsModalOpen(true)}
          className="inline-flex items-center space-x-2 px-4 py-2 rounded-xl bg-emerald-600 hover:bg-emerald-500 text-white text-xs sm:text-sm font-semibold shadow-lg shadow-emerald-600/20 transition-all self-start sm:self-auto"
        >
          <Plus className="w-4 h-4" />
          <span>Onboard University</span>
        </button>
      </div>


      {loading && institutions.length === 0 ? (
        <div className="min-h-[300px] flex flex-col items-center justify-center space-y-3">
          <Loader2 className="w-8 h-8 animate-spin text-emerald-400" />
          <span className="text-xs text-slate-400">Loading university catalog...</span>
        </div>
      ) : error ? (
        <div className="p-6 rounded-2xl bg-rose-950/20 border border-rose-800/60 text-center text-sm text-rose-300">
          {error}
        </div>
      ) : institutions.length === 0 ? (
        <div className="glass-card rounded-2xl p-12 border border-slate-800 text-center space-y-4">
          <Building2 className="w-12 h-12 text-slate-600 mx-auto" />
          <h4 className="text-base font-semibold text-slate-300">No Universities Registered Yet</h4>
          <p className="text-xs text-slate-400 max-w-sm mx-auto">
            Onboard your first university partner to enable template matching and authoritative records cross-check.
          </p>
          <button
            onClick={() => setIsModalOpen(true)}
            className="px-4 py-2 rounded-xl bg-emerald-600 text-white text-xs font-semibold hover:bg-emerald-500 transition-colors"
          >
            Register Institution
          </button>
        </div>
      ) : (
        <div className="glass-card rounded-2xl border border-slate-800 overflow-hidden shadow-xl">
          <div className="overflow-x-auto">
            <table className="w-full text-left text-xs sm:text-sm">
              <thead className="bg-slate-900/80 border-b border-slate-800 text-slate-400 uppercase text-[11px] tracking-wider font-semibold">
                <tr>
                  <th className="py-3.5 px-4">University Name</th>
                  <th className="py-3.5 px-4">Code</th>
                  <th className="py-3.5 px-4">Templates</th>
                  <th className="py-3.5 px-4">Student Records</th>
                  <th className="py-3.5 px-4">Status</th>
                  <th className="py-3.5 px-4 text-right">Action</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-800/60 text-slate-300">
                {institutions.map((inst) => (
                  <tr key={inst.id} className="hover:bg-slate-800/30 transition-colors">
                    <td className="py-4 px-4 font-semibold flex items-center space-x-2.5">
                      <Building2 className="w-4 h-4 text-slate-400 shrink-0" />
                      <span>{inst.name}</span>
                    </td>
                    <td className="py-4 px-4 font-mono text-emerald-400 font-bold">{inst.code}</td>
                    <td className="py-4 px-4 font-mono">{inst.template_count ?? 0}</td>
                    <td className="py-4 px-4 font-mono">{inst.record_count ?? 0}</td>
                    <td className="py-4 px-4">
                      {inst.is_active ? (
                        <span className="inline-flex items-center space-x-1 px-2.5 py-0.5 rounded-full text-xs font-semibold bg-emerald-500/10 text-emerald-400 border border-emerald-500/20">
                          <CheckCircle2 className="w-3.5 h-3.5" />
                          <span>Active</span>
                        </span>
                      ) : (
                        <span className="inline-flex items-center space-x-1 px-2.5 py-0.5 rounded-full text-xs font-semibold bg-rose-500/10 text-rose-400 border border-rose-500/20">
                          <XCircle className="w-3.5 h-3.5" />
                          <span>Inactive</span>
                        </span>
                      )}
                    </td>
                    <td className="py-4 px-4 text-right">
                      <button
                        onClick={() => handleToggleStatus(inst)}
                        className={`text-xs px-3 py-1 rounded-lg border font-medium transition-colors ${
                          inst.is_active
                            ? 'bg-rose-950/40 text-rose-300 border-rose-800/60 hover:bg-rose-900/60'
                            : 'bg-emerald-950/40 text-emerald-300 border-emerald-800/60 hover:bg-emerald-900/60'
                        }`}
                      >
                        {inst.is_active ? 'Deactivate' : 'Activate'}
                      </button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>

          {total > 15 && (
            <div className="p-3 border-t border-slate-800 flex items-center justify-between text-xs text-slate-400 bg-slate-900/40">
              <span>
                Page {page} of {Math.ceil(total / 15)}
              </span>
              <div className="flex items-center space-x-2">
                <button
                  onClick={() => setPage((p) => Math.max(1, p - 1))}
                  disabled={page <= 1}
                  className="px-2.5 py-1 rounded-lg bg-slate-800 hover:bg-slate-700 disabled:opacity-40 transition-colors"
                >
                  Prev
                </button>
                <button
                  onClick={() => setPage((p) => p + 1)}
                  disabled={page >= Math.ceil(total / 15)}
                  className="px-2.5 py-1 rounded-lg bg-slate-800 hover:bg-slate-700 disabled:opacity-40 transition-colors"
                >
                  Next
                </button>
              </div>
            </div>
          )}
        </div>
      )}


      {/* Onboard University Modal */}
      {isModalOpen && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/80 backdrop-blur-sm animate-fadeIn">
          <div className="glass-card rounded-2xl max-w-md w-full border border-slate-700/80 shadow-2xl p-6 space-y-4">
            <div className="flex items-center justify-between border-b border-slate-800 pb-3">
              <h3 className="text-sm font-bold text-slate-100">Onboard Accredited University</h3>
              <button
                onClick={() => setIsModalOpen(false)}
                className="p-1 rounded-lg text-slate-400 hover:text-white transition-colors"
              >
                <X className="w-5 h-5" />
              </button>
            </div>

            {formError && (
              <div className="p-3 rounded-xl bg-rose-950/40 border border-rose-800/60 text-xs text-rose-300">
                {formError}
              </div>
            )}

            <form onSubmit={handleCreateSubmit} className="space-y-4 text-xs sm:text-sm">
              <div>
                <label className="block text-slate-300 font-medium mb-1">University Name</label>
                <input
                  type="text"
                  required
                  placeholder="e.g. Stanford University"
                  value={formName}
                  onChange={(e) => setFormName(e.target.value)}
                  className="w-full px-3.5 py-2 rounded-xl bg-slate-900 border border-slate-800 text-slate-100 focus:outline-none focus:border-emerald-500"
                />
              </div>

              <div>
                <label className="block text-slate-300 font-medium mb-1">Institution Code</label>
                <input
                  type="text"
                  required
                  placeholder="e.g. STANFORD"
                  value={formCode}
                  onChange={(e) => setFormCode(e.target.value)}
                  className="w-full px-3.5 py-2 rounded-xl bg-slate-900 border border-slate-800 text-slate-100 uppercase focus:outline-none focus:border-emerald-500 font-mono"
                />
              </div>

              <div>
                <label className="block text-slate-300 font-medium mb-1">Registrar Contact Email</label>
                <input
                  type="email"
                  required
                  placeholder="e.g. registrar@stanford.edu"
                  value={formEmail}
                  onChange={(e) => setFormEmail(e.target.value)}
                  className="w-full px-3.5 py-2 rounded-xl bg-slate-900 border border-slate-800 text-slate-100 focus:outline-none focus:border-emerald-500"
                />
              </div>

              <div className="pt-2 flex items-center justify-end space-x-2">
                <button
                  type="button"
                  onClick={() => setIsModalOpen(false)}
                  className="px-4 py-2 rounded-xl bg-slate-800 hover:bg-slate-700 text-slate-300 text-xs font-medium transition-colors"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  disabled={isSubmitting}
                  className="px-5 py-2 rounded-xl bg-emerald-600 hover:bg-emerald-500 text-white text-xs font-semibold shadow-lg shadow-emerald-600/25 transition-all disabled:opacity-50"
                >
                  {isSubmitting ? 'Registering...' : 'Register Institution'}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
};
