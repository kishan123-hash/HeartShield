import React, { useState, useEffect } from 'react';
import { useParams, Link, useNavigate } from 'react-router-dom';
import {
  Shield,
  Heart,
  Printer,
  ArrowLeft,
  Download,
  CheckCircle2,
  AlertCircle,
  Clock,
  User,
  Activity,
  FileCheck,
  Bot
} from 'lucide-react';
import api from '../api/client';
import { useAuth } from '../context/AuthContext';

export default function PatientReportPage() {
  const { id } = useParams();
  const navigate = useNavigate();
  const { user } = useAuth();

  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [prediction, setPrediction] = useState(null);
  const [assessment, setAssessment] = useState(null);
  const [report, setReport] = useState(null);

  useEffect(() => {
    const fetchReportData = async () => {
      setLoading(true);
      setError('');
      try {
        // 1. Get prediction details
        const predRes = await api.get(`/predictions/${id}`);
        setPrediction(predRes.data);

        // 2. Get associated assessment if available
        if (predRes.data?.assessment_id) {
          try {
            const assessRes = await api.get(`/assessments/${predRes.data.assessment_id}`);
            setAssessment(assessRes.data);
          } catch (aErr) {
            console.warn('Assessment detail not fetched:', aErr);
          }
        }

        // 3. Check for existing generated report
        try {
          const repRes = await api.get(`/reports?limit=10`);
          const matched = repRes.data?.reports?.find((r) => r.prediction_id === Number(id));
          if (matched) {
            const detailRes = await api.get(`/reports/${matched.id}`);
            setReport(detailRes.data);
          }
        } catch (rErr) {
          console.warn('Report detail check:', rErr);
        }
      } catch (err) {
        console.error('Error fetching report:', err);
        setError('Failed to load clinical report data.');
      } finally {
        setLoading(false);
      }
    };

    if (id) {
      fetchReportData();
    }
  }, [id]);

  const handlePrint = () => {
    window.print();
  };

  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-warm-bg">
        <div className="w-10 h-10 border-4 border-brand-800 border-t-transparent rounded-full animate-spin mb-4" />
      </div>
    );
  }

  if (error || !prediction) {
    return (
      <div className="min-h-screen flex flex-col items-center justify-center bg-warm-bg p-6 text-center">
        <AlertCircle className="w-12 h-12 text-red-600 mb-4" />
        <h2 className="text-xl font-bold text-gray-900 mb-2">Report Unavailable</h2>
        <p className="text-xs text-warm-muted max-w-sm mb-6">{error || 'Could not find clinical report.'}</p>
        <button
          onClick={() => navigate(-1)}
          className="px-6 py-2.5 rounded-full bg-brand-800 text-white font-bold text-xs"
        >
          Go Back
        </button>
      </div>
    );
  }

  const probPercent = Math.round(Number(prediction.ensemble_probability || 0) * 100);
  const riskLevel = prediction.risk_level || 'Moderate';
  const isHighRisk = riskLevel.toUpperCase().includes('HIGH');

  return (
    <div className="min-h-screen bg-warm-bg py-8 px-4 sm:px-6">
      {/* Top Action Bar (Hidden when printing) */}
      <div className="max-w-4xl mx-auto mb-6 flex flex-wrap items-center justify-between gap-3 print:hidden">
        <button
          onClick={() => navigate(-1)}
          className="inline-flex items-center space-x-2 text-xs font-bold text-gray-700 bg-white px-4 py-2 rounded-full border border-warm-border hover:bg-rose-50 transition-all shadow-xs"
        >
          <ArrowLeft className="w-4 h-4" />
          <span>Back</span>
        </button>

        <div className="flex flex-wrap items-center gap-2 sm:gap-3">
          <Link
            to="/patient/chat"
            className="inline-flex items-center space-x-2 text-xs font-bold text-brand-800 bg-brand-50 px-4 py-2 rounded-full border border-brand-200 hover:bg-brand-100 transition-all"
          >
            <Bot className="w-4 h-4" />
            <span>Ask AI Health Assistant</span>
          </Link>
          <button
            onClick={handlePrint}
            className="inline-flex items-center space-x-2 text-xs font-bold text-white bg-brand-800 px-5 py-2.5 rounded-full hover:bg-brand-900 transition-all shadow-md shadow-brand-900/20"
          >
            <Printer className="w-4 h-4" />
            <span>Print / Save as PDF</span>
          </button>
        </div>
      </div>

      {/* Main Printable Document Card */}
      <div className="max-w-4xl mx-auto bg-white border border-warm-border rounded-3xl p-8 sm:p-12 shadow-sm print:shadow-none print:border-none print:p-0 print:m-0">
        {/* Header */}
        <div className="border-b-2 border-brand-800 pb-6 flex flex-col sm:flex-row sm:items-center justify-between gap-4">
         <div className="flex items-center space-x-3">
  <img
    src="/heartshield-logo.png"
    alt="HeartShield Logo"
    className="w-20 h-20 object-contain"
  />
  </div>

          <div className="text-left sm:text-right space-y-1">
            <span className="text-xs font-bold uppercase tracking-wider text-brand-800 bg-brand-50 px-2.5 py-0.5 rounded-full border border-brand-200">
              Official Assessment Record
            </span>
            <p className="text-xs text-warm-muted">
              Report ID: <span className="font-mono font-semibold text-gray-800">HS-REP-{prediction.id.toString().padStart(6, '0')}</span>
            </p>
            <p className="text-xs text-warm-muted">
              Generated: <span className="font-semibold text-gray-800">{new Date(prediction.created_at).toLocaleDateString()}</span>
            </p>
          </div>
        </div>

        {/* Patient Demographics */}
        <div className="my-8 bg-warm-bg p-5 rounded-2xl border border-warm-border/80 grid grid-cols-2 sm:grid-cols-4 gap-4">
          <div>
            <span className="text-[10px] font-bold text-warm-muted uppercase tracking-wider">Patient Name</span>
            <p className="text-xs font-bold text-gray-900 mt-0.5">
              {user?.full_name || user?.username || 'Authenticated Patient'}
            </p>
          </div>
          <div>
            <span className="text-[10px] font-bold text-warm-muted uppercase tracking-wider">User Reference ID</span>
            <p className="text-xs font-mono font-bold text-gray-900 mt-0.5">USR-{user?.id || '001'}</p>
          </div>
          <div>
            <span className="text-[10px] font-bold text-warm-muted uppercase tracking-wider">Assessment Status</span>
            <div className="flex items-center space-x-1 mt-0.5">
              <CheckCircle2 className="w-3.5 h-3.5 text-emerald-600" />
              <span className="text-xs font-bold text-emerald-700">Validated</span>
            </div>
          </div>
          <div>
            <span className="text-[10px] font-bold text-warm-muted uppercase tracking-wider">Evaluation Engine</span>
            <p className="text-xs font-bold text-brand-800 mt-0.5">Hard-Voting v2.0</p>
          </div>
        </div>

        {/* Executive Clinical Assessment Result */}
        <div className="mb-8 p-6 rounded-2xl border border-warm-border bg-gradient-to-r from-rose-50/50 to-white">
          <span className="text-[10px] font-bold uppercase tracking-wider text-brand-800">
            Diagnostic Consensus
          </span>
          <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 mt-2">
            <div>
              <h3 className="text-xl font-black text-gray-900">{prediction.prediction_label}</h3>
              <p className="text-xs text-gray-600 mt-1 max-w-xl">
                Synthesized from 3 heterogeneous classifiers (Logistic Regression, Random Forest, XGBoost) using majority consensus voting rules.
              </p>
            </div>
            <div className="flex flex-col items-center justify-center p-3 rounded-xl bg-white border border-warm-border min-w-[120px]">
              <span className="text-2xl font-black text-brand-800">{probPercent}%</span>
              <span className="text-[10px] font-bold text-warm-muted uppercase tracking-wider">Calculated Risk</span>
            </div>
          </div>
        </div>

        {/* Model Voting Sub-table */}
        <div className="mb-8">
          <h4 className="text-xs font-bold uppercase tracking-wider text-gray-800 mb-3">
            Ensemble Model Voting Breakdown
          </h4>
          <div className="overflow-x-auto">
            <table className="w-full text-left text-xs border border-warm-border rounded-xl overflow-hidden">
              <thead className="bg-warm-bg text-warm-muted uppercase tracking-wider text-[10px] font-bold border-b border-warm-border">
                <tr>
                  <th className="p-3">Classifier Architecture</th>
                  <th className="p-3">Class Vote</th>
                  <th className="p-3">Confidence Score</th>
                  <th className="p-3">Methodology</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-warm-border">
                <tr>
                  <td className="p-3 font-semibold text-gray-900">Logistic Regression</td>
                  <td className="p-3">
                    <span className="font-bold text-gray-800">
                      {Number(prediction.logistic_probability || 0) >= 0.5 ? 'Positive (Class 1)' : 'Negative (Class 0)'}
                    </span>
                  </td>
                  <td className="p-3 font-mono font-bold text-brand-800">
                    {Math.round(Number(prediction.logistic_probability || 0) * 100)}%
                  </td>
                  <td className="p-3 text-warm-muted text-[11px]">Regularized Linear Estimator</td>
                </tr>
                <tr>
                  <td className="p-3 font-semibold text-gray-900">Random Forest Classifier</td>
                  <td className="p-3">
                    <span className="font-bold text-gray-800">
                      {Number(prediction.random_forest_probability || 0) >= 0.5 ? 'Positive (Class 1)' : 'Negative (Class 0)'}
                    </span>
                  </td>
                  <td className="p-3 font-mono font-bold text-brand-800">
                    {Math.round(Number(prediction.random_forest_probability || 0) * 100)}%
                  </td>
                  <td className="p-3 text-warm-muted text-[11px]">Bagged Decision Ensemble</td>
                </tr>
                <tr>
                  <td className="p-3 font-semibold text-gray-900">XGBoost Classifier</td>
                  <td className="p-3">
                    <span className="font-bold text-gray-800">
                      {Number(prediction.xgboost_probability || 0) >= 0.5 ? 'Positive (Class 1)' : 'Negative (Class 0)'}
                    </span>
                  </td>
                  <td className="p-3 font-mono font-bold text-brand-800">
                    {Math.round(Number(prediction.xgboost_probability || 0) * 100)}%
                  </td>
                  <td className="p-3 text-warm-muted text-[11px]">Gradient Boosted Decision Trees</td>
                </tr>
              </tbody>
            </table>
          </div>
        </div>

        {/* Clinical Parameters & Lifestyle Grid */}
        {assessment && (
          <div className="mb-8 space-y-4">
            <h4 className="text-xs font-bold uppercase tracking-wider text-gray-800">
              Recorded Biomarkers & Lifestyle Metrics
            </h4>
            <div className="grid grid-cols-2 sm:grid-cols-4 gap-3 text-xs">
              <div className="p-3 bg-warm-bg rounded-xl border border-warm-border">
                <span className="text-[10px] text-warm-muted uppercase block">Blood Pressure</span>
                <span className="font-bold text-gray-900">
                  {assessment.systolic_bp} / {assessment.diastolic_bp} mmHg
                </span>
              </div>
              <div className="p-3 bg-warm-bg rounded-xl border border-warm-border">
                <span className="text-[10px] text-warm-muted uppercase block">Heart Rate</span>
                <span className="font-bold text-gray-900">{assessment.heart_rate} bpm</span>
              </div>
              <div className="p-3 bg-warm-bg rounded-xl border border-warm-border">
                <span className="text-[10px] text-warm-muted uppercase block">Body Mass Index</span>
                <span className="font-bold text-gray-900">{assessment.bmi} kg/m²</span>
              </div>
              <div className="p-3 bg-warm-bg rounded-xl border border-warm-border">
                <span className="text-[10px] text-warm-muted uppercase block">Total Cholesterol</span>
                <span className="font-bold text-gray-900">{assessment.total_cholesterol} mg/dL</span>
              </div>
              <div className="p-3 bg-warm-bg rounded-xl border border-warm-border">
                <span className="text-[10px] text-warm-muted uppercase block">HDL / LDL</span>
                <span className="font-bold text-gray-900">{assessment.hdl} / {assessment.ldl} mg/dL</span>
              </div>
              <div className="p-3 bg-warm-bg rounded-xl border border-warm-border">
                <span className="text-[10px] text-warm-muted uppercase block">Blood Glucose</span>
                <span className="font-bold text-gray-900">{assessment.blood_glucose} mg/dL</span>
              </div>
              <div className="p-3 bg-warm-bg rounded-xl border border-warm-border">
                <span className="text-[10px] text-warm-muted uppercase block">Physical Activity</span>
                <span className="font-bold text-gray-900">{assessment.physical_activity || 'Moderate'}</span>
              </div>
              <div className="p-3 bg-warm-bg rounded-xl border border-warm-border">
                <span className="text-[10px] text-warm-muted uppercase block">Smoking Status</span>
                <span className="font-bold text-gray-900">{assessment.smoking || 'Never'}</span>
              </div>
            </div>
          </div>
        )}

        {/* Clinical Recommendations */}
        <div className="mb-8 p-5 bg-warm-bg rounded-2xl border border-warm-border space-y-3">
          <h4 className="text-xs font-bold uppercase tracking-wider text-brand-800">
            Clinical Recommendations & Action Plan
          </h4>
          <ul className="text-xs text-gray-700 space-y-2 list-disc list-inside">
            <li>
              <strong>Cardiovascular Screening:</strong> Routine monitoring of ambulatory blood pressure and lipid panels every 6–12 months.
            </li>
            <li>
              <strong>Lifestyle Modification:</strong> Adhere to heart-healthy dietary patterns with balanced sodium intake and rich dietary fiber.
            </li>
            <li>
              <strong>Aerobic Conditioning:</strong> Maintain at least 150 minutes of moderate-intensity physical activity weekly.
            </li>
            <li>
              <strong>Physician Follow-up:</strong> Discuss these AI screening outcomes with a board-certified cardiologist or primary care physician.
            </li>
          </ul>
        </div>

        {/* Doctor Review & Sign-off Area */}
        <div className="border-t border-warm-border pt-6 grid grid-cols-1 sm:grid-cols-2 gap-6 items-end">
          <div className="space-y-1">
            <span className="text-[10px] font-bold text-warm-muted uppercase tracking-wider">Clinical Verification</span>
            <div className="flex items-center space-x-2">
              <FileCheck className="w-4 h-4 text-emerald-600" />
              <span className="text-xs font-bold text-gray-900">
                {report?.is_approved ? 'Verified by Attending Physician' : 'Automated Diagnostic Output'}
              </span>
            </div>
            {report?.doctor_notes && (
              <p className="text-[11px] text-gray-600 italic mt-1">"{report.doctor_notes}"</p>
            )}
            <p className="text-[10px] text-warm-muted mt-2">
              This automated assessment provides evidence-based risk stratification and does not replace in-person medical evaluation.
            </p>
          </div>

          <div className="text-right space-y-3 sm:space-y-6">
            <div className="inline-block border-b-2 border-gray-400 w-48 text-center pb-1">
              <span className="font-mono text-xs text-gray-400">HeartShield AI Ensemble</span>
            </div>
            <p className="text-[10px] text-warm-muted">Authorized Digital Sign-off</p>
          </div>
        </div>
      </div>
    </div>
  );
}
