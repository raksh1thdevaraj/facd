import React from 'react';
import {
  FileSearch,
  History,
  Calculator,
  ShieldCheck,
  ChevronLeft,
  ChevronRight,
} from 'lucide-react';

export type EnterpriseTab = 'inspection' | 'ledger' | 'schemes';

interface EnterpriseSidebarProps {
  activeTab: EnterpriseTab;
  onTabChange: (tab: EnterpriseTab) => void;
  isCollapsed?: boolean;
  onToggleCollapse?: () => void;
}

export const EnterpriseSidebar: React.FC<EnterpriseSidebarProps> = ({
  activeTab,
  onTabChange,
  isCollapsed = false,
  onToggleCollapse,
}) => {
  const navItems = [
    {
      id: 'inspection' as EnterpriseTab,
      label: 'Document Ingestion & Live Inspection',
      shortLabel: 'Inspect',
      icon: FileSearch,
      badge: 'Live',
    },
    {
      id: 'ledger' as EnterpriseTab,
      label: 'Audit Ledger & History',
      shortLabel: 'Ledger',
      icon: History,
      badge: null,
    },
    {
      id: 'schemes' as EnterpriseTab,
      label: 'VTU Grading & Schemes Matrix',
      shortLabel: 'Schemes',
      icon: Calculator,
      badge: 'CBCS',
    },
  ];

  return (
    <aside
      className={`bg-white border-r border-slate-200 transition-all duration-200 flex flex-col justify-between shrink-0 ${
        isCollapsed ? 'w-16' : 'w-64'
      }`}
    >
      <div className="p-3 space-y-4">
        {/* Navigation list */}
        <nav className="space-y-1">
          {navItems.map((item) => {
            const Icon = item.icon;
            const isActive = activeTab === item.id;
            return (
              <button
                key={item.id}
                onClick={() => onTabChange(item.id)}
                className={`w-full flex items-center px-3 py-2.5 rounded-lg text-xs font-medium transition-colors ${
                  isActive
                    ? 'bg-indigo-50 text-indigo-900 border border-indigo-200 font-semibold shadow-xs'
                    : 'text-slate-600 hover:text-slate-900 hover:bg-slate-50 border border-transparent'
                }`}
                title={item.label}
              >
                <Icon
                  className={`w-4 h-4 shrink-0 ${
                    isActive ? 'text-indigo-800' : 'text-slate-400 group-hover:text-slate-600'
                  }`}
                />
                {!isCollapsed && (
                  <div className="ml-3 flex-1 flex items-center justify-between truncate">
                    <span className="truncate">{item.label}</span>
                    {item.badge && (
                      <span
                        className={`text-[9px] font-mono uppercase px-1.5 py-0.5 rounded ${
                          isActive
                            ? 'bg-indigo-200/60 text-indigo-900'
                            : 'bg-slate-100 text-slate-500'
                        }`}
                      >
                        {item.badge}
                      </span>
                    )}
                  </div>
                )}
              </button>
            );
          })}
        </nav>

        {/* Quick Institutional Info Card */}
        {!isCollapsed && (
          <div className="p-3 rounded-lg bg-slate-50 border border-slate-200 space-y-1.5 text-[11px]">
            <div className="flex items-center space-x-1.5 text-slate-700 font-semibold">
              <ShieldCheck className="w-3.5 h-3.5 text-indigo-700" />
              <span>Inspection Standard</span>
            </div>
            <p className="text-slate-500 text-[10px] leading-relaxed">
              Strictly configured for VTU Karnataka CBCS marksheets & autonomous engineering affiliated grade cards.
            </p>
            <div className="pt-1 text-[10px] text-slate-400 font-mono">
              Engine: Gemini Vision 2.5 + Deterministic Math
            </div>
          </div>
        )}
      </div>

      {/* Collapse Toggle */}
      {onToggleCollapse && (
        <div className="p-3 border-t border-slate-200">
          <button
            onClick={onToggleCollapse}
            className="w-full flex items-center justify-center p-2 rounded-lg text-slate-400 hover:text-slate-600 hover:bg-slate-50 text-xs transition-colors"
            title={isCollapsed ? 'Expand sidebar' : 'Collapse sidebar'}
          >
            {isCollapsed ? <ChevronRight className="w-4 h-4" /> : <ChevronLeft className="w-4 h-4" />}
          </button>
        </div>
      )}
    </aside>
  );
};
