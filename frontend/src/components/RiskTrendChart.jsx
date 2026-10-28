import React, { useState, useMemo } from 'react';
import { Link } from 'react-router-dom';
import { TrendingUp, Clock, AlertCircle, PlusCircle, Activity } from 'lucide-react';

/**
 * Professional SVG Line Chart for Patient Cardiovascular Risk Trend
 * Visualizes historical risk probability changes across real clinical assessments.
 * Strict Rule: Real patient data only, no dummy data, hover-only values.
 */
export default function RiskTrendChart({ predictions = [], loading = false }) {
  const [activeIndex, setActiveIndex] = useState(null);

  // Process and sort real assessment history chronologically (oldest to newest)
  const processedData = useMemo(() => {
    if (!predictions || !Array.isArray(predictions) || predictions.length === 0) {
      return [];
    }

    // Filter valid historical predictions
    const valid = predictions.filter((p) => {
      if (!p || !p.created_at) return false;
      const raw = Number(p.ensemble_probability);
      return !isNaN(raw) && isFinite(raw);
    });

    // Chronological sort: oldest assessment first -> newest last (left to right on X axis)
    const sorted = [...valid].sort(
      (a, b) => new Date(a.created_at).getTime() - new Date(b.created_at).getTime()
    );

    return sorted.map((p) => {
      const raw = Number(p.ensemble_probability);
      // Backend stores ensemble_probability as decimal (0 to 1, e.g. 0.08 or 0.72)
      // If already > 1 (e.g. 8 or 72), prevent double multiplication
      const pct = raw <= 1.0 ? raw * 100 : raw;
      const clampedPct = Math.min(Math.max(pct, 0), 100);

      return {
        id: p.id,
        assessmentId: p.assessment_id,
        rawProbability: raw,
        probability: clampedPct,
        displayProbability: Math.round(clampedPct),
        riskLevel: String(p.risk_level || 'LOW').toUpperCase(),
        predictionLabel: p.prediction_label || '',
        modelVersion: p.model_version || '1.0.0',
        createdAt: p.created_at,
      };
    });
  }, [predictions]);

  // Chart layout dimensions (SVG viewBox)
  const viewBoxWidth = 600;
  const viewBoxHeight = 240;
  const paddingLeft = 48; // Space for Y-axis percentage labels
  const paddingRight = 24;
  const paddingTop = 26;  // Breathing room at top (100% mark)
  const paddingBottom = 42; // Space for X-axis assessment dates
  const plotWidth = viewBoxWidth - paddingLeft - paddingRight;
  const plotHeight = viewBoxHeight - paddingTop - paddingBottom;
  const yZero = paddingTop + plotHeight; // Y coordinate for 0%

  // Compute point coordinates
  const points = useMemo(() => {
    const count = processedData.length;
    if (count === 0) return [];

    return processedData.map((d, idx) => {
      let x;
      if (count === 1) {
        // Single data point centered on the timeline
        x = paddingLeft + plotWidth / 2;
      } else {
        x = paddingLeft + (idx / (count - 1)) * plotWidth;
      }
      const y = yZero - (d.probability / 100) * plotHeight;
      return {
        ...d,
        x: Number(x.toFixed(2)),
        y: Number(y.toFixed(2)),
        index: idx,
      };
    });
  }, [processedData, plotWidth, plotHeight, paddingLeft, yZero]);

  // Smooth spline path generator
  const linePath = useMemo(() => {
    if (points.length < 2) return '';
    if (points.length === 2) {
      return `M ${points[0].x} ${points[0].y} L ${points[1].x} ${points[1].y}`;
    }

    let path = `M ${points[0].x} ${points[0].y}`;
    const tension = 0.15; // Gentle medical-waveform smoothing

    for (let i = 0; i < points.length - 1; i++) {
      const p0 = points[i === 0 ? 0 : i - 1];
      const p1 = points[i];
      const p2 = points[i + 1];
      const p3 = points[i + 2] || p2;

      const cp1x = p1.x + (p2.x - p0.x) * tension;
      const cp1y = p1.y + (p2.y - p0.y) * tension;
      const cp2x = p2.x - (p3.x - p1.x) * tension;
      const cp2y = p2.y - (p3.y - p1.y) * tension;

      path += ` C ${cp1x.toFixed(2)} ${cp1y.toFixed(2)}, ${cp2x.toFixed(2)} ${cp2y.toFixed(2)}, ${p2.x.toFixed(2)} ${p2.y.toFixed(2)}`;
    }
    return path;
  }, [points]);

  // Shaded area path below the line
  const areaPath = useMemo(() => {
    if (points.length < 2 || !linePath) return '';
    const first = points[0];
    const last = points[points.length - 1];
    return `${linePath} L ${last.x} ${yZero} L ${first.x} ${yZero} Z`;
  }, [points, linePath, yZero]);

  // Risk badge style helper
  const getRiskBadgeInfo = (level) => {
    const l = String(level || 'LOW').toUpperCase();
    if (l.includes('HIGH')) {
      return {
        label: 'High Risk',
        badgeClass: 'bg-red-500/20 text-red-300 border border-red-500/40',
        dotClass: 'bg-red-500',
      };
    }
    if (l.includes('MOD') || l.includes('MED')) {
      return {
        label: 'Moderate Risk',
        badgeClass: 'bg-amber-500/20 text-amber-300 border border-amber-500/40',
        dotClass: 'bg-amber-400',
      };
    }
    return {
      label: 'Low Risk',
      badgeClass: 'bg-emerald-500/20 text-emerald-300 border border-emerald-500/40',
      dotClass: 'bg-emerald-400',
    };
  };

  // Format short date for X-axis
  const formatXDate = (dateStr) => {
    if (!dateStr) return '';
    const d = new Date(dateStr);
    return d.toLocaleDateString('en-GB', { day: 'numeric', month: 'short' });
  };

  // Format full date & time for tooltip
  const formatFullDateTime = (dateStr) => {
    if (!dateStr) return '';
    const d = new Date(dateStr);
    const dateFormatted = d.toLocaleDateString('en-GB', {
      day: 'numeric',
      month: 'short',
      year: 'numeric',
    });
    const timeFormatted = d.toLocaleTimeString([], {
      hour: '2-digit',
      minute: '2-digit',
    });
    return `${dateFormatted}, ${timeFormatted}`;
  };

  // Loading Skeleton State
  if (loading) {
    return (
      <div className="h-60 w-full flex flex-col items-center justify-center text-center p-6 bg-warm-bg/40 rounded-2xl animate-pulse space-y-3">
        <div className="w-8 h-8 rounded-full border-2 border-brand-800 border-t-transparent animate-spin" />
        <p className="text-xs font-semibold text-warm-muted">Loading risk assessment trajectory...</p>
      </div>
    );
  }

  // Clean Empty State (Requirement 2 & 8: No dummy data)
  if (processedData.length === 0) {
    return (
      <div className="h-60 w-full flex flex-col items-center justify-center text-center p-6 bg-warm-bg/40 rounded-2xl border border-dashed border-warm-border">
        <div className="w-12 h-12 rounded-full bg-rose-50 border border-brand-200/60 flex items-center justify-center text-brand-800 mb-3 shadow-xs">
          <Activity className="w-6 h-6" />
        </div>
        <p className="text-sm font-bold text-gray-900">No Assessment History Recorded</p>
        <p className="text-xs text-warm-muted max-w-sm mt-1 leading-relaxed">
          Complete clinical assessments to visualize your personalized cardiovascular risk probability trend over time.
        </p>
        <Link
          to="/patient/assessment"
          className="inline-flex items-center space-x-1.5 text-xs font-bold text-white bg-brand-800 hover:bg-brand-900 shadow-sm shadow-brand-900/20 px-4 py-2 rounded-full mt-3 transition-colors"
        >
          <PlusCircle className="w-4 h-4" />
          <span>Complete Initial Assessment</span>
        </Link>
      </div>
    );
  }

  const activePoint = activeIndex !== null ? points[activeIndex] : null;

  return (
    <div className="w-full space-y-2 select-none">
      {/* Chart Canvas Container */}
      <div
        className="relative w-full h-56 sm:h-64"
        onMouseLeave={() => setActiveIndex(null)}
        onClick={() => setActiveIndex(null)}
      >
        <svg
          viewBox={`0 0 ${viewBoxWidth} ${viewBoxHeight}`}
          className="w-full h-full overflow-visible"
          preserveAspectRatio="none"
          role="img"
          aria-label="Patient cardiovascular risk probability trend across historical assessments"
        >
          <defs>
            {/* Area Fill Gradient: HeartShield Burgundy to Soft Pink to Transparent */}
            <linearGradient id="riskAreaGradient" x1="0" y1="0" x2="0" y2="1">
              <stop offset="0%" stopColor="#800020" stopOpacity="0.22" />
              <stop offset="75%" stopColor="#F8D0D6" stopOpacity="0.05" />
              <stop offset="100%" stopColor="#FFFFFF" stopOpacity="0.0" />
            </linearGradient>

            {/* Stroke Line Gradient: Burgundy tone */}
            <linearGradient id="riskLineGradient" x1="0" y1="0" x2="1" y2="0">
              <stop offset="0%" stopColor="#B8233E" />
              <stop offset="100%" stopColor="#800020" />
            </linearGradient>

            {/* Subtle drop shadow for points */}
            <filter id="pointGlow" x="-50%" y="-50%" width="200%" height="200%">
              <feDropShadow dx="0" dy="1" stdDeviation="1.5" floodColor="#800020" floodOpacity="0.3" />
            </filter>
          </defs>

          {/* Horizontal Grid Lines & Y-Axis Scale (0%, 25%, 50%, 75%, 100%) */}
          {[100, 75, 50, 25, 0].map((pct) => {
            const y = yZero - (pct / 100) * plotHeight;
            const isZero = pct === 0;
            return (
              <g key={pct}>
                {/* Subtle Grid Line */}
                <line
                  x1={paddingLeft}
                  y1={y}
                  x2={viewBoxWidth - paddingRight}
                  y2={y}
                  stroke="#F2D7D5"
                  strokeWidth={isZero ? '1.2' : '1'}
                  strokeDasharray={isZero ? undefined : '4 4'}
                  strokeOpacity={isZero ? '0.9' : '0.6'}
                />
                {/* Y-Axis Label */}
                <text
                  x={paddingLeft - 8}
                  y={y + 3.5}
                  textAnchor="end"
                  className="text-[10px] font-semibold fill-[#7E6360]"
                >
                  {pct}%
                </text>
              </g>
            );
          })}

          {/* Area under the line */}
          {areaPath && (
            <path
              d={areaPath}
              fill="url(#riskAreaGradient)"
              className="transition-all duration-300"
            />
          )}

          {/* Single assessment horizontal reference guide */}
          {points.length === 1 && (
            <line
              x1={paddingLeft}
              y1={points[0].y}
              x2={viewBoxWidth - paddingRight}
              y2={points[0].y}
              stroke="#800020"
              strokeWidth="1.2"
              strokeDasharray="4 4"
              strokeOpacity="0.35"
            />
          )}

          {/* Interactive Line connecting historical points */}
          {linePath && (
            <path
              d={linePath}
              fill="none"
              stroke="url(#riskLineGradient)"
              strokeWidth="2.5"
              strokeLinecap="round"
              strokeLinejoin="round"
              className="transition-all duration-300"
            />
          )}

          {/* Hover Crosshair / Vertical Guide Line */}
          {activePoint && (
            <g>
              <line
                x1={activePoint.x}
                y1={paddingTop}
                x2={activePoint.x}
                y2={yZero}
                stroke="#800020"
                strokeWidth="1.2"
                strokeDasharray="3 3"
                strokeOpacity="0.55"
              />
              <line
                x1={paddingLeft}
                y1={activePoint.y}
                x2={activePoint.x}
                y2={activePoint.y}
                stroke="#800020"
                strokeWidth="1"
                strokeDasharray="2 2"
                strokeOpacity="0.35"
              />
            </g>
          )}

          {/* X-Axis Assessment Date Labels (Ordered Oldest to Newest) */}
          {points.map((pt, idx) => {
            const isFirst = idx === 0;
            const isLast = idx === points.length - 1;
            const anchor = points.length === 1 ? 'middle' : isFirst ? 'start' : isLast ? 'end' : 'middle';
            return (
              <text
                key={`label-${pt.id || idx}`}
                x={pt.x}
                y={yZero + 18}
                textAnchor={anchor}
                className="text-[10px] font-medium fill-[#7E6360]"
              >
                {formatXDate(pt.createdAt)}
              </text>
            );
          })}

          {/* Data Points (NO permanent numbers — values show ONLY on hover) */}
          {points.map((pt, idx) => {
            const isActive = activeIndex === idx;

            return (
              <g key={`point-${pt.id || idx}`}>
                {/* Active Hover Glow Rings */}
                {isActive && (
                  <>
                    <circle
                      cx={pt.x}
                      cy={pt.y}
                      r="13"
                      fill="#800020"
                      fillOpacity="0.14"
                      className="animate-pulse"
                    />
                    <circle
                      cx={pt.x}
                      cy={pt.y}
                      r="8"
                      fill="#800020"
                      fillOpacity="0.25"
                    />
                  </>
                )}

                {/* Point Marker */}
                <circle
                  cx={pt.x}
                  cy={pt.y}
                  r={isActive ? 6 : 4.5}
                  fill={isActive ? '#800020' : '#FFFFFF'}
                  stroke="#800020"
                  strokeWidth="2.5"
                  filter={isActive ? 'url(#pointGlow)' : undefined}
                  className="transition-all duration-150"
                />

                {/* Invisible large touch/pointer hit target */}
                <circle
                  cx={pt.x}
                  cy={pt.y}
                  r="24"
                  fill="transparent"
                  className="cursor-pointer"
                  onMouseEnter={() => setActiveIndex(idx)}
                  onTouchStart={(e) => {
                    e.stopPropagation();
                    setActiveIndex(idx);
                  }}
                  onClick={(e) => {
                    e.stopPropagation();
                    setActiveIndex(idx);
                  }}
                />
              </g>
            );
          })}
        </svg>

        {/* Hover-Only Interactive Tooltip (Requirement 4) */}
        {activePoint && (() => {
          const leftPct = (activePoint.x / viewBoxWidth) * 100;
          const topPct = (activePoint.y / viewBoxHeight) * 100;
          const badgeInfo = getRiskBadgeInfo(activePoint.riskLevel);

          // Horizontal alignment adjustment near borders
          const isNearLeft = activePoint.x < 120;
          const isNearRight = activePoint.x > viewBoxWidth - 120;
          let xTransform = '-translate-x-1/2';
          if (isNearLeft) xTransform = 'translate-x-0';
          if (isNearRight) xTransform = '-translate-x-full';

          // Vertical alignment adjustment near top
          const isNearTop = activePoint.y < 75;
          const yTransform = isNearTop
            ? 'translate-y-3.5'
            : '-translate-y-full -translate-y-3.5';

          return (
            <div
              className={`absolute pointer-events-none z-30 transition-transform duration-100 ease-out ${xTransform} ${yTransform}`}
              style={{
                left: `${leftPct}%`,
                top: `${topPct}%`,
              }}
            >
              <div className="bg-gray-900/95 backdrop-blur-md text-white rounded-xl shadow-xl shadow-black/25 border border-gray-700/60 p-3 min-w-[200px] text-xs space-y-2">
                {/* Assessment Date & Time */}
                <div className="flex items-center space-x-1.5 text-gray-300 text-[11px] pb-1.5 border-b border-gray-800">
                  <Clock className="w-3.5 h-3.5 text-rose-300 shrink-0" />
                  <span className="font-semibold">{formatFullDateTime(activePoint.createdAt)}</span>
                </div>

                {/* Risk Probability (Hover Only!) */}
                <div className="flex items-baseline justify-between pt-0.5">
                  <span className="text-[11px] text-gray-400 font-medium">Risk Probability:</span>
                  <span className="text-base font-black text-white tracking-tight">
                    {activePoint.displayProbability}%
                  </span>
                </div>

                {/* Risk Classification Badge */}
                <div className="flex items-center justify-between">
                  <span className="text-[11px] text-gray-400 font-medium">Risk Tier:</span>
                  <span className={`inline-flex items-center space-x-1 px-2 py-0.5 rounded-full text-[10px] font-bold uppercase tracking-wider ${badgeInfo.badgeClass}`}>
                    <span className={`w-1.5 h-1.5 rounded-full ${badgeInfo.dotClass}`} />
                    <span>{badgeInfo.label}</span>
                  </span>
                </div>

                {/* Additional Clinical Context if available */}
                {activePoint.predictionLabel && (
                  <div className="pt-1.5 border-t border-gray-800/80 text-[10px] text-gray-400 flex items-center justify-between">
                    <span className="truncate max-w-[130px] text-gray-300">{activePoint.predictionLabel}</span>
                    <span className="font-mono text-[9px] text-gray-500">v{activePoint.modelVersion}</span>
                  </div>
                )}
              </div>
            </div>
          );
        })()}
      </div>

      {/* Footer hint / single assessment context */}
      <div className="flex items-center justify-between pt-1 text-[11px] text-warm-muted px-1">
        <span>
          {points.length === 1
            ? '1 assessment recorded — subsequent assessments will plot longitudinal trajectory'
            : `Showing ${points.length} historical assessment records in chronological order`}
        </span>
        <span className="hidden sm:inline-block italic text-[10px]">
          Hover or tap any data point for exact assessment values
        </span>
      </div>
    </div>
  );
}
