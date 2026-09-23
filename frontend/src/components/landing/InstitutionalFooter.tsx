import React from 'react';
import { ShieldCheck } from 'lucide-react';

export const InstitutionalFooter: React.FC = () => {
  return (
    <footer className="border-t border-slate-800/80 bg-[#060911] text-xs text-slate-400 pt-12 pb-8 mt-16">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 space-y-10">
        {/* Compliance Badges Ribbon */}
        <div className="grid grid-cols-2 sm:grid-cols-4 gap-4 p-5 rounded-2xl bg-slate-900/60 border border-slate-800 text-center">
          <div className="space-y-1">
            <span className="text-emerald-400 font-bold font-mono text-sm block">FERPA & GDPR</span>
            <span className="text-[11px] text-slate-500">Zero-Knowledge Student Privacy</span>
          </div>
          <div className="space-y-1">
            <span className="text-cyan-400 font-bold font-mono text-sm block">ISO / IEC 27001</span>
            <span className="text-[11px] text-slate-500">Cryptographic Security Standard</span>
          </div>
          <div className="space-y-1">
            <span className="text-teal-400 font-bold font-mono text-sm block">HMAC-SHA256</span>
            <span className="text-[11px] text-slate-500">Tamper-Evident Report Signatures</span>
          </div>
          <div className="space-y-1">
            <span className="text-indigo-400 font-bold font-mono text-sm block">W3C Verifiable</span>
            <span className="text-[11px] text-slate-500">Decentralized Identifier Ready</span>
          </div>
        </div>

        {/* Links & Information Columns */}
        <div className="grid grid-cols-1 md:grid-cols-4 gap-8">
          {/* Brand Col */}
          <div className="space-y-3 md:col-span-1">
            <div className="flex items-center space-x-2.5">
              <div className="p-2 rounded-xl bg-gradient-to-tr from-emerald-600 to-teal-500 text-white shadow-lg shadow-emerald-500/20">
                <ShieldCheck className="w-5 h-5" />
              </div>
              <span className="font-extrabold text-base text-white tracking-tight">
                CertiShield AI
              </span>
            </div>
            <p className="text-[11px] text-slate-500 leading-relaxed">
              VeriDoc Multi-Modal Forensic Engine for high-throughput academic certificate fraud detection, OCR alignment, and Error Level Analysis.
            </p>
            <div className="flex items-center space-x-2 font-mono text-[10px] text-emerald-400">
              <span className="w-2 h-2 rounded-full bg-emerald-400 animate-pulse" />
              <span>ENGINE V2.4 ONLINE • 99.4% PRECISION</span>
            </div>
          </div>

          {/* Forensic Modules */}
          <div className="space-y-2">
            <h4 className="text-xs font-bold text-slate-200 font-mono uppercase tracking-wider">
              Forensic Modules
            </h4>
            <ul className="space-y-1.5 text-[11px] text-slate-500">
              <li>Dual-Engine OCR Layout Analysis</li>
              <li>Multi-Scale Error Level Analysis (ELA)</li>
              <li>SIFT / ORB Keypoint Homography</li>
              <li>ResNet-50 Grad-CAM Visual Heatmaps</li>
              <li>Dempster-Shafer Evidential Fusion</li>
            </ul>
          </div>

          {/* Research & Compliance */}
          <div className="space-y-2">
            <h4 className="text-xs font-bold text-slate-200 font-mono uppercase tracking-wider">
              Research & Standards
            </h4>
            <ul className="space-y-1.5 text-[11px] text-slate-500">
              <li>IEEE Trans. on Information Forensics (2023)</li>
              <li>ACM Symposium on Applied Computing (2024)</li>
              <li>Elsevier Forensic Science International</li>
              <li>Accredited University Registrars Consortium</li>
              <li>Zero-Knowledge Ephemeral Intake Policy</li>
            </ul>
          </div>

          {/* Security & Cryptography */}
          <div className="space-y-2">
            <h4 className="text-xs font-bold text-slate-200 font-mono uppercase tracking-wider">
              Cryptographic Trust
            </h4>
            <div className="p-3 rounded-xl bg-slate-900/80 border border-slate-800 space-y-1 text-[11px]">
              <span className="text-slate-400 block font-mono text-[10px]">SIGNATURE FINGERPRINT</span>
              <p className="font-mono text-emerald-400 truncate text-[10px]">
                0x9F83A2B7C4D1E8902BCA4710
              </p>
              <span className="text-[10px] text-slate-500 block">
                Audited & timestamped via RFC 3161 cryptographic protocol.
              </span>
            </div>
          </div>
        </div>

        {/* Copyright & Disclaimer */}
        <div className="pt-8 border-t border-slate-800/80 flex flex-col sm:flex-row items-center justify-between text-[11px] text-slate-600 gap-4">
          <p>© {new Date().getFullYear()} CertiShield AI • VeriDoc Forensic Engine. All rights reserved.</p>
          <div className="flex items-center space-x-6">
            <span className="hover:text-slate-400 cursor-pointer">Security Policy</span>
            <span className="hover:text-slate-400 cursor-pointer">FERPA Privacy</span>
            <span className="hover:text-slate-400 cursor-pointer">API Documentation</span>
          </div>
        </div>
      </div>
    </footer>
  );
};
