import React from 'react';

export default function ShapBarChart({ features = [] }) {
  const defaultFeatures = [
    { feature: 'Serum Cholesterol', percentage: 32, clinical_value: '220 mg/dL' },
    { feature: 'Systolic Blood Pressure', percentage: 28, clinical_value: '142 mmHg' },
    { feature: 'Body Mass Index (BMI)', percentage: 18, clinical_value: '28.4' },
    { feature: 'Fasting Blood Glucose', percentage: 12, clinical_value: '115 mg/dL' },
    { feature: 'Smoking Status', percentage: 10, clinical_value: 'Current smoker' },
  ];

  const items = features.length > 0 ? features : defaultFeatures;

  return (
    <div className="space-y-3.5">
      {items.map((item, idx) => {
        const pct = item.percentage != null ? Math.round(item.percentage) : Math.round((item.importance || 0.1) * 100);
        const isProtective = item.direction === 'negative' || item.contribution_direction === 'negative';
        return (
          <div key={idx} className="space-y-1">
            <div className="flex justify-between items-center text-xs">
              <span className="font-semibold text-gray-800">{item.feature}</span>
              <div className="flex items-center space-x-2">
                {item.clinical_value && (
                  <span className="text-[11px] text-warm-muted">{item.clinical_value}</span>
                )}
                {item.direction && (
                  <span className={`text-[10px] font-bold px-1.5 py-0.5 rounded ${isProtective ? 'bg-emerald-50 text-emerald-700' : 'bg-rose-50 text-rose-700'}`}>
                    {isProtective ? 'Protective' : 'Risk Factor'}
                  </span>
                )}
                <span className="font-bold text-brand-800">{pct}%</span>
              </div>
            </div>
            <div className="w-full bg-warm-bg rounded-full h-2.5 overflow-hidden border border-warm-border/60">
              <div
                className={`h-2.5 rounded-full transition-all duration-700 ease-out ${
                  isProtective
                    ? 'bg-gradient-to-r from-emerald-600 to-teal-500'
                    : 'bg-gradient-to-r from-brand-700 to-rose-500'
                }`}
                style={{ width: `${Math.min(pct, 100)}%` }}
              />
            </div>
          </div>
        );
      })}
    </div>
  );
}
