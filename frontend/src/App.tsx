import React from 'react';
import { ShieldAlert, FileText, Cpu, Lock, ArrowRight } from 'lucide-react';
import { Header } from './components/Header';

export const App: React.FC = () => {
  return (
    <div className="min-h-screen bg-[#0b0f19] text-slate-100 flex flex-col selection:bg-emerald-500/30 selection:text-emerald-200">
      <Header />

      <main className="flex-1 max-w-7xl w-full mx-auto px-4 sm:px-6 lg:px-8 py-10">
        {/* Hero Banner / Foundation Shell */}
        <div className="relative overflow-hidden rounded-3xl glass-panel p-8 md:p-12 border border-slate-800/80 bg-gradient-to-b from-slate-900/90 to-slate-950/90 shadow-2xl">
          <div className="absolute top-0 right-0 -mr-16 -mt-16 w-96 h-96 bg-emerald-500/10 rounded-full blur-3xl pointer-events-none" />
          <div className="absolute bottom-0 left-0 -ml-16 -mb-16 w-96 h-96 bg-blue-500/10 rounded-full blur-3xl pointer-events-none" />

          <div className="relative z-10 max-w-3xl">
            <div className="inline-flex items-center space-x-2 px-3 py-1 rounded-full bg-emerald-500/10 border border-emerald-500/20 text-emerald-400 text-xs font-semibold uppercase tracking-wider mb-6">
              <span className="w-2 h-2 rounded-full bg-emerald-400 animate-pulse" />
              <span>Phase 01 — Project Foundation Active</span>
            </div>

            <h2 className="text-3xl sm:text-4xl md:text-5xl font-extrabold tracking-tight text-white leading-tight">
              AI-Powered Forensic Verification for Academic Certificates
            </h2>

            <p className="mt-4 text-base sm:text-lg text-slate-300 leading-relaxed">
              Multi-stage automated assessment combining OCR extraction, forensic error level analysis (ELA), copy-move tampering detection, text consistency checks, and multi-modal risk score fusion.
            </p>

            <div className="mt-8 flex flex-wrap gap-4">
              <button
                type="button"
                className="inline-flex items-center space-x-2 px-6 py-3 rounded-xl bg-emerald-600 hover:bg-emerald-500 text-white font-semibold shadow-lg shadow-emerald-600/30 transition-all duration-150 transform hover:-translate-y-0.5 cursor-pointer"
              >
                <span>Upload Certificate</span>
                <ArrowRight className="w-4 h-4" />
              </button>
              <a
                href="/docs"
                target="_blank"
                rel="noreferrer"
                className="inline-flex items-center space-x-2 px-6 py-3 rounded-xl bg-slate-800 hover:bg-slate-700 text-slate-200 font-semibold border border-slate-700/60 transition-all duration-150"
              >
                <span>API Swagger Docs</span>
              </a>
            </div>
          </div>
        </div>

        {/* System Architecture Modules Grid */}
        <div className="mt-12">
          <div className="flex items-center justify-between mb-6">
            <h3 className="text-lg font-bold text-slate-200">Integrated Verification Pipeline Modules</h3>
            <span className="text-xs text-slate-400">Deterministic Contracts v1.0</span>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
            <div className="glass-card p-6 rounded-2xl border border-slate-800/80 hover:border-slate-700/80 transition-all">
              <div className="w-10 h-10 rounded-xl bg-blue-500/10 border border-blue-500/20 text-blue-400 flex items-center justify-center mb-4">
                <FileText className="w-5 h-5" />
              </div>
              <h4 className="font-semibold text-slate-100">Document Ingestion & OCR</h4>
              <p className="mt-2 text-xs text-slate-400 leading-relaxed">
                PDF rasterization, deskewing, noise reduction, and high-precision token extraction with bounding box geometry.
              </p>
            </div>

            <div className="glass-card p-6 rounded-2xl border border-slate-800/80 hover:border-slate-700/80 transition-all">
              <div className="w-10 h-10 rounded-xl bg-amber-500/10 border border-amber-500/20 text-amber-400 flex items-center justify-center mb-4">
                <ShieldAlert className="w-5 h-5" />
              </div>
              <h4 className="font-semibold text-slate-100">Image Forensics</h4>
              <p className="mt-2 text-xs text-slate-400 leading-relaxed">
                Error Level Analysis (ELA), copy-move cloning detection, font anomaly scoring, and compression artifact heatmaps.
              </p>
            </div>

            <div className="glass-card p-6 rounded-2xl border border-slate-800/80 hover:border-slate-700/80 transition-all">
              <div className="w-10 h-10 rounded-xl bg-purple-500/10 border border-purple-500/20 text-purple-400 flex items-center justify-center mb-4">
                <Lock className="w-5 h-5" />
              </div>
              <h4 className="font-semibold text-slate-100">Consistency Rules</h4>
              <p className="mt-2 text-xs text-slate-400 leading-relaxed">
                Chronological date logic, grade format validity, cert-number patterns, and institutional registry cross-matching.
              </p>
            </div>

            <div className="glass-card p-6 rounded-2xl border border-slate-800/80 hover:border-slate-700/80 transition-all">
              <div className="w-10 h-10 rounded-xl bg-emerald-500/10 border border-emerald-500/20 text-emerald-400 flex items-center justify-center mb-4">
                <Cpu className="w-5 h-5" />
              </div>
              <h4 className="font-semibold text-slate-100">Score Fusion & Report</h4>
              <p className="mt-2 text-xs text-slate-400 leading-relaxed">
                Calibrated tabular & visual ML inference, explainable contributing factors (SHAP), and downloadable PDF audits.
              </p>
            </div>
          </div>
        </div>
      </main>

      <footer className="border-t border-slate-800/80 bg-[#070a11] py-6 text-center text-xs text-slate-500">
        <p>AI-Based Detection of Fake or Manipulated Academic Certificates • Research & Verification System</p>
      </footer>
    </div>
  );
};

export default App;
