import React from 'react';
import { Link, useLocation } from 'react-router-dom';
import { ShieldCheck, UploadCloud, History, LogIn, LogOut, User as UserIcon } from 'lucide-react';
import { SystemHealthBadge } from '../SystemHealthBadge';
import { useAuth } from '../../context/AuthContext';

export const Navbar: React.FC = () => {
  const location = useLocation();
  const { user, isAuthenticated, logout } = useAuth();

  const isActive = (path: string) => location.pathname === path;

  return (
    <header className="sticky top-0 z-50 glass-panel border-b border-slate-800 bg-[#0b0f19]/90 backdrop-blur-md">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 h-16 flex items-center justify-between">
        <Link to="/" className="flex items-center space-x-3 group">
          <div className="p-2 rounded-xl bg-gradient-to-tr from-emerald-600 to-teal-500 text-white shadow-lg shadow-emerald-500/20 group-hover:scale-105 transition-transform">
            <ShieldCheck className="w-5 h-5" />
          </div>
          <div>
            <h1 className="text-base font-bold text-slate-100 flex items-center space-x-2">
              <span>CertCheck AI</span>
              <span className="text-[10px] uppercase tracking-wider font-semibold bg-emerald-500/10 text-emerald-400 border border-emerald-500/20 px-2 py-0.5 rounded">
                v1.0
              </span>
            </h1>
            <p className="text-xs text-slate-400 hidden sm:block">Certificate Forensics & Deep Verification</p>
          </div>
        </Link>

        <nav className="flex items-center space-x-2 sm:space-x-3">
          <Link
            to="/upload"
            className={`flex items-center space-x-2 px-3 py-1.5 rounded-lg text-xs sm:text-sm font-medium transition-colors ${
              isActive('/upload')
                ? 'text-slate-100 bg-slate-800 border border-slate-700'
                : 'text-slate-400 hover:text-slate-200 hover:bg-slate-800/50'
            }`}
          >
            <UploadCloud className="w-4 h-4 text-emerald-400" />
            <span>Verify Document</span>
          </Link>

          <Link
            to="/history"
            className={`flex items-center space-x-2 px-3 py-1.5 rounded-lg text-xs sm:text-sm font-medium transition-colors ${
              isActive('/history')
                ? 'text-slate-100 bg-slate-800 border border-slate-700'
                : 'text-slate-400 hover:text-slate-200 hover:bg-slate-800/50'
            }`}
          >
            <History className="w-4 h-4" />
            <span className="hidden sm:inline">Verification History</span>
          </Link>

          <Link
            to="/admin"
            className={`flex items-center space-x-2 px-3 py-1.5 rounded-lg text-xs sm:text-sm font-medium transition-colors ${
              isActive('/admin')
                ? 'text-slate-100 bg-slate-800 border border-slate-700'
                : 'text-slate-400 hover:text-slate-200 hover:bg-slate-800/50'
            }`}
          >
            <span>Admin Console</span>
          </Link>

          <div className="hidden lg:block ml-2 border-l border-slate-800 pl-3">
            <SystemHealthBadge />
          </div>


          <div className="ml-2 border-l border-slate-800 pl-3 flex items-center space-x-2">
            {isAuthenticated && user ? (
              <div className="flex items-center space-x-2">
                <span className="text-xs text-slate-300 hidden md:flex items-center space-x-1.5 bg-slate-800/60 px-2.5 py-1 rounded-md border border-slate-700">
                  <UserIcon className="w-3.5 h-3.5 text-emerald-400" />
                  <span>{user.username || user.full_name || user.email}</span>
                </span>
                <button
                  onClick={() => logout()}
                  title="Sign out"
                  className="flex items-center space-x-1 px-2.5 py-1.5 text-xs text-slate-400 hover:text-rose-400 hover:bg-slate-800/50 rounded-lg transition-colors"
                >
                  <LogOut className="w-4 h-4" />
                  <span className="hidden sm:inline">Sign Out</span>
                </button>
              </div>
            ) : (
              <Link
                to="/login"
                className={`flex items-center space-x-1.5 px-3 py-1.5 rounded-lg text-xs sm:text-sm font-medium text-slate-300 hover:text-white bg-slate-800/60 hover:bg-slate-800 border border-slate-700 transition-colors ${
                  isActive('/login') ? 'ring-2 ring-emerald-500/50' : ''
                }`}
              >
                <LogIn className="w-4 h-4 text-emerald-400" />
                <span>Sign In</span>
              </Link>
            )}
          </div>
        </nav>
      </div>
    </header>
  );
};
