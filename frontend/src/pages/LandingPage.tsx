import React from 'react';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import { Hero3DCanvas } from '../components/landing/Hero3DCanvas';
import { ProblemSolutionMatrix } from '../components/landing/ProblemSolutionMatrix';
import { PipelineVisualization } from '../components/landing/PipelineVisualization';
import { InteractiveDemoSandbox } from '../components/landing/InteractiveDemoSandbox';
import { ResearchMatrix } from '../components/landing/ResearchMatrix';
import {
  ShieldCheck,
  ArrowRight,
  Layers,
  Scan,
} from 'lucide-react';

export const LandingPage: React.FC = () => {
  const { isAuthenticated, openAuthModal } = useAuth();
  const navigate = useNavigate();

  const handleLaunchVerification = () => {
    if (isAuthenticated) {
      navigate('/verify');
    } else {
      openAuthModal(undefined, 'Authentication required to access verification tools.');
    }
  };

  const handleScrollToPipeline = () => {
    const el = document.getElementById('pipeline');
    if (el) {
      el.scrollIntoView({ behavior: 'smooth' });
    }
  };

  return (
    <div className="space-y-24 pb-16">
      {/* --- HERO SECTION --- */}
      <section className="relative pt-6 sm:pt-12">
        {/* Ambient background light bleeds */}
        <div className="absolute top-1/4 left-1/2 -translate-x-1/2 -translate-y-1/2 w-[600px] h-[350px] bg-gradient-to-tr from-emerald-500/15 via-cyan-500/10 to-indigo-500/15 rounded-full blur-[120px] pointer-events-none -z-10" />

        <div className="grid grid-cols-1 lg:grid-cols-12 gap-12 items-center">
          {/* Left Column: Headline & Action CTAs (7 cols) */}
          <div className="lg:col-span-7 space-y-6 text-center lg:text-left">
            {/* Live Security Status Pill */}
            <div className="inline-flex items-center space-x-2 px-3.5 py-1.5 rounded-full bg-emerald-950/70 border border-emerald-500/30 text-emerald-300 text-xs font-mono font-semibold shadow-inner">
              <span className="w-2 h-2 rounded-full bg-emerald-400 animate-pulse" />
              <span>ENGINE V2.4 ACTIVE</span>
              <span className="text-slate-500">•</span>
              <span className="text-emerald-400/90">ZERO-KNOWLEDGE CORE</span>
            </div>

            {/* Headline */}
            <h1 className="text-4xl sm:text-5xl lg:text-6xl font-extrabold tracking-tight text-white leading-[1.12]">
              Next-Gen{' '}
              <span className="text-transparent bg-clip-text bg-gradient-to-r from-emerald-400 via-teal-300 to-cyan-400">
                Multi-Modal Academic Certificate
              </span>{' '}
              Forensic & Integrity Engine
            </h1>

            {/* Subheading */}
            <p className="text-base sm:text-lg text-slate-300 max-w-2xl mx-auto lg:mx-0 leading-relaxed">
              Mitigating academic fraud through unified dual-engine OCR extraction, Error Level Analysis (ELA), Computer Vision deep feature attribution, and evidential multi-indicator score fusion.
            </p>

            {/* Dual CTAs */}
            <div className="flex flex-wrap items-center justify-center lg:justify-start gap-4 pt-2">
              <button
                onClick={handleLaunchVerification}
                className="shimmer-button inline-flex items-center space-x-2 px-7 py-4 rounded-2xl bg-gradient-to-r from-emerald-600 to-teal-600 hover:from-emerald-500 hover:to-teal-500 text-white font-bold text-sm shadow-xl shadow-emerald-600/30 transition-all hover:scale-105 active:scale-95 cursor-pointer"
              >
                <ShieldCheck className="w-5 h-5 text-emerald-200" />
                <span>Verify a Certificate</span>
                <ArrowRight className="w-4 h-4 ml-1" />
              </button>

              <button
                onClick={handleScrollToPipeline}
                className="inline-flex items-center space-x-2 px-6 py-4 rounded-2xl bg-slate-900/80 hover:bg-slate-800 text-slate-200 font-semibold text-sm border border-slate-700/80 hover:border-slate-600 transition-all hover:scale-105 active:scale-95"
              >
                <Layers className="w-4 h-4 text-cyan-400" />
                <span>Explore Forensic Architecture</span>
              </button>
            </div>
          </div>

          {/* Right Column: Three.js Interactive 3D Hero Canvas (5 cols) */}
          <div className="lg:col-span-5 relative">
            <Hero3DCanvas />
          </div>
        </div>

        {/* --- LIVE SECURITY METRICS RIBBON --- */}
        <div className="mt-16 grid grid-cols-2 md:grid-cols-4 gap-4">
          <div className="glass-card rounded-2xl p-5 border border-slate-800 text-center space-y-1">
            <span className="text-2xl sm:text-3xl font-extrabold text-emerald-400 font-mono block">
              10-Stage
            </span>
            <span className="text-xs font-semibold text-slate-300 block">
              Multi-Modal Pipeline
            </span>
            <span className="text-[10px] text-slate-500 font-mono">
              Intake to Dempster-Shafer
            </span>
          </div>

          <div className="glass-card rounded-2xl p-5 border border-slate-800 text-center space-y-1">
            <span className="text-2xl sm:text-3xl font-extrabold text-cyan-400 font-mono block">
              99.4%
            </span>
            <span className="text-xs font-semibold text-slate-300 block">
              Tamper Precision
            </span>
            <span className="text-[10px] text-slate-500 font-mono">
              FPR &lt; 0.4% on 24k Benchmark
            </span>
          </div>

          <div className="glass-card rounded-2xl p-5 border border-slate-800 text-center space-y-1">
            <span className="text-2xl sm:text-3xl font-extrabold text-teal-400 font-mono block">
              Zero-Knowledge
            </span>
            <span className="text-xs font-semibold text-slate-300 block">
              Hash Verification
            </span>
            <span className="text-[10px] text-slate-500 font-mono">
              HMAC-SHA256 & Public Ledgers
            </span>
          </div>

          <div className="glass-card rounded-2xl p-5 border border-slate-800 text-center space-y-1">
            <span className="text-2xl sm:text-3xl font-extrabold text-indigo-400 font-mono block">
              &lt; 1.8s
            </span>
            <span className="text-xs font-semibold text-slate-300 block">
              End-to-End Latency
            </span>
            <span className="text-[10px] text-slate-500 font-mono">
              Optimized Torch & OCR Ensemble
            </span>
          </div>
        </div>
      </section>

      {/* --- PROBLEM VS SOLUTION MATRIX --- */}
      <ProblemSolutionMatrix />

      {/* --- 10-STAGE PIPELINE VISUALIZATION --- */}
      <PipelineVisualization />

      {/* --- INTERACTIVE DEMO SANDBOX (SPLIT SLIDER) --- */}
      <InteractiveDemoSandbox />

      {/* --- EMPIRICAL RESEARCH BENCHMARK MATRIX --- */}
      <ResearchMatrix />

      {/* --- BOTTOM CALL TO ACTION BANNER --- */}
      <section className="relative rounded-3xl p-8 sm:p-12 overflow-hidden border border-emerald-500/30 bg-gradient-to-r from-[#0b1324] via-[#0d1c33] to-[#0b1324] shadow-2xl text-center space-y-6">
        <div className="w-16 h-16 rounded-2xl bg-emerald-500/20 text-emerald-400 border border-emerald-500/30 mx-auto flex items-center justify-center">
          <Scan className="w-8 h-8 text-emerald-400" />
        </div>

        <div className="space-y-2 max-w-2xl mx-auto">
          <h2 className="text-3xl sm:text-4xl font-extrabold text-white tracking-tight">
            Ready to Verify with Forensic Certainty?
          </h2>
          <p className="text-sm text-slate-400">
            Launch the neural inspection portal to upload academic credentials, inspect pixel-level Error Level Analysis heatmaps, and generate cryptographic audit dossiers.
          </p>
        </div>

        <div className="flex flex-wrap items-center justify-center gap-4 pt-2">
          <button
            onClick={handleLaunchVerification}
            className="shimmer-button inline-flex items-center space-x-2 px-8 py-4 rounded-2xl bg-emerald-600 hover:bg-emerald-500 text-white font-bold text-sm shadow-xl shadow-emerald-600/30 transition-all hover:scale-105 active:scale-95 cursor-pointer"
          >
            <ShieldCheck className="w-5 h-5 text-emerald-200" />
            <span>Launch Forensic Scanner Now</span>
            <ArrowRight className="w-4 h-4 ml-1" />
          </button>
        </div>
      </section>
    </div>
  );
};
