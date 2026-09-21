import React from 'react';
import { ShieldCheck, Cpu, Database, CheckSquare } from 'lucide-react';

export const Footer: React.FC = () => {
  return (
    <footer className="border-t border-slate-800/80 bg-[#080c14] py-8 text-xs text-slate-500">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 flex flex-col md:flex-row items-center justify-between gap-4">
        <div className="flex items-center space-x-3">
          <ShieldCheck className="w-5 h-5 text-emerald-500" />
          <span>CertCheck AI — Academic Certificate Tamper & Forgery Detection Platform</span>
        </div>

        <div className="flex items-center space-x-6">
          <div className="flex items-center space-x-1.5">
            <Cpu className="w-3.5 h-3.5 text-slate-400" />
            <span>Multimodal ResNet-50</span>
          </div>
          <div className="flex items-center space-x-1.5">
            <Database className="w-3.5 h-3.5 text-slate-400" />
            <span>Cryptographic Registry</span>
          </div>
          <div className="flex items-center space-x-1.5">
            <CheckSquare className="w-3.5 h-3.5 text-slate-400" />
            <span>Forensics ELA</span>
          </div>
        </div>

        <div>
          <span>© {new Date().getFullYear()} Authenticity Verification Core. Production Grade.</span>
        </div>
      </div>
    </footer>
  );
};
