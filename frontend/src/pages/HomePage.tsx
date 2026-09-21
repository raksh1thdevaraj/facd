import React from 'react';
import { Link } from 'react-router-dom';
import { ShieldCheck, Cpu, Search, Eye, FileCheck, ArrowRight, Sparkles, CheckCircle2, Lock } from 'lucide-react';

export const HomePage: React.FC = () => {
  return (
    <div className="space-y-16 pb-12">
      {/* Hero Section */}
      <section className="relative pt-8 pb-12 text-center space-y-6 max-w-4xl mx-auto">
        <div className="inline-flex items-center space-x-2 px-3.5 py-1.5 rounded-full bg-emerald-950/60 border border-emerald-500/30 text-emerald-300 text-xs font-medium">
          <Sparkles className="w-3.5 h-3.5 text-emerald-400" />
          <span>Next-Generation Academic Document Intelligence</span>
        </div>

        <h1 className="text-4xl sm:text-6xl font-extrabold tracking-tight text-slate-100 leading-tight">
          Detect Fake & Manipulated Certificates with{' '}
          <span className="text-transparent bg-clip-text bg-gradient-to-r from-emerald-400 via-teal-300 to-cyan-400">
            Multi-Modal AI
          </span>
        </h1>

        <p className="text-base sm:text-lg text-slate-400 max-w-2xl mx-auto leading-relaxed">
          Comprehensive forensic verification combining deep neural feature attribution, Error Level Analysis (ELA), dual-engine OCR consistency, and cryptographic registries.
        </p>

        <div className="flex flex-wrap items-center justify-center gap-4 pt-4">
          <Link
            to="/upload"
            className="inline-flex items-center space-x-2 px-6 py-3.5 rounded-xl bg-emerald-600 hover:bg-emerald-500 text-white font-semibold text-sm shadow-xl shadow-emerald-600/25 transition-all hover:scale-105 active:scale-95"
          >
            <ShieldCheck className="w-5 h-5" />
            <span>Verify Document Now</span>
            <ArrowRight className="w-4 h-4 ml-1" />
          </Link>

          <Link
            to="/history"
            className="inline-flex items-center space-x-2 px-5 py-3.5 rounded-xl bg-slate-800/80 hover:bg-slate-800 text-slate-300 text-sm font-medium border border-slate-700 transition-colors"
          >
            <span>View Verification Log</span>
          </Link>
        </div>
      </section>

      {/* Feature Pillar Cards */}
      <section className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6 max-w-7xl mx-auto">
        <div className="glass-card rounded-2xl p-6 border border-slate-800 space-y-3 hover:border-slate-700 transition-colors">
          <div className="p-3 rounded-xl bg-emerald-500/10 text-emerald-400 border border-emerald-500/20 w-fit">
            <Cpu className="w-6 h-6" />
          </div>
          <h3 className="text-lg font-bold text-slate-100">ResNet-50 Visual Deep Learning</h3>
          <p className="text-xs sm:text-sm text-slate-400 leading-relaxed">
            Detects subtle micro-splicing, boundary inconsistencies, and synthetic generation artifacts with pixel-level Grad-CAM visual heatmaps.
          </p>
        </div>

        <div className="glass-card rounded-2xl p-6 border border-slate-800 space-y-3 hover:border-slate-700 transition-colors">
          <div className="p-3 rounded-xl bg-cyan-500/10 text-cyan-400 border border-cyan-500/20 w-fit">
            <Eye className="w-6 h-6" />
          </div>
          <h3 className="text-lg font-bold text-slate-100">Forensics & Error Level Analysis</h3>
          <p className="text-xs sm:text-sm text-slate-400 leading-relaxed">
            Multi-pass JPEG re-compression difference mapping reveals digitally altered names, grades, and copy-move forged university seals.
          </p>
        </div>

        <div className="glass-card rounded-2xl p-6 border border-slate-800 space-y-3 hover:border-slate-700 transition-colors">
          <div className="p-3 rounded-xl bg-teal-500/10 text-teal-400 border border-teal-500/20 w-fit">
            <Search className="w-6 h-6" />
          </div>
          <h3 className="text-lg font-bold text-slate-100">Dual-Engine OCR Cross-Check</h3>
          <p className="text-xs sm:text-sm text-slate-400 leading-relaxed">
            Runs Tesseract and EasyOCR simultaneously with font consistency analysis, spatial baseline alignment, and kerning discrepancy checks.
          </p>
        </div>

        <div className="glass-card rounded-2xl p-6 border border-slate-800 space-y-3 hover:border-slate-700 transition-colors">
          <div className="p-3 rounded-xl bg-purple-500/10 text-purple-400 border border-purple-500/20 w-fit">
            <FileCheck className="w-6 h-6" />
          </div>
          <h3 className="text-lg font-bold text-slate-100">Template Geometric Alignment</h3>
          <p className="text-xs sm:text-sm text-slate-400 leading-relaxed">
            SIFT and ORB homography rectification compares uploaded diplomas against accredited university layout baselines.
          </p>
        </div>

        <div className="glass-card rounded-2xl p-6 border border-slate-800 space-y-3 hover:border-slate-700 transition-colors">
          <div className="p-3 rounded-xl bg-amber-500/10 text-amber-400 border border-amber-500/20 w-fit">
            <Lock className="w-6 h-6" />
          </div>
          <h3 className="text-lg font-bold text-slate-100">Tamper-Evident Signatures</h3>
          <p className="text-xs sm:text-sm text-slate-400 leading-relaxed">
            Each generated report receives an HMAC-SHA256 digital signature and verifiable QR code for instant smartphone validation.
          </p>
        </div>

        <div className="glass-card rounded-2xl p-6 border border-slate-800 space-y-3 hover:border-slate-700 transition-colors">
          <div className="p-3 rounded-xl bg-blue-500/10 text-blue-400 border border-blue-500/20 w-fit">
            <CheckCircle2 className="w-6 h-6" />
          </div>
          <h3 className="text-lg font-bold text-slate-100">Score Fusion & Dossier</h3>
          <p className="text-xs sm:text-sm text-slate-400 leading-relaxed">
            Weighted Dempster-Shafer evidential fusion outputs an overall authenticity verdict (AUTHENTIC, SUSPICIOUS, MANIPULATED) in milliseconds.
          </p>
        </div>
      </section>
    </div>
  );
};
