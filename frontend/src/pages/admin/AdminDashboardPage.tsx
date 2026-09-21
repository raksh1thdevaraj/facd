import React, { useState } from 'react';
import { AnalyticsOverview } from './AnalyticsOverview';
import { SystemHealthTab } from './SystemHealthTab';
import { InstitutionsManager } from './InstitutionsManager';
import { TemplatesManager } from './TemplatesManager';
import { AuditLogsViewer } from './AuditLogsViewer';
import {
  BarChart3,
  Activity,
  Building2,
  Stamp,
  ShieldCheck,
  FileCode,
} from 'lucide-react';

type AdminTab = 'overview' | 'diagnostics' | 'institutions' | 'templates' | 'audit';

export const AdminDashboardPage: React.FC = () => {
  const [activeTab, setActiveTab] = useState<AdminTab>('overview');

  const tabs: { id: AdminTab; label: string; icon: React.ElementType }[] = [
    { id: 'overview', label: 'Fraud Intelligence', icon: BarChart3 },
    { id: 'diagnostics', label: 'System Health', icon: Activity },
    { id: 'institutions', label: 'Universities', icon: Building2 },
    { id: 'templates', label: 'Master Templates', icon: Stamp },
    { id: 'audit', label: 'Audit Trail', icon: FileCode },
  ];

  return (
    <div className="space-y-8 pb-16">
      {/* Top Banner */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 border-b border-slate-800 pb-6">
        <div className="flex items-center space-x-3">
          <div className="p-3 rounded-2xl bg-gradient-to-tr from-emerald-600 to-teal-500 text-white shadow-xl shadow-emerald-500/20">
            <ShieldCheck className="w-7 h-7" />
          </div>
          <div>
            <div className="flex items-center space-x-2">
              <h2 className="text-2xl font-black text-slate-100">Administrative Control Center</h2>
              <span className="px-2 py-0.5 rounded text-[10px] font-bold uppercase bg-emerald-500/10 text-emerald-400 border border-emerald-500/20">
                Admin Console
              </span>
            </div>
            <p className="text-xs text-slate-400 mt-1">
              Multi-institutional forensics management, system diagnostics, and compliance audit log
            </p>
          </div>
        </div>

        {/* Tab switcher buttons */}
        <div className="flex flex-wrap items-center gap-1.5 p-1 rounded-xl bg-slate-900 border border-slate-800 self-start sm:self-auto text-xs font-semibold">
          {tabs.map((tab) => {
            const Icon = tab.icon;
            const isActive = activeTab === tab.id;
            return (
              <button
                key={tab.id}
                onClick={() => setActiveTab(tab.id)}
                className={`flex items-center space-x-2 px-3.5 py-2 rounded-lg transition-all ${
                  isActive
                    ? 'bg-slate-800 text-slate-100 shadow border border-slate-700'
                    : 'text-slate-400 hover:text-slate-200 hover:bg-slate-800/40'
                }`}
              >
                <Icon className={`w-3.5 h-3.5 ${isActive ? 'text-emerald-400' : ''}`} />
                <span>{tab.label}</span>
              </button>
            );
          })}
        </div>
      </div>

      {/* Tab Panels */}
      <div>
        {activeTab === 'overview' && <AnalyticsOverview />}
        {activeTab === 'diagnostics' && <SystemHealthTab />}
        {activeTab === 'institutions' && <InstitutionsManager />}
        {activeTab === 'templates' && <TemplatesManager />}
        {activeTab === 'audit' && <AuditLogsViewer />}
      </div>
    </div>
  );
};
