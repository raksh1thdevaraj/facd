import React from 'react';
import { ShieldCheck, FileCheck, Layers, Settings } from 'lucide-react';
import { SystemHealthBadge } from './SystemHealthBadge';

export const Header: React.FC = () => {
  return (
    <header className="sticky top-0 z-50 glass-panel border-b border-slate-800 bg-[#0b0f19]/80 backdrop-blur-md">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 h-16 flex items-center justify-between">
        <div className="flex items-center space-x-3">
          <div className="p-2 rounded-xl bg-gradient-to-tr from-emerald-600 to-teal-500 text-white shadow-lg shadow-emerald-500/20">
            <ShieldCheck className="w-5 h-5" />
          </div>
          <div>
            <h1 className="text-base font-bold text-slate-100 flex items-center space-x-2">
              <span>CertCheck AI</span>
              <span className="text-[10px] uppercase tracking-wider font-semibold bg-emerald-500/10 text-emerald-400 border border-emerald-500/20 px-2 py-0.5 rounded">
                v1.0
              </span>
            </h1>
            <p className="text-xs text-slate-400">Academic Certificate Authenticity & Forensics</p>
          </div>
        </div>

        <nav className="hidden md:flex items-center space-x-1">
          <a
            href="#verify"
            className="flex items-center space-x-2 px-3.5 py-2 rounded-lg text-sm font-medium text-slate-200 bg-slate-800/80 border border-slate-700/60"
          >
            <FileCheck className="w-4 h-4 text-emerald-400" />
            <span>Verify Document</span>
          </a>
          <a
            href="#history"
            className="flex items-center space-x-2 px-3.5 py-2 rounded-lg text-sm font-medium text-slate-400 hover:text-slate-200 hover:bg-slate-800/40 transition-colors"
          >
            <Layers className="w-4 h-4" />
            <span>History</span>
          </a>
          <a
            href="#admin"
            className="flex items-center space-x-2 px-3.5 py-2 rounded-lg text-sm font-medium text-slate-400 hover:text-slate-200 hover:bg-slate-800/40 transition-colors"
          >
            <Settings className="w-4 h-4" />
            <span>Administration</span>
          </a>
        </nav>

        <div className="flex items-center space-x-3">
          <SystemHealthBadge />
        </div>
      </div>
    </header>
  );
};
