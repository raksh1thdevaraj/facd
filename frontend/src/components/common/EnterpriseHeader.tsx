import React from 'react';
import {
  Download,
  Building2,
  UserCheck,
  Layers,
  LogOut,
  User as UserIcon,
} from 'lucide-react';
import { SystemHealthBadge } from '../SystemHealthBadge';
import { useAuth } from '../../context/AuthContext';

export interface EnterpriseHeaderProps {
  currentScheme: string;
  onSchemeChange: (scheme: string) => void;
  onExportDossier?: () => void;
  hasActiveReport?: boolean;
}

export const VTU_SCHEMES = [
  { id: 'VTU_2021_CBCS', name: 'VTU 2021 CBCS Scheme (160 Credits)', badge: 'Active Standard' },
  { id: 'VTU_2018_CBCS', name: 'VTU 2018 CBCS Scheme (175 Credits)', badge: 'Legacy CBCS' },
  { id: 'VTU_2022_NEP', name: 'VTU 2022 NEP Scheme (160 Credits)', badge: 'NEP Curriculum' },
  { id: 'AUTONOMOUS_ENGG', name: 'Autonomous Affiliated Engineering', badge: 'Tier-1 Affiliated' },
];

export const EnterpriseHeader: React.FC<EnterpriseHeaderProps> = ({
  currentScheme,
  onSchemeChange,
  onExportDossier,
  hasActiveReport = false,
}) => {
  const { user, isAuthenticated, isAdmin, logout, openAuthModal } = useAuth();

  return (
    <header className="sticky top-0 z-40 bg-white border-b border-slate-200 shadow-sm">
      <div className="max-w-[1720px] mx-auto px-4 sm:px-6 h-16 flex items-center justify-between gap-4">
        {/* Brand & Institutional Identity */}
        <div className="flex items-center space-x-3 shrink-0">
          <div className="w-9 h-9 rounded-lg bg-indigo-900 flex items-center justify-center text-white shadow-sm ring-1 ring-slate-900/10">
            <Building2 className="w-5 h-5 text-indigo-200" />
          </div>
          <div>
            <div className="flex items-center space-x-2">
              <span className="font-extrabold text-base tracking-tight text-slate-900 font-display">
                VERIDOC <span className="text-indigo-800 font-semibold text-xs ml-1 px-1.5 py-0.5 bg-indigo-50 border border-indigo-200 rounded">VTU MARKS CARD FORENSICS</span>
              </span>
            </div>
            <p className="text-[11px] text-slate-500 font-medium">
              Academic Marks Card Tampering & Cryptographic Semantic Verification
            </p>
          </div>
        </div>

        {/* Institutional Scheme Selector & Diagnostics */}
        <div className="hidden lg:flex items-center space-x-3">
          <div className="flex items-center space-x-2 px-3 py-1.5 rounded-lg bg-slate-50 border border-slate-200 text-xs">
            <Layers className="w-3.5 h-3.5 text-indigo-700" />
            <span className="text-slate-500 font-medium">Curriculum Scheme:</span>
            <select
              value={currentScheme}
              onChange={(e) => onSchemeChange(e.target.value)}
              className="bg-transparent text-slate-900 font-semibold text-xs border-none focus:outline-none cursor-pointer pr-1"
            >
              {VTU_SCHEMES.map((scheme) => (
                <option key={scheme.id} value={scheme.id} className="text-slate-900 bg-white">
                  {scheme.name}
                </option>
              ))}
            </select>
          </div>

          <SystemHealthBadge />
        </div>

        {/* Quick Actions & Profile Session */}
        <div className="flex items-center space-x-3 shrink-0">
          {onExportDossier && (
            <button
              onClick={onExportDossier}
              disabled={!hasActiveReport}
              className={`inline-flex items-center space-x-1.5 px-3 py-1.5 rounded-lg text-xs font-semibold shadow-sm transition-all ${
                hasActiveReport
                  ? 'bg-indigo-900 hover:bg-indigo-800 text-white cursor-pointer active:scale-95'
                  : 'bg-slate-100 text-slate-400 border border-slate-200 cursor-not-allowed'
              }`}
              title={hasActiveReport ? 'Download Institutional Audit Dossier PDF' : 'Inspect a document first to generate audit dossier'}
            >
              <Download className="w-3.5 h-3.5" />
              <span>Export Dossier (PDF)</span>
            </button>
          )}

          {/* User Profile / Auth Action */}
          {isAuthenticated && user ? (
            <div className="flex items-center space-x-2 pl-2 border-l border-slate-200">
              <div className="flex items-center space-x-2 px-2.5 py-1 rounded-lg bg-slate-100 border border-slate-200 text-xs">
                <div className="w-6 h-6 rounded-md bg-indigo-900 text-white font-bold text-xs flex items-center justify-center">
                  {user.full_name ? user.full_name.charAt(0).toUpperCase() : <UserIcon className="w-3.5 h-3.5" />}
                </div>
                <div className="hidden sm:block text-left">
                  <div className="font-semibold text-slate-900 text-[11px] leading-tight max-w-[110px] truncate">
                    {user.full_name || user.email}
                  </div>
                  <div className="text-[10px] text-slate-500 font-mono">
                    {isAdmin ? 'Senior Examiner' : 'Forensic Officer'}
                  </div>
                </div>
              </div>

              <button
                onClick={() => logout()}
                title="Sign out"
                className="p-1.5 rounded-lg text-slate-400 hover:text-rose-600 hover:bg-rose-50 border border-transparent hover:border-rose-200 transition-colors"
              >
                <LogOut className="w-4 h-4" />
              </button>
            </div>
          ) : (
            <button
              onClick={() => openAuthModal()}
              className="inline-flex items-center space-x-1.5 px-3 py-1.5 rounded-lg bg-slate-900 hover:bg-slate-800 text-white text-xs font-semibold transition-all shadow-sm"
            >
              <UserCheck className="w-3.5 h-3.5" />
              <span>Officer Sign In</span>
            </button>
          )}
        </div>
      </div>
    </header>
  );
};
