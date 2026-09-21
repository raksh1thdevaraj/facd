import React from 'react';

interface ScoreGaugeProps {
  score: number; // 0.0 to 1.0
  size?: number;
  strokeWidth?: number;
}

export const ScoreGauge: React.FC<ScoreGaugeProps> = ({
  score,
  size = 220,
  strokeWidth = 16,
}) => {
  const percentage = Math.min(100, Math.max(0, score * 100));
  const radius = (size - strokeWidth) / 2;
  const circumference = 2 * Math.PI * radius;
  const strokeDashoffset = circumference - (percentage / 100) * circumference;

  const getColor = () => {
    if (percentage >= 75) return '#10b981'; // emerald-500
    if (percentage >= 45) return '#f59e0b'; // amber-500
    return '#f43f5e'; // rose-500
  };

  const color = getColor();

  return (
    <div className="glass-card rounded-2xl p-6 border border-slate-800 shadow-xl flex flex-col items-center justify-center text-center">
      <h3 className="text-sm font-semibold text-slate-300 mb-4">
        Authenticity Confidence Gauge
      </h3>

      <div className="relative flex items-center justify-center" style={{ width: size, height: size }}>
        <svg width={size} height={size} className="transform -rotate-90">
          {/* Background Track */}
          <circle
            cx={size / 2}
            cy={size / 2}
            r={radius}
            stroke="#1e293b"
            strokeWidth={strokeWidth}
            fill="transparent"
          />
          {/* Progress Arc */}
          <circle
            cx={size / 2}
            cy={size / 2}
            r={radius}
            stroke={color}
            strokeWidth={strokeWidth}
            strokeDasharray={circumference}
            strokeDashoffset={strokeDashoffset}
            strokeLinecap="round"
            fill="transparent"
            className="transition-all duration-1000 ease-out"
          />
        </svg>

        {/* Center Content */}
        <div className="absolute inset-0 flex flex-col items-center justify-center">
          <span className="text-4xl font-extrabold font-mono text-slate-100 tracking-tight">
            {percentage.toFixed(1)}%
          </span>
          <span className="text-xs uppercase tracking-wider font-semibold mt-1" style={{ color }}>
            {percentage >= 75 ? 'Authentic' : percentage >= 45 ? 'Suspicious' : 'Manipulated'}
          </span>
          <span className="text-[11px] text-slate-400 mt-0.5">Fusion Score</span>
        </div>
      </div>

      {/* Threshold Legend */}
      <div className="mt-5 w-full grid grid-cols-3 gap-2 text-center text-[11px] pt-4 border-t border-slate-800/80">
        <div className="p-1.5 rounded bg-rose-950/30 border border-rose-900/40 text-rose-300">
          &lt; 45% Manipulated
        </div>
        <div className="p-1.5 rounded bg-amber-950/30 border border-amber-900/40 text-amber-300">
          45-74% Suspicious
        </div>
        <div className="p-1.5 rounded bg-emerald-950/30 border border-emerald-900/40 text-emerald-300">
          &ge; 75% Authentic
        </div>
      </div>
    </div>
  );
};
