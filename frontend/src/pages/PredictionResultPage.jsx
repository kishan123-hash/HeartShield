import React, { useState, useEffect } from 'react';
import { useParams, Link, useNavigate } from 'react-router-dom';
import {
  Activity,
  FileText,
  Bot,
  ArrowLeft,
  Download,
  AlertTriangle,
  CheckCircle2,
  Info,
  Sparkles,
  Layers,
  Heart,
  ShieldCheck,
  TrendingUp,
  RefreshCw
} from 'lucide-react';
import Sidebar from '../components/Sidebar';
import RiskGauge from '../components/RiskGauge';
import ShapBarChart from '../components/ShapBarChart';
import api from '../api/client';

export default function PredictionResultPage() {
  const { id } = useParams();
  const navigate = useNavigate();

  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [prediction, setPrediction] = useState(null);
  const [shapData, setShapData] = useState([]);
  const [limeData, setLimeData] = useState([]);
  const [activeXaiTab, setActiveXaiTab] = useState('shap');
  const [limeMetrics, setLimeMetrics] = useState(null);
  const [explanation, setExplanation] = useState(null);

  useEffect(() => {
    const fetchPredictionDetails = async () => {
      setLoading(true);
      setError('');
      try {
        // Fetch Prediction
        const predRes = await api.get(`/predictions/${id}`);
        setPrediction(predRes.data);

        // Fetch SHAP explanations
        try {
          const shapRes = await api.get(`/predictions/${id}/shap`);
          const rawShap = shapRes.data?.shap_values || shapRes.data?.top_features || [];
          if (rawShap.length > 0) {
            setShapData(
              rawShap.map((v) => ({
                feature: v.feature_name || v.feature,
                percentage: v.percentage != null ? Math.round(v.percentage) : Math.round(Math.abs(v.shap_value || v.importance || 0.1) * 100),
                clinical_value: v.clinical_value || (v.feature_value != null ? String(v.feature_value) : undefined),
                direction: v.contribution_direction || (v.shap_value >= 0 ? 'positive' : 'negative'),
                shap_value: v.shap_value,
              }))
            );
          }
        } catch (sErr) {
          console.warn('SHAP fetch notice:', sErr);
        }

        // Fetch LIME explanations
        try {
          const limeRes = await api.get(`/predictions/${id}/lime`);
          const rawLime = limeRes.data?.lime_values || limeRes.data?.top_features || [];
          if (rawLime.length > 0) {
            setLimeData(
              rawLime.map((v) => ({
                feature: v.feature_name || v.feature,
                percentage: v.percentage != null ? Math.round(v.percentage) : Math.round(Math.abs(v.importance_score || 0.1) * 100),
                clinical_value: v.clinical_value || (v.feature_value != null ? String(v.feature_value) : undefined),
                direction: v.contribution_direction || 'positive',
                importance: v.importance_score,
              }))
            );
            setLimeMetrics({
              accuracy: Math.round((limeRes.data.explanation_accuracy || 0.85) * 100),
              localPred: Math.round((limeRes.data.local_prediction_probability || 0.5) * 100),
            });
          }
        } catch (lErr) {
          console.warn('LIME fetch notice:', lErr);
        }

        // Fetch General Explanation
        try {
          const expRes = await api.get(`/predictions/${id}/explanation`);
          setExplanation(expRes.data);
        } catch (eErr) {
          console.warn('Explanation fetch notice:', eErr);
        }
      } catch (err) {
        console.error('Error loading prediction:', err);
        setError('Unable to load assessment prediction details. Please verify the ID or try again.');
      } finally {
        setLoading(false);
      }
    };

    if (id) {
      fetchPredictionDetails();
    }
  }, [id]);

  if (loading) {
    return (
      <div className="min-h-screen flex flex-col lg:flex-row bg-warm-bg w-full min-w-0 overflow-x-hidden">
        <Sidebar />
        <main className="flex-1 flex flex-col items-center justify-center p-8">
          <div className="w-12 h-12 border-4 border-brand-800 border-t-transparent rounded-full animate-spin mb-4" />
          <p className="text-sm font-semibold text-warm-muted">Loading ensemble prediction analysis...</p>
        </main>
      </div>
    );
  }

  if (error || !prediction) {
    return (
      <div className="min-h-screen flex flex-col lg:flex-row bg-warm-bg w-full min-w-0 overflow-x-hidden">
        <Sidebar />
        <main className="flex-1 p-8 max-w-4xl mx-auto flex flex-col items-center justify-center text-center">
          <div className="w-16 h-16 bg-red-100 text-red-600 rounded-full flex items-center justify-center mb-4">
            <AlertTriangle className="w-8 h-8" />
          </div>
          <h2 className="text-xl font-bold text-gray-900 mb-2">Prediction Not Found</h2>
          <p className="text-sm text-warm-muted max-w-md mb-6">{error || 'Unable to locate this assessment record.'}</p>
          <Link
            to="/patient/assessment"
            className="px-6 py-2.5 rounded-full bg-brand-800 text-white font-bold text-xs hover:bg-brand-900 transition-all shadow-md"
          >
            Start New Assessment
          </Link>
        </main>
      </div>
    );
  }

  const prob = Number(prediction.ensemble_probability || 0);
  const probPercent = Math.round(prob * 100);
  const riskLevel = prediction.risk_level || (prob >= 0.7 ? 'High' : prob >= 0.4 ? 'Moderate' : 'Low');
  const isHighRisk = riskLevel.toUpperCase().includes('HIGH');
  const isModRisk = riskLevel.toUpperCase().includes('MOD') || riskLevel.toUpperCase().includes('MED');

  const lrProb = Math.round(Number(prediction.logistic_probability || 0) * 100);
  const rfProb = Math.round(Number(prediction.random_forest_probability || 0) * 100);
  const xgbProb = Math.round(Number(prediction.xgboost_probability || 0) * 100);

  const lrVote = lrProb >= 50 ? 'Positive (1)' : 'Negative (0)';
  const rfVote = rfProb >= 50 ? 'Positive (1)' : 'Negative (0)';
  const xgbVote = xgbProb >= 50 ? 'Positive (1)' : 'Negative (0)';

  return (
    <div className="min-h-screen flex flex-col lg:flex-row bg-warm-bg w-full min-w-0 overflow-x-hidden">
      <Sidebar />

      <main className="flex-1 p-4 sm:p-6 lg:p-10 max-w-5xl w-full mx-auto space-y-8 min-w-0">
        {/* Top Navigation & Title */}
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
          <div className="flex items-center space-x-3">
            <button
              onClick={() => navigate('/patient/dashboard')}
              className="p-2 rounded-xl bg-white border border-warm-border text-warm-muted hover:text-brand-800 hover:bg-rose-50 transition-all"
              title="Back to Dashboard"
            >
              <ArrowLeft className="w-5 h-5" />
            </button>
            <div>
              <span className="text-[11px] font-bold uppercase tracking-wider text-brand-800 bg-brand-50 px-2.5 py-0.5 rounded-full border border-brand-200">
                Evaluation Complete
              </span>
              <h1 className="text-2xl font-black text-gray-900 tracking-tight mt-1">
                Risk Assessment Outcome
              </h1>
            </div>
          </div>

          <div className="flex items-center space-x-3">
            <Link
              to={`/patient/report/${prediction.id}`}
              className="inline-flex items-center space-x-2 px-5 py-2.5 rounded-full text-xs font-bold text-gray-700 bg-white border border-warm-border hover:bg-warm-bg transition-all shadow-xs"
            >
              <FileText className="w-4 h-4 text-brand-800" />
              <span>Full Medical Report</span>
            </Link>
            <Link
              to="/patient/chat"
              className="inline-flex items-center space-x-2 px-5 py-2.5 rounded-full text-xs font-bold text-white bg-brand-800 hover:bg-brand-900 transition-all shadow-md shadow-brand-900/20"
            >
              <Bot className="w-4 h-4" />
              <span>Discuss with AI Doctor</span>
            </Link>
          </div>
        </div>

        {/* Primary Outcome Card (Gauge + Summary) */}
        <div className="bg-white rounded-3xl p-6 sm:p-8 border border-warm-border shadow-xs grid grid-cols-1 md:grid-cols-12 gap-8 items-center">
          <div className="md:col-span-5 flex flex-col items-center justify-center border-b md:border-b-0 md:border-r border-warm-border pb-6 md:pb-0 md:pr-8">
            <RiskGauge percentage={probPercent} riskLevel={riskLevel} />
            <p className="text-xs text-warm-muted text-center mt-2 max-w-xs">
              Calculated via Hard-Voting Ensemble with calibrated classifier probabilities.
            </p>
          </div>

          <div className="md:col-span-7 space-y-4">
            <div className="flex items-center space-x-2">
              <span
                className={`px-3 py-1 rounded-full text-xs font-black uppercase tracking-wide border ${
                  isHighRisk
                    ? 'bg-red-50 text-red-700 border-red-200'
                    : isModRisk
                    ? 'bg-amber-50 text-amber-700 border-amber-200'
                    : 'bg-emerald-50 text-emerald-700 border-emerald-200'
                }`}
              >
                {prediction.prediction_label || `${riskLevel} Risk Profile`}
              </span>
              <span className="text-xs text-warm-muted">
                Evaluated on {new Date(prediction.created_at).toLocaleDateString()}
              </span>
            </div>

            <h2 className="text-xl font-bold text-gray-900">
              {isHighRisk
                ? 'Heightened Cardiovascular Risk Detected'
                : isModRisk
                ? 'Moderate Risk — Proactive Monitoring Advised'
                : 'Optimal Cardiovascular Health Profile'}
            </h2>

            <p className="text-xs text-gray-600 leading-relaxed">
              {explanation?.summary ||
                (isHighRisk
                  ? 'Your biometric and lifestyle profile indicates elevated cardiac stress factors. Clinical consultation and guided diagnostic panels (lipid electrophoresis, ECG) are strongly recommended.'
                  : isModRisk
                  ? 'Several borderline markers were identified during analysis. Lifestyle optimization in sleep hygiene, diet, and physical activity will significantly reduce future vulnerability.'
                  : 'Your physiological markers, vital signs, and daily lifestyle habits demonstrate high protective resilience against heart disease. Maintain your current active routine.')}
            </p>

            <div className="pt-2 flex flex-wrap gap-2 text-xs">
              <span className="bg-warm-bg px-3 py-1.5 rounded-lg border border-warm-border font-medium text-gray-700">
                Model: <strong>HeartShield v{prediction.model_version || '2.0'}</strong>
              </span>
              <span className="bg-warm-bg px-3 py-1.5 rounded-lg border border-warm-border font-medium text-gray-700">
                Ensemble Rule: <strong>Majority (&ge; 2 votes)</strong>
              </span>
            </div>
          </div>
        </div>

        {/* Hard-Voting Ensemble Breakdown (Screen 13 detail) */}
        <div className="space-y-4">
          <div className="flex items-center justify-between">
            <div className="flex items-center space-x-2">
              <Layers className="w-5 h-5 text-brand-800" />
              <h3 className="text-base font-bold text-gray-900">Ensemble Classifier Breakdown</h3>
            </div>
            <span className="text-xs text-warm-muted">3 Independent Estimators</span>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            {/* Logistic Regression */}
            <div className="bg-white p-5 rounded-2xl border border-warm-border shadow-xs space-y-3">
              <div className="flex items-center justify-between">
                <span className="text-xs font-bold text-gray-700">Logistic Regression</span>
                <span className="text-[10px] font-bold px-2 py-0.5 rounded-full bg-blue-50 text-blue-700 border border-blue-100">
                  Linear Baseline
                </span>
              </div>
              <div className="flex items-baseline justify-between">
                <span className="text-2xl font-black text-gray-900">{lrProb}%</span>
                <span className={`text-xs font-bold ${lrProb >= 50 ? 'text-red-600' : 'text-emerald-600'}`}>
                  Vote: {lrVote}
                </span>
              </div>
              <div className="w-full bg-warm-bg h-2 rounded-full overflow-hidden">
                <div className="bg-blue-600 h-2 rounded-full" style={{ width: `${lrProb}%` }} />
              </div>
              <p className="text-[11px] text-warm-muted leading-tight">
                Evaluates linear clinical risk factor weights with L2 regularization.
              </p>
            </div>

            {/* Random Forest */}
            <div className="bg-white p-5 rounded-2xl border border-warm-border shadow-xs space-y-3">
              <div className="flex items-center justify-between">
                <span className="text-xs font-bold text-gray-700">Random Forest</span>
                <span className="text-[10px] font-bold px-2 py-0.5 rounded-full bg-emerald-50 text-emerald-700 border border-emerald-100">
                  Bagged Ensemble
                </span>
              </div>
              <div className="flex items-baseline justify-between">
                <span className="text-2xl font-black text-gray-900">{rfProb}%</span>
                <span className={`text-xs font-bold ${rfProb >= 50 ? 'text-red-600' : 'text-emerald-600'}`}>
                  Vote: {rfVote}
                </span>
              </div>
              <div className="w-full bg-warm-bg h-2 rounded-full overflow-hidden">
                <div className="bg-emerald-600 h-2 rounded-full" style={{ width: `${rfProb}%` }} />
              </div>
              <p className="text-[11px] text-warm-muted leading-tight">
                Aggregates 100 orthogonal decision trees to mitigate individual variance.
              </p>
            </div>

            {/* XGBoost */}
            <div className="bg-white p-5 rounded-2xl border border-warm-border shadow-xs space-y-3">
              <div className="flex items-center justify-between">
                <span className="text-xs font-bold text-gray-700">XGBoost Classifier</span>
                <span className="text-[10px] font-bold px-2 py-0.5 rounded-full bg-brand-50 text-brand-800 border border-brand-200">
                  Gradient Boosted
                </span>
              </div>
              <div className="flex items-baseline justify-between">
                <span className="text-2xl font-black text-gray-900">{xgbProb}%</span>
                <span className={`text-xs font-bold ${xgbProb >= 50 ? 'text-red-600' : 'text-emerald-600'}`}>
                  Vote: {xgbVote}
                </span>
              </div>
              <div className="w-full bg-warm-bg h-2 rounded-full overflow-hidden">
                <div className="bg-brand-800 h-2 rounded-full" style={{ width: `${xgbProb}%` }} />
              </div>
              <p className="text-[11px] text-warm-muted leading-tight">
                Optimizes gradient loss over sequential trees for non-linear interactions.
              </p>
            </div>
          </div>
        </div>

        {/* Explainability & Feature Importance (SHAP / LIME) */}
        <div className="grid grid-cols-1 md:grid-cols-12 gap-6">
          <div className="md:col-span-7 bg-white p-6 rounded-3xl border border-warm-border shadow-xs space-y-4">
            <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2">
              <div className="flex items-center space-x-2">
                <Sparkles className="w-5 h-5 text-brand-800" />
                <h3 className="text-sm font-bold text-gray-900">Explainable AI (XAI)</h3>
              </div>
              <div className="flex items-center space-x-1 p-0.5 bg-warm-bg rounded-xl border border-warm-border self-start sm:self-auto">
                <button
                  type="button"
                  onClick={() => setActiveXaiTab('shap')}
                  className={`px-3 py-1 text-xs font-bold rounded-lg transition-all ${
                    activeXaiTab === 'shap'
                      ? 'bg-brand-800 text-white shadow-xs'
                      : 'text-warm-muted hover:text-gray-900'
                  }`}
                >
                  SHAP (Attributions)
                </button>
                <button
                  type="button"
                  onClick={() => setActiveXaiTab('lime')}
                  className={`px-3 py-1 text-xs font-bold rounded-lg transition-all ${
                    activeXaiTab === 'lime'
                      ? 'bg-brand-800 text-white shadow-xs'
                      : 'text-warm-muted hover:text-gray-900'
                  }`}
                >
                  LIME (Local Surrogacy)
                </button>
              </div>
            </div>

            {activeXaiTab === 'shap' ? (
              <>
                <p className="text-xs text-warm-muted">
                  SHAP computes Shapley values from cooperative game theory on the trained XGBoost estimator, quantifying how each biomarker pushes your risk assessment toward or away from high risk.
                </p>
                <div className="pt-2">
                  <ShapBarChart features={shapData} />
                </div>
              </>
            ) : (
              <>
                <div className="flex items-center justify-between text-xs text-warm-muted">
                  <p>
                    LIME builds an interpretable local linear surrogate model around your clinical inputs to reveal decision boundary influences on the ensemble.
                  </p>
                  {limeMetrics && (
                    <span className="text-[11px] font-bold text-emerald-700 bg-emerald-50 px-2 py-0.5 rounded-md border border-emerald-200 shrink-0 ml-2">
                      Surrogate Fit: {limeMetrics.accuracy}%
                    </span>
                  )}
                </div>
                <div className="pt-2">
                  <ShapBarChart features={limeData.length > 0 ? limeData : shapData} />
                </div>
              </>
            )}
          </div>

          {/* Actionable Clinical Recommendations */}
          <div className="md:col-span-5 bg-white p-6 rounded-3xl border border-warm-border shadow-xs space-y-4 flex flex-col justify-between">
            <div className="space-y-4">
              <div className="flex items-center space-x-2">
                <ShieldCheck className="w-5 h-5 text-emerald-600" />
                <h3 className="text-sm font-bold text-gray-900">Evidence-Based Guidance</h3>
              </div>

              <div className="space-y-3">
                <div className="p-3 bg-warm-bg rounded-xl border border-warm-border/60">
                  <h4 className="text-xs font-bold text-gray-900">1. Blood Pressure Management</h4>
                  <p className="text-[11px] text-gray-600 mt-1">
                    Maintain systolic &lt; 120 mmHg and diastolic &lt; 80 mmHg. Consider the DASH diet (rich in fruits, vegetables, low-fat dairy, reduced sodium).
                  </p>
                </div>

                <div className="p-3 bg-warm-bg rounded-xl border border-warm-border/60">
                  <h4 className="text-xs font-bold text-gray-900">2. Physical Activity</h4>
                  <p className="text-[11px] text-gray-600 mt-1">
                    Target 150 minutes of moderate aerobic exercise (brisk walking, cycling) per week as recommended by the American Heart Association.
                  </p>
                </div>

                <div className="p-3 bg-warm-bg rounded-xl border border-warm-border/60">
                  <h4 className="text-xs font-bold text-gray-900">3. Sleep & Stress Hygiene</h4>
                  <p className="text-[11px] text-gray-600 mt-1">
                    Aim for 7–8 hours of restorative sleep. Chronic stress elevates cortisol and sympathetic vascular resistance.
                  </p>
                </div>
              </div>
            </div>

            <div className="pt-4 border-t border-warm-border flex flex-col sm:flex-row gap-2">
              <Link
                to="/patient/assessment"
                className="flex-1 py-2.5 rounded-full text-center text-xs font-bold text-gray-700 bg-warm-bg hover:bg-warm-border transition-all"
              >
                Re-assess Vitals
              </Link>
              <Link
                to={`/patient/report/${prediction.id}`}
                className="flex-1 py-2.5 rounded-full text-center text-xs font-bold text-white bg-brand-800 hover:bg-brand-900 transition-all shadow-md shadow-brand-900/20"
              >
                Download PDF
              </Link>
            </div>
          </div>
        </div>
      </main>
    </div>
  );
}
