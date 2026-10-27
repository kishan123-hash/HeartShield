import React, { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import {
  Clock,
  Activity,
  FileText,
  Search,
  Filter,
  ArrowRight,
  TrendingUp,
  AlertCircle,
  CheckCircle2,
  Calendar,
  ChevronRight,
  Layers
} from 'lucide-react';
import Sidebar from '../components/Sidebar';
import api from '../api/client';

export default function PredictionHistoryPage() {
  const [predictions, setPredictions] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [searchTerm, setSearchTerm] = useState('');
  const [filterRisk, setFilterRisk] = useState('ALL');

  useEffect(() => {
    const fetchHistory = async () => {
      setLoading(true);
      setError('');
      try {
        const res = await api.get('/predictions?limit=50');
        setPredictions(res.data?.predictions || []);
      } catch (err) {
        console.error('Error fetching prediction history:', err);
        setError('Failed to load past assessment records.');
      } finally {
        setLoading(false);
      }
    };

    fetchHistory();
  }, []);

  const filteredPredictions = predictions.filter((p) => {
    const risk = (p.risk_level || '').toUpperCase();
    if (filterRisk !== 'ALL' && !risk.includes(filterRisk)) {
      return false;
    }
    if (searchTerm) {
      const dateStr = new Date(p.created_at).toLocaleDateString().toLowerCase();
      const label = (p.prediction_label || '').toLowerCase();
      return dateStr.includes(searchTerm.toLowerCase()) || label.includes(searchTerm.toLowerCase());
    }
    return true;
  });

  return (
    <div className="min-h-screen flex flex-col lg:flex-row bg-warm-bg w-full min-w-0 overflow-x-hidden">
      <Sidebar />

      <main className="flex-1 p-4 sm:p-6 lg:p-10 max-w-6xl w-full mx-auto space-y-8 min-w-0">
        {/* Header */}
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
          <div>
            <span className="text-[11px] font-bold uppercase tracking-wider text-brand-800 bg-brand-50 px-2.5 py-0.5 rounded-full border border-brand-200">
              Longitudinal Tracking
            </span>
            <h1 className="text-2xl font-black text-gray-900 tracking-tight mt-1">
              Prediction History
            </h1>
            <p className="text-xs text-warm-muted mt-1">
              Review your historical cardiovascular risk assessments and model consensus logs.
            </p>
          </div>

          <Link
            to="/patient/assessment"
            className="inline-flex items-center space-x-2 px-5 py-2.5 rounded-full text-xs font-bold text-white bg-brand-800 hover:bg-brand-900 transition-all shadow-md shadow-brand-900/20 shrink-0"
          >
            <Activity className="w-4 h-4" />
            <span>New Assessment</span>
          </Link>
        </div>

        {/* Filter and Search Bar */}
        <div className="bg-white p-4 rounded-2xl border border-warm-border shadow-xs flex flex-col sm:flex-row items-center justify-between gap-4">
          <div className="relative w-full sm:w-80">
            <Search className="w-4 h-4 text-warm-muted absolute left-3.5 top-1/2 -translate-y-1/2" />
            <input
              type="text"
              placeholder="Search by date or result..."
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
              className="w-full pl-10 pr-4 py-2 bg-warm-bg border border-warm-border rounded-xl text-xs text-gray-900 focus:outline-none focus:border-brand-800 transition-all"
            />
          </div>

          <div className="flex items-center space-x-2 w-full sm:w-auto">
            <Filter className="w-4 h-4 text-warm-muted shrink-0" />
            <span className="text-xs text-warm-muted font-semibold shrink-0">Filter:</span>
            <div className="flex space-x-1.5 overflow-x-auto">
              {['ALL', 'HIGH', 'MEDIUM', 'LOW'].map((lvl) => (
                <button
                  key={lvl}
                  onClick={() => setFilterRisk(lvl)}
                  className={`px-3 py-1.5 rounded-lg text-xs font-bold transition-all ${
                    filterRisk === lvl
                      ? 'bg-brand-800 text-white shadow-xs'
                      : 'bg-warm-bg text-warm-muted hover:text-gray-900 border border-warm-border'
                  }`}
                >
                  {lvl === 'ALL' ? 'All Risks' : lvl === 'MEDIUM' ? 'Moderate' : lvl.charAt(0) + lvl.slice(1).toLowerCase()}
                </button>
              ))}
            </div>
          </div>
        </div>

        {/* Historical Records Table */}
        <div className="bg-white rounded-3xl border border-warm-border shadow-xs overflow-hidden">
          {loading ? (
            <div className="p-12 flex flex-col items-center justify-center text-center">
              <div className="w-8 h-8 border-3 border-brand-800 border-t-transparent rounded-full animate-spin mb-3" />
              <p className="text-xs font-semibold text-warm-muted">Loading historical assessments...</p>
            </div>
          ) : error ? (
            <div className="p-12 text-center text-red-600 space-y-2">
              <AlertCircle className="w-8 h-8 mx-auto" />
              <p className="text-xs font-bold">{error}</p>
            </div>
          ) : filteredPredictions.length === 0 ? (
            <div className="p-12 text-center space-y-4">
              <div className="w-14 h-14 bg-rose-50 text-brand-800 rounded-full flex items-center justify-center mx-auto">
                <Clock className="w-7 h-7" />
              </div>
              <div>
                <h3 className="text-base font-bold text-gray-900">No Assessment Records Found</h3>
                <p className="text-xs text-warm-muted max-w-sm mx-auto mt-1">
                  You haven't completed any cardiovascular assessments matching these filters yet.
                </p>
              </div>
              <Link
                to="/patient/assessment"
                className="inline-flex items-center space-x-2 px-6 py-2.5 rounded-full text-xs font-bold text-white bg-brand-800 hover:bg-brand-900 shadow-md shadow-brand-900/20"
              >
                <span>Take First Assessment</span>
                <ArrowRight className="w-4 h-4" />
              </Link>
            </div>
          ) : (
            <div className="overflow-x-auto">
              <table className="w-full text-left text-xs">
                <thead className="bg-warm-bg text-warm-muted uppercase tracking-wider text-[10px] font-bold border-b border-warm-border">
                  <tr>
                    <th className="py-4 px-6">Assessment Date</th>
                    <th className="py-4 px-6">Ensemble Risk</th>
                    <th className="py-4 px-6">Status / Label</th>
                    <th className="py-4 px-6">Ensemble Votes</th>
                    <th className="py-4 px-6">Model</th>
                    <th className="py-4 px-6 text-right">Actions</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-warm-border">
                  {filteredPredictions.map((pred) => {
                    const prob = Math.round(Number(pred.ensemble_probability || 0) * 100);
                    const risk = pred.risk_level || 'Moderate';
                    const isHigh = risk.toUpperCase().includes('HIGH');
                    const isMod = risk.toUpperCase().includes('MOD') || risk.toUpperCase().includes('MED');

                    const lrProb = Math.round(Number(pred.logistic_probability || 0) * 100);
                    const rfProb = Math.round(Number(pred.random_forest_probability || 0) * 100);
                    const xgbProb = Math.round(Number(pred.xgboost_probability || 0) * 100);

                    return (
                      <tr key={pred.id} className="hover:bg-rose-50/30 transition-colors">
                        <td className="py-4 px-6 font-semibold text-gray-900">
                          <div className="flex items-center space-x-2">
                            <Calendar className="w-4 h-4 text-warm-muted" />
                            <span>{new Date(pred.created_at).toLocaleDateString()}</span>
                            <span className="text-[10px] text-warm-muted">
                              {new Date(pred.created_at).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
                            </span>
                          </div>
                        </td>

                        <td className="py-4 px-6">
                          <div className="flex items-center space-x-2">
                            <span className="text-base font-black text-brand-800">{prob}%</span>
                            <div className="w-16 bg-warm-bg h-1.5 rounded-full overflow-hidden">
                              <div
                                className={`h-1.5 rounded-full ${
                                  isHigh ? 'bg-red-500' : isMod ? 'bg-amber-500' : 'bg-emerald-500'
                                }`}
                                style={{ width: `${prob}%` }}
                              />
                            </div>
                          </div>
                        </td>

                        <td className="py-4 px-6">
                          <span
                            className={`px-2.5 py-1 rounded-full text-[10px] font-bold uppercase tracking-wider border ${
                              isHigh
                                ? 'bg-red-50 text-red-700 border-red-200'
                                : isMod
                                ? 'bg-amber-50 text-amber-700 border-amber-200'
                                : 'bg-emerald-50 text-emerald-700 border-emerald-200'
                            }`}
                          >
                            {pred.prediction_label || `${risk} Risk`}
                          </span>
                        </td>

                        <td className="py-4 px-6">
                          <div className="flex items-center space-x-1.5 font-mono text-[11px] text-gray-700">
                            <span title={`Logistic Regression: ${lrProb}%`} className="px-1.5 py-0.5 rounded bg-warm-bg border border-warm-border">
                              LR:{lrProb}%
                            </span>
                            <span title={`Random Forest: ${rfProb}%`} className="px-1.5 py-0.5 rounded bg-warm-bg border border-warm-border">
                              RF:{rfProb}%
                            </span>
                            <span title={`XGBoost: ${xgbProb}%`} className="px-1.5 py-0.5 rounded bg-warm-bg border border-warm-border">
                              XGB:{xgbProb}%
                            </span>
                          </div>
                        </td>

                        <td className="py-4 px-6 font-mono text-warm-muted text-[11px]">
                          v{pred.model_version || '2.0'}
                        </td>

                        <td className="py-4 px-6 text-right">
                          <div className="flex items-center justify-end space-x-2">
                            <Link
                              to={`/patient/prediction-result/${pred.id}`}
                              className="px-3 py-1.5 rounded-lg text-xs font-bold text-brand-800 bg-brand-50 hover:bg-brand-100 transition-all border border-brand-200"
                            >
                              Outcome
                            </Link>
                            <Link
                              to={`/patient/report/${pred.id}`}
                              className="p-1.5 rounded-lg text-gray-600 hover:text-brand-800 hover:bg-warm-bg transition-all"
                              title="Medical Report"
                            >
                              <FileText className="w-4 h-4" />
                            </Link>
                          </div>
                        </td>
                      </tr>
                    );
                  })}
                </tbody>
              </table>
            </div>
          )}
        </div>
      </main>
    </div>
  );
}
