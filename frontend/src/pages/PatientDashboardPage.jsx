import React, { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import {
  Activity,
  FileText,
  Sparkles,
  TrendingUp,
  AlertCircle,
  PlusCircle,
  ArrowRight,
  CheckCircle2,
  Clock,
  Heart,
  Stethoscope,
  MessageCircle
} from 'lucide-react';
import Sidebar from '../components/Sidebar';
import { useAuth } from '../context/AuthContext';
import api from '../api/client';

export default function PatientDashboardPage() {
  const { user } = useAuth();
  const [latestPrediction, setLatestPrediction] = useState(null);
  const [predictions, setPredictions] = useState([]);
  const [reports, setReports] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const fetchDashboardData = async () => {
      try {
        // Fetch latest prediction
        try {
          const predRes = await api.get('/predictions/latest');
          setLatestPrediction(predRes.data);
        } catch (e) {
          // No predictions yet
          setLatestPrediction(null);
        }

        // Fetch prediction list
        try {
          const listRes = await api.get('/predictions?limit=5');
          setPredictions(listRes.data?.predictions || []);
        } catch (e) {
          setPredictions([]);
        }

        // Fetch uploaded reports
        try {
          const repRes = await api.get('/medical-reports');
          setReports(repRes.data?.reports || []);
        } catch (e) {
          setReports([]);
        }
      } catch (err) {
        console.error("Dashboard data load error:", err);
      } finally {
        setLoading(false);
      }
    };

    fetchDashboardData();
  }, []);

  const getRiskBadge = (level) => {
    const l = String(level || 'LOW').toUpperCase();
    if (l.includes('HIGH')) {
      return <span className="px-2.5 py-1 rounded-full text-xs font-bold bg-red-100 text-red-700 border border-red-200">High Risk</span>;
    }
    if (l.includes('MOD') || l.includes('MED')) {
      return <span className="px-2.5 py-1 rounded-full text-xs font-bold bg-amber-100 text-amber-700 border border-amber-200">Moderate Risk</span>;
    }
    return <span className="px-2.5 py-1 rounded-full text-xs font-bold bg-emerald-100 text-emerald-700 border border-emerald-200">Low Risk</span>;
  };

  return (
    <div className="min-h-screen flex flex-col lg:flex-row bg-warm-bg w-full min-w-0 overflow-x-hidden">
      <Sidebar />

      <main className="flex-1 p-4 sm:p-6 lg:p-10 max-w-7xl w-full mx-auto space-y-8 min-w-0">
        {/* Welcome Greeting Banner (Screen 11) */}
        <div className="bg-white rounded-3xl p-6 sm:p-8 border border-warm-border shadow-xs flex flex-col sm:flex-row items-start sm:items-center justify-between gap-6">
          <div className="space-y-1.5">
            <h1 className="text-2xl sm:text-3xl font-black text-gray-900 tracking-tight">
              Welcome, {user?.full_name || 'Patient'}!
            </h1>
            <p className="text-xs sm:text-sm text-warm-muted">
              Take control of your heart health with explainable AI-powered insights.
            </p>
          </div>

          <div className="flex flex-wrap items-center gap-3 shrink-0">
            <Link
              to="/patient/doctors"
              className="inline-flex items-center space-x-2 px-5 py-3 rounded-full bg-rose-50 text-brand-800 font-bold text-xs hover:bg-rose-100 border border-brand-200 transition-all shrink-0"
            >
              <Stethoscope className="w-4 h-4" />
              <span>Consult Cardiologist</span>
            </Link>

            <Link
              to="/patient/assessment"
              className="inline-flex items-center space-x-2 px-6 py-3 rounded-full bg-brand-800 text-white font-bold text-sm hover:bg-brand-900 shadow-md shadow-brand-900/20 transition-all shrink-0"
            >
              <PlusCircle className="w-4 h-4" />
              <span>Start New Assessment</span>
            </Link>
          </div>
        </div>

        {/* 3 Metric Cards */}
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
          {/* Card 1: Last Check */}
          <div className="bg-white p-6 rounded-2xl border border-warm-border shadow-xs flex items-center justify-between">
            <div>
              <span className="text-[11px] font-bold text-warm-muted uppercase tracking-wider">Last Check</span>
              <p className="text-base font-bold text-gray-900 mt-1">
                {latestPrediction?.created_at
                  ? new Date(latestPrediction.created_at).toLocaleDateString('en-GB', { day: 'numeric', month: 'short', year: 'numeric' })
                  : 'No checks yet'}
              </p>
              <div className="mt-2">
                {latestPrediction ? getRiskBadge(latestPrediction.risk_level) : <span className="text-xs text-warm-muted italic">Pending assessment</span>}
              </div>
            </div>
            <div className="w-12 h-12 rounded-xl bg-rose-50 text-brand-800 flex items-center justify-center">
              <Activity className="w-6 h-6" />
            </div>
          </div>

          {/* Card 2: Reports */}
          <div className="bg-white p-6 rounded-2xl border border-warm-border shadow-xs flex items-center justify-between">
            <div>
              <span className="text-[11px] font-bold text-warm-muted uppercase tracking-wider">Uploaded Reports</span>
              <p className="text-2xl font-black text-gray-900 mt-1">{reports.length}</p>
              <Link to="/patient/medical-reports" className="text-xs font-semibold text-brand-800 hover:underline mt-2 inline-block">
                Manage Documents →
              </Link>
            </div>
            <div className="w-12 h-12 rounded-xl bg-rose-50 text-brand-800 flex items-center justify-center">
              <FileText className="w-6 h-6" />
            </div>
          </div>

          {/* Card 3: Next Step */}
          <div className="bg-white p-6 rounded-2xl border border-warm-border shadow-xs flex items-center justify-between">
            <div>
              <span className="text-[11px] font-bold text-warm-muted uppercase tracking-wider">Next Step</span>
              <p className="text-base font-bold text-gray-900 mt-1">
                {latestPrediction ? 'Maintain Active Habits' : 'Take First Assessment'}
              </p>
              <span className="text-xs text-emerald-700 font-semibold block mt-1">
                {latestPrediction ? 'AHA Guideline Alignment' : 'Estimate Risk Score'}
              </span>
            </div>
            <div className="w-12 h-12 rounded-xl bg-emerald-50 text-emerald-700 flex items-center justify-center">
              <Heart className="w-6 h-6" />
            </div>
          </div>
        </div>

        {/* Middle Section: Risk Trend & Recent Reports */}
        <div className="grid grid-cols-1 lg:grid-cols-12 gap-8">
          {/* Risk Trend Chart (Screen 11 left) */}
          <div className="lg:col-span-7 bg-white p-6 sm:p-7 rounded-3xl border border-warm-border shadow-xs space-y-4">
            <div className="flex items-center justify-between">
              <div>
                <h3 className="text-base font-bold text-gray-900 tracking-tight">Risk Trend</h3>
                <p className="text-xs text-warm-muted">Historical probability progression</p>
              </div>
              <TrendingUp className="w-5 h-5 text-brand-800" />
            </div>

            {predictions.length > 0 ? (
              <div className="pt-4">
                {/* Visual SVG Trend line */}
                <div className="h-44 w-full flex items-end justify-between gap-4 pt-4 px-2 border-b border-warm-border">
                  {predictions.slice(0, 6).reverse().map((p, idx) => {
                    const prob = Math.round(Number(p.ensemble_probability) * 100);
                    const heightPercent = Math.max(prob, 15);
                    return (
                      <div key={idx} className="flex-1 flex flex-col items-center gap-2 group">
                        <span className="text-[10px] font-bold text-brand-900 opacity-0 group-hover:opacity-100 transition-opacity">
                          {prob}%
                        </span>
                        <div
                          className="w-full max-w-[36px] bg-gradient-to-t from-brand-800 to-rose-400 rounded-t-lg transition-all group-hover:brightness-110"
                          style={{ height: `${heightPercent}%` }}
                        />
                        <span className="text-[10px] text-warm-muted truncate w-full text-center">
                          {new Date(p.created_at).toLocaleDateString('en-GB', { day: 'numeric', month: 'short' })}
                        </span>
                      </div>
                    );
                  })}
                </div>
              </div>
            ) : (
              <div className="h-44 flex flex-col items-center justify-center text-center p-6 bg-warm-bg/40 rounded-2xl border border-dashed border-warm-border">
                <AlertCircle className="w-8 h-8 text-warm-muted mb-2" />
                <p className="text-xs text-warm-muted">No assessment data recorded yet.</p>
                <Link to="/patient/assessment" className="text-xs font-bold text-brand-800 hover:underline mt-2">
                  Complete your first clinical assessment →
                </Link>
              </div>
            )}
          </div>

          {/* Quick Tips (Screen 11 right) */}
          <div className="lg:col-span-5 bg-white p-6 sm:p-7 rounded-3xl border border-warm-border shadow-xs space-y-4">
            <h3 className="text-base font-bold text-gray-900 tracking-tight">Quick Health Tips</h3>
            <div className="space-y-3">
              {[
                { title: 'Maintain healthy diet', desc: 'Emphasize fruits, vegetables, whole grains, and lean fish.' },
                { title: 'Regular aerobic exercise', desc: 'Aim for 150 minutes of moderate aerobic activity weekly.' },
                { title: 'Avoid tobacco & smoke', desc: 'Cigarette smoking elevates coronary artery disease risk.' },
                { title: 'Manage stress levels', desc: 'Practice mindfulness, meditation, and ensure 7-9 hours sleep.' }
              ].map((tip, idx) => (
                <div key={idx} className="flex items-start space-x-3 p-3 rounded-xl bg-warm-bg/50 border border-warm-border/50">
                  <CheckCircle2 className="w-4 h-4 text-emerald-600 shrink-0 mt-0.5" />
                  <div>
                    <h4 className="text-xs font-bold text-gray-900">{tip.title}</h4>
                    <p className="text-[11px] text-warm-muted mt-0.5 leading-relaxed">{tip.desc}</p>
                  </div>
                </div>
              ))}
            </div>
          </div>
        </div>

        {/* Recent Reports Table (Screen 11 Bottom) */}
        <div className="bg-white p-6 sm:p-8 rounded-3xl border border-warm-border shadow-xs space-y-4">
          <div className="flex items-center justify-between">
            <h3 className="text-base font-bold text-gray-900 tracking-tight">Recent Assessments & Reports</h3>
            <Link to="/patient/history" className="text-xs font-bold text-brand-800 hover:underline">
              View All History →
            </Link>
          </div>

          {predictions.length > 0 ? (
            <div className="overflow-x-auto">
              <table className="w-full text-left text-xs">
                <thead>
                  <tr className="border-b border-warm-border text-warm-muted uppercase tracking-wider">
                    <th className="py-3 px-4 font-bold">Assessment Date</th>
                    <th className="py-3 px-4 font-bold">Risk Level</th>
                    <th className="py-3 px-4 font-bold">Probability</th>
                    <th className="py-3 px-4 font-bold">Model Version</th>
                    <th className="py-3 px-4 font-bold text-right">Action</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-warm-border/50">
                  {predictions.map((p) => (
                    <tr key={p.id} className="hover:bg-warm-bg/40 transition-colors">
                      <td className="py-3.5 px-4 font-semibold text-gray-900">
                        {new Date(p.created_at).toLocaleDateString('en-GB', { day: 'numeric', month: 'short', year: 'numeric' })}
                      </td>
                      <td className="py-3.5 px-4">{getRiskBadge(p.risk_level)}</td>
                      <td className="py-3.5 px-4 font-bold text-gray-900">
                        {Math.round(Number(p.ensemble_probability) * 100)}%
                      </td>
                      <td className="py-3.5 px-4 text-warm-muted">{p.model_version || '1.0.0'}</td>
                      <td className="py-3.5 px-4 text-right">
                        <Link
                          to={`/patient/prediction-result/${p.id}`}
                          className="inline-flex items-center space-x-1 px-3 py-1.5 rounded-lg bg-brand-50 text-brand-800 hover:bg-brand-100 font-bold text-xs"
                        >
                          <span>View Result</span>
                          <ArrowRight className="w-3.5 h-3.5" />
                        </Link>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          ) : (
            <div className="text-center py-8 text-xs text-warm-muted">
              No recent assessment records available.
            </div>
          )}
        </div>
      </main>
    </div>
  );
}
