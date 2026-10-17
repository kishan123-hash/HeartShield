import React from 'react';

export default function RiskGauge({ percentage = 28, riskLevel = 'Moderate Risk' }) {
  // Normalize percentage 0-100
  const val = Math.min(Math.max(Number(percentage) || 0, 0), 100);

  // SVG Gauge calculations
  const radius = 80;
  const strokeWidth = 14;
  const circumference = Math.PI * radius; // Half circle
  const strokeDashoffset = circumference - (val / 100) * circumference;

  const getRiskColor = (level) => {
    const l = String(level).toUpperCase();
    if (l.includes('HIGH')) return '#EF4444'; // Red
    if (l.includes('MOD') || l.includes('MED')) return '#F59E0B'; // Amber
    return '#10B981'; // Green
  };

  const getRiskBg = (level) => {
    const l = String(level).toUpperCase();
    if (l.includes('HIGH')) return 'bg-red-50 text-red-700 border-red-200';
    if (l.includes('MOD') || l.includes('MED')) return 'bg-amber-50 text-amber-700 border-amber-200';
    return 'bg-emerald-50 text-emerald-700 border-emerald-200';
  };

  const activeColor = getRiskColor(riskLevel);

  return (
    <div className="flex flex-col items-center justify-center p-4">
      <div className="relative w-48 h-28 flex items-center justify-center">
        <svg className="w-48 h-48 -rotate-180 transform" viewBox="0 0 200 200">
          {/* Background Arc */}
          <circle
            cx="100"
            cy="100"
            r={radius}
            fill="none"
            stroke="#F0E3E1"
            strokeWidth={strokeWidth}
            strokeDasharray={circumference}
            strokeDashoffset="0"
            strokeLinecap="round"
          />
          {/* Active Value Arc */}
          <circle
            cx="100"
            cy="100"
            r={radius}
            fill="none"
            stroke={activeColor}
            strokeWidth={strokeWidth}
            strokeDasharray={circumference}
            strokeDashoffset={strokeDashoffset}
            strokeLinecap="round"
            className="transition-all duration-1000 ease-out"
          />
        </svg>

        {/* Center Text */}
        <div className="absolute bottom-2 text-center">
          <span className="text-3xl font-black text-gray-900 tracking-tight">{val}%</span>
          <span className="block text-[11px] font-semibold text-warm-muted uppercase tracking-wider">Probability</span>
        </div>
      </div>

      {/* Risk Badge */}
      <div className={`mt-3 px-4 py-1.5 rounded-full border text-xs font-bold tracking-wide uppercase ${getRiskBg(riskLevel)}`}>
        {riskLevel}
      </div>
    </div>
  );
}
