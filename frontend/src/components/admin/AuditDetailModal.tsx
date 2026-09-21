import React from 'react';
import { X, FileCode, Check, Copy } from 'lucide-react';
import { AuditLogItem } from '../../types/admin';

interface AuditDetailModalProps {
  log: AuditLogItem | null;
  onClose: () => void;
}

export const AuditDetailModal: React.FC<AuditDetailModalProps> = ({ log, onClose }) => {
  const [copied, setCopied] = React.useState<boolean>(false);
  if (!log) return null;

  const jsonString = JSON.stringify(log.details, null, 2);

  const handleCopy = () => {
    navigator.clipboard.writeText(jsonString);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/80 backdrop-blur-sm animate-fadeIn">
      <div className="glass-card rounded-2xl max-w-2xl w-full border border-slate-700/80 shadow-2xl overflow-hidden flex flex-col max-h-[85vh]">
        {/* Modal Header */}
        <div className="flex items-center justify-between p-4 border-b border-slate-800 bg-slate-900/60">
          <div className="flex items-center space-x-2.5">
            <div className="p-2 rounded-xl bg-purple-500/10 text-purple-400 border border-purple-500/20">
              <FileCode className="w-4 h-4" />
            </div>
            <div>
              <h3 className="text-sm font-bold text-slate-100">Audit Event Details</h3>
              <p className="text-xs text-slate-400">
                Action: <span className="font-mono text-emerald-400">{log.action}</span> • IP: {log.ip_address || 'Internal'}
              </p>
            </div>
          </div>

          <button
            onClick={onClose}
            className="p-1.5 rounded-lg text-slate-400 hover:text-white hover:bg-slate-800 transition-colors"
          >
            <X className="w-5 h-5" />
          </button>
        </div>

        {/* Modal Body */}
        <div className="p-6 overflow-y-auto space-y-4">
          <div className="flex items-center justify-between text-xs text-slate-400">
            <span>Payload Data:</span>
            <button
              onClick={handleCopy}
              className="inline-flex items-center space-x-1 text-xs text-slate-400 hover:text-slate-200 bg-slate-800 px-2.5 py-1 rounded-lg border border-slate-700 transition-colors"
            >
              {copied ? <Check className="w-3.5 h-3.5 text-emerald-400" /> : <Copy className="w-3.5 h-3.5" />}
              <span>{copied ? 'Copied' : 'Copy JSON'}</span>
            </button>
          </div>

          <div className="bg-slate-950 p-4 rounded-xl border border-slate-800 overflow-x-auto">
            <pre className="text-xs font-mono text-cyan-300 leading-relaxed">
              <code>{jsonString}</code>
            </pre>
          </div>

          <div className="grid grid-cols-2 gap-3 text-xs text-slate-400">
            <div>
              <span className="text-slate-500 block text-[10px] uppercase font-semibold">Event ID</span>
              <code className="text-slate-300 font-mono text-[11px] truncate block">{log.id}</code>
            </div>
            <div>
              <span className="text-slate-500 block text-[10px] uppercase font-semibold">Recorded At</span>
              <span className="text-slate-300">{new Date(log.created_at).toLocaleString()}</span>
            </div>
          </div>
        </div>

        {/* Modal Footer */}
        <div className="p-3 border-t border-slate-800 bg-slate-900/40 text-right">
          <button
            onClick={onClose}
            className="px-4 py-2 rounded-xl bg-slate-800 hover:bg-slate-700 text-slate-200 text-xs font-semibold transition-colors"
          >
            Close Inspector
          </button>
        </div>
      </div>
    </div>
  );
};
