import React from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { ShieldCheck, LogOut, ExternalLink, User as UserIcon, History } from 'lucide-react';
import { SystemHealthBadge } from '../SystemHealthBadge';
import { useAuth } from '../../context/AuthContext';

export const Navbar: React.FC = () => {
  const navigate = useNavigate();
  const { user, isAuthenticated, isAdmin, logout, openAuthModal } = useAuth();

  const handleOpenWorkspace = () => {
    if (isAdmin) {
      navigate('/admin');
    } else {
      navigate('/verify');
    }
  };

  return (
    <header className="sticky top-0 z-50 border-b border-slate-800/80 bg-[#0b0f19]/90 backdrop-blur-xl">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 h-18 flex items-center justify-between">
        {/* 1. Brand / "About Us" Link */}
        <Link
          to="/"
          className="flex items-center space-x-3 group"
          title="CertiShield AI • About Us & Multi-Modal Architecture"
        >
          <div className="p-2.5 rounded-2xl bg-gradient-to-tr from-emerald-600 via-teal-500 to-cyan-500 text-white shadow-lg shadow-emerald-500/25 group-hover:scale-105 transition-all">
            <ShieldCheck className="w-5 h-5" />
          </div>
          <div>
            <div className="flex items-center space-x-2">
              <span className="font-extrabold text-base tracking-tight text-white font-display">
                CertiShield AI
              </span>
            </div>
            <p className="text-[11px] text-slate-400">
              About Us &bull; Forensic Architecture
            </p>
          </div>
        </Link>

        {/* 2. Server Status Indicator (Live Health Monitor) */}
        <div className="flex items-center justify-center">
          <SystemHealthBadge />
        </div>

        {/* 3. Account Action (Login / Register or User Avatar & Assigned Workspace) */}
        <div className="flex items-center">
          {isAuthenticated && user ? (
            <div className="flex items-center space-x-2.5 sm:space-x-3">
              {/* User Avatar & Role Badge */}
              <div className="flex items-center space-x-2 bg-slate-900/90 border border-slate-700/80 px-2.5 py-1.5 rounded-xl text-xs text-slate-200 shadow-sm">
                <div className="w-6 h-6 rounded-lg bg-slate-800 border border-slate-600 flex items-center justify-center text-slate-200 font-bold text-xs shrink-0">
                  {user.full_name ? user.full_name.charAt(0).toUpperCase() : <UserIcon className="w-3.5 h-3.5" />}
                </div>
                <span className="max-w-[110px] truncate font-medium hidden sm:inline">
                  {user.full_name || user.email}
                </span>
                <span
                  className={`text-[9px] font-mono uppercase px-2 py-0.5 rounded-md border font-bold ${
                    isAdmin
                      ? 'bg-rose-950/80 text-rose-300 border-rose-500/40'
                      : 'bg-emerald-950/80 text-emerald-300 border-emerald-500/40'
                  }`}
                >
                  {isAdmin ? 'Admin' : 'User'}
                </span>
              </div>

              {/* History Navigation Link */}
              <Link
                to="/history"
                className="inline-flex items-center space-x-1.5 px-3 py-1.5 rounded-xl text-xs font-semibold border transition-all cursor-pointer bg-slate-900/90 hover:bg-slate-800 text-slate-300 border-slate-700/80 hover:border-slate-600"
                title="View Verification History"
              >
                <History className="w-3.5 h-3.5 text-emerald-400" />
                <span className="hidden sm:inline">History</span>
              </Link>

              {/* Action to Open Assigned Workspace (/verify for User, /admin for Admin) */}
              <button
                onClick={handleOpenWorkspace}
                className={`inline-flex items-center space-x-1 px-3 py-1.5 rounded-xl text-xs font-semibold border transition-all cursor-pointer ${
                  isAdmin
                    ? 'bg-rose-950/40 hover:bg-rose-900/60 text-rose-300 border-rose-700/60 hover:border-rose-500'
                    : 'bg-emerald-950/40 hover:bg-emerald-900/60 text-emerald-300 border-emerald-700/60 hover:border-emerald-500'
                }`}
                title={isAdmin ? 'Open Admin Console' : 'Open Verification Workspace'}
              >
                <span>{isAdmin ? 'Admin Console' : 'Workspace'}</span>
                <ExternalLink className="w-3 h-3 ml-0.5" />
              </button>

              {/* Logout Button */}
              <button
                onClick={() => logout()}
                title="Sign out"
                className="p-2 rounded-xl text-slate-400 hover:text-rose-400 hover:bg-slate-800/80 transition-colors border border-slate-800 hover:border-slate-700 cursor-pointer"
              >
                <LogOut className="w-4 h-4" />
              </button>
            </div>
          ) : (
            <button
              onClick={() => openAuthModal()}
              className="inline-flex items-center space-x-2 px-4 py-2 rounded-xl bg-gradient-to-r from-emerald-600 to-teal-600 hover:from-emerald-500 hover:to-teal-500 text-white text-xs font-bold shadow-lg shadow-emerald-600/25 transition-all hover:scale-105 active:scale-95 cursor-pointer"
            >
              <span>Login / Register</span>
            </button>
          )}
        </div>
      </div>
    </header>
  );
};

