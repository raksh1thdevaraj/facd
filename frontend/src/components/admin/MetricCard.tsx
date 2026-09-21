import React, { ElementType } from 'react';
import { TrendingUp, TrendingDown } from 'lucide-react';

interface MetricCardProps {
  title: string;
  value: string | number;
  subtitle?: string;
  trend?: string;
  isPositiveTrend?: boolean;
  icon: ElementType;
  accentColor?: 'emerald' | 'amber' | 'rose' | 'cyan' | 'purple';
}

export const MetricCard: React.FC<MetricCardProps> = ({
  title,
  value,
  subtitle,
  trend,
  isPositiveTrend = true,
  icon: Icon,
  accentColor = 'emerald',
}) => {
  const getColors = () => {
    switch (accentColor) {
      case 'rose':
        return {
          iconBg: 'bg-rose-500/10 text-rose-400 border-rose-500/20',
          valColor: 'text-rose-400',
        };
      case 'amber':
        return {
          iconBg: 'bg-amber-500/10 text-amber-400 border-amber-500/20',
          valColor: 'text-amber-400',
        };
      case 'cyan':
        return {
          iconBg: 'bg-cyan-500/10 text-cyan-400 border-cyan-500/20',
          valColor: 'text-cyan-400',
        };
      case 'purple':
        return {
          iconBg: 'bg-purple-500/10 text-purple-400 border-purple-500/20',
          valColor: 'text-purple-400',
        };
      case 'emerald':
      default:
        return {
          iconBg: 'bg-emerald-500/10 text-emerald-400 border-emerald-500/20',
          valColor: 'text-emerald-400',
        };
    }
  };

  const colors = getColors();

  return (
    <div className="glass-card rounded-2xl p-5 border border-slate-800 space-y-3">
      <div className="flex items-center justify-between">
        <span className="text-xs font-semibold text-slate-400 uppercase tracking-wider">{title}</span>
        <div className={`p-2 rounded-xl border ${colors.iconBg}`}>
          <Icon className="w-4 h-4" />
        </div>
      </div>

      <div className="flex items-baseline justify-between">
        <span className={`text-2xl sm:text-3xl font-extrabold font-mono ${colors.valColor}`}>
          {value}
        </span>

        {trend && (
          <span
            className={`inline-flex items-center space-x-1 text-xs font-semibold ${
              isPositiveTrend ? 'text-emerald-400' : 'text-rose-400'
            }`}
          >
            {isPositiveTrend ? (
              <TrendingUp className="w-3.5 h-3.5" />
            ) : (
              <TrendingDown className="w-3.5 h-3.5" />
            )}
            <span>{trend}</span>
          </span>
        )}
      </div>

      {subtitle && <p className="text-[11px] text-slate-500">{subtitle}</p>}
    </div>
  );
};
