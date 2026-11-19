import React, { useState, useEffect } from 'react';
import { useParams, useNavigate, Link } from 'react-router-dom';
import {
  ArrowLeft,
  Printer,
  FileCheck,
  CheckCircle2,
  Stethoscope,
  Activity,
  Heart,
  Calendar,
  Clock,
  AlertCircle,
  Building,
  User,
  ShieldCheck,
  Award,
  Layers
} from 'lucide-react';
import RiskGauge from '../components/RiskGauge';
import api from '../api/client';

export default function PatientVerifiedReportDetailPage() {
  const { id } = useParams();
  const navigate = useNavigate();

  const [reportData, setReportData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [errorMsg, setErrorMsg] = useState('');

  useEffect(() => {
    const fetchReportDetail = async () => {
      setLoading(true);
      setErrorMsg('');
      try {
        const res = await api.get(`/patients/me/verified-reports/${id}`);
        setReportData(res.data);
      } catch (err) {
        console.error('Error fetching verified report details:', err);
        setErrorMsg('Failed to load verified medical report. You may not have permission to view it.');
      } finally {
        setLoading(false);
      }
    };

    if (id) {
      fetchReportDetail();
    }
  }, [id]);

  const handlePrint = () => {
    window.print();
  };

  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-warm-bg">
        <div className="text-center space-y-3">
          <div className="w-10 h-10 border-4 border-brand-800 border-t-transparent rounded-full animate-spin mx-auto" />
          <p className="text-xs font-semibold text-warm-muted">Loading verified report...</p>
        </div>
      </div>
    );
  }

  if (errorMsg || !reportData) {
    return (
      <div className="min-h-screen flex flex-col items-center justify-center bg-warm-bg p-6 text-center">
        <AlertCircle className="w-12 h-12 text-red-600 mb-4" />
        <h2 className="text-xl font-bold text-gray-900 mb-2">Report Unavailable</h2>
        <p className="text-xs text-warm-muted max-w-sm mb-6">{errorMsg || 'Could not load report details.'}</p>
        <button
          onClick={() => navigate('/patient/verified-reports')}
          className="px-6 py-2.5 rounded-full bg-brand-800 text-white font-bold text-xs shadow-md"
        >
          Return to Verified Reports
        </button>
      </div>
    );
  }

  const {
    report_code,
    verification_status,
    verification_date,
    patient,
    section_1_prediction,
    section_2_verification,
    section_3_recommendations,
  } = reportData;

  const probPercent = section_1_prediction?.risk_percentage ?? 0;
  const riskCategory = section_1_prediction?.risk_category || 'Moderate';
  const biometrics = section_1_prediction?.biometric_markers || {};
  const history = section_1_prediction?.medical_history || {};
  const lifestyle = section_1_prediction?.lifestyle || {};

  const formattedVerDate = verification_date
    ? new Date(verification_date).toLocaleDateString('en-US', {
        month: 'long',
        day: 'numeric',
        year: 'numeric',
      })
    : '—';

  const formattedVerTime = verification_date
    ? new Date(verification_date).toLocaleTimeString('en-US', {
        hour: '2-digit',
        minute: '2-digit',
      })
    : '';

  const formattedPredDate = section_1_prediction?.prediction_date
    ? new Date(section_1_prediction.prediction_date).toLocaleDateString('en-US', {
        month: 'long',
        day: 'numeric',
        year: 'numeric',
      })
    : '—';

  return (
    <div className="min-h-screen bg-warm-bg py-8 px-4 sm:px-6">
      {/* Action Bar (Hidden when printing) */}
      <div className="max-w-4xl mx-auto mb-6 flex flex-wrap items-center justify-between gap-3 print:hidden">
        <button
          onClick={() => navigate('/patient/verified-reports')}
          className="inline-flex items-center space-x-2 text-xs font-bold text-gray-700 bg-white px-4 py-2 rounded-full border border-warm-border hover:bg-rose-50 transition-all shadow-xs"
        >
          <ArrowLeft className="w-4 h-4" />
          <span>Back to Verified Reports</span>
        </button>

        <button
          onClick={handlePrint}
          className="inline-flex items-center space-x-2 text-xs font-bold text-white bg-brand-800 px-5 py-2.5 rounded-full hover:bg-brand-900 transition-all shadow-md shadow-brand-900/20"
        >
          <Printer className="w-4 h-4" />
          <span>Print / Save as PDF</span>
        </button>
      </div>

      {/* Main Printable Document Card */}
      <div className="max-w-4xl mx-auto bg-white border border-warm-border rounded-3xl p-8 sm:p-12 shadow-sm space-y-8 print:shadow-none print:border-none print:p-0 print:m-0">
        {/* Document Header */}
        <div className="border-b-2 border-brand-800 pb-6 flex flex-col sm:flex-row sm:items-center justify-between gap-4">
          <div className="flex items-center space-x-3">
            <img
              src="/heartshield-logo.png"
              alt="HeartShield Logo"
              className="w-16 h-16 object-contain"
            />
            <div>
              <h2 className="text-xl font-black text-gray-900 tracking-tight">HeartShield</h2>
              <p className="text-xs text-warm-muted">Cardiovascular Health Intelligence Platform</p>
            </div>
          </div>

          <div className="text-left sm:text-right space-y-1">
            <span className="text-xs font-bold uppercase tracking-wider text-emerald-800 bg-emerald-50 px-3 py-1 rounded-full border border-emerald-200 inline-flex items-center space-x-1">
              <CheckCircle2 className="w-3.5 h-3.5" />
              <span>Official Physician-Verified Report</span>
            </span>
            <p className="text-xs text-warm-muted mt-1">
              Report ID: <span className="font-mono font-bold text-gray-900">{report_code}</span>
            </p>
            <p className="text-xs text-warm-muted">
              Signed Off: <span className="font-semibold text-gray-800">{formattedVerDate} {formattedVerTime}</span>
            </p>
          </div>
        </div>

        {/* Patient Demographics Banner */}
        <div className="bg-warm-bg p-5 rounded-2xl border border-warm-border grid grid-cols-2 sm:grid-cols-4 gap-4 text-xs">
          <div>
            <span className="text-[10px] font-bold text-warm-muted uppercase tracking-wider block">Patient Name</span>
            <p className="font-bold text-gray-900 mt-0.5">{patient?.full_name || 'Authenticated Patient'}</p>
          </div>
          <div>
            <span className="text-[10px] font-bold text-warm-muted uppercase tracking-wider block">Gender &amp; Blood Group</span>
            <p className="font-bold text-gray-900 mt-0.5 capitalize">
              {patient?.gender || '—'} / {patient?.blood_group || '—'}
            </p>
          </div>
          <div>
            <span className="text-[10px] font-bold text-warm-muted uppercase tracking-wider block">Date of Birth</span>
            <p className="font-bold text-gray-900 mt-0.5">
              {patient?.date_of_birth ? new Date(patient.date_of_birth).toLocaleDateString() : '—'}
            </p>
          </div>
          <div>
            <span className="text-[10px] font-bold text-warm-muted uppercase tracking-wider block">Verification Status</span>
            <div className="flex items-center space-x-1 mt-0.5 text-emerald-700 font-bold">
              <ShieldCheck className="w-3.5 h-3.5" />
              <span>Verified &amp; Signed</span>
            </div>
          </div>
        </div>

        {/* ========================================================= */}
        {/* SECTION 1: ORIGINAL PREDICTION REPORT */}
        {/* ========================================================= */}
        <div className="space-y-4">
          <div className="flex items-center space-x-2 border-b border-warm-border pb-2">
            <span className="text-xs font-bold uppercase tracking-wider text-brand-800 bg-brand-50 px-2.5 py-0.5 rounded-full border border-brand-200">
              Section 1
            </span>
            <h3 className="text-base font-bold text-gray-900">Original AI Risk Prediction &amp; Clinical Vitals</h3>
          </div>

          {/* Risk Summary Highlight */}
          <div className="p-6 rounded-2xl border border-warm-border bg-gradient-to-r from-rose-50/50 to-white flex flex-col sm:flex-row sm:items-center justify-between gap-4">
            <div className="space-y-1">
              <span className="text-[10px] font-bold uppercase tracking-wider text-brand-800">
                Evaluation Consensus
              </span>
              <h4 className="text-lg font-black text-gray-900">
                {section_1_prediction?.prediction_label || `${riskCategory} Risk of Heart Disease`}
              </h4>
              <p className="text-xs text-warm-muted max-w-lg">
                Calculated on {formattedPredDate} using heterogeneous hard-voting ensemble architecture (Logistic Regression + Random Forest + XGBoost).
              </p>
            </div>

            <div className="flex flex-col items-center justify-center p-4 rounded-xl bg-white border border-warm-border min-w-[140px] shadow-2xs">
              <span className="text-3xl font-black text-brand-800">{probPercent}%</span>
              <span className="text-[10px] font-bold text-warm-muted uppercase tracking-wider mt-0.5">
                Calculated Risk
              </span>
              <span className="mt-1 text-[11px] font-bold text-gray-800">{riskCategory} Category</span>
            </div>
          </div>

          {/* Relevant Biometric Markers Grid */}
          <div className="space-y-2">
            <span className="text-[11px] font-bold text-gray-800 uppercase tracking-wider block">
              Recorded Biometric Markers &amp; Clinical Features
            </span>
            <div className="grid grid-cols-2 sm:grid-cols-4 gap-3 text-xs">
              <div className="p-3 bg-warm-bg rounded-xl border border-warm-border">
                <span className="text-[10px] text-warm-muted uppercase block">Blood Pressure</span>
                <span className="font-bold text-gray-900">
                  {biometrics.systolic_bp || 120} / {biometrics.diastolic_bp || 80} mmHg
                </span>
              </div>
              <div className="p-3 bg-warm-bg rounded-xl border border-warm-border">
                <span className="text-[10px] text-warm-muted uppercase block">Heart Rate</span>
                <span className="font-bold text-gray-900">{biometrics.heart_rate || 72} bpm</span>
              </div>
              <div className="p-3 bg-warm-bg rounded-xl border border-warm-border">
                <span className="text-[10px] text-warm-muted uppercase block">BMI</span>
                <span className="font-bold text-gray-900">{biometrics.bmi || 24.5} kg/m²</span>
              </div>
              <div className="p-3 bg-warm-bg rounded-xl border border-warm-border">
                <span className="text-[10px] text-warm-muted uppercase block">Total Cholesterol</span>
                <span className="font-bold text-gray-900">{biometrics.total_cholesterol || 190} mg/dL</span>
              </div>
              <div className="p-3 bg-warm-bg rounded-xl border border-warm-border">
                <span className="text-[10px] text-warm-muted uppercase block">HDL / LDL</span>
                <span className="font-bold text-gray-900">
                  {biometrics.hdl || 50} / {biometrics.ldl || 110} mg/dL
                </span>
              </div>
              <div className="p-3 bg-warm-bg rounded-xl border border-warm-border">
                <span className="text-[10px] text-warm-muted uppercase block">Fasting Blood Glucose</span>
                <span className="font-bold text-gray-900">{biometrics.blood_glucose || 95} mg/dL</span>
              </div>
              <div className="p-3 bg-warm-bg rounded-xl border border-warm-border">
                <span className="text-[10px] text-warm-muted uppercase block">Physical Activity</span>
                <span className="font-bold text-gray-900 capitalize">{lifestyle.physical_activity || 'Moderate'}</span>
              </div>
              <div className="p-3 bg-warm-bg rounded-xl border border-warm-border">
                <span className="text-[10px] text-warm-muted uppercase block">Smoking / Alcohol</span>
                <span className="font-bold text-gray-900 capitalize">
                  {lifestyle.smoking || 'Never'} / {lifestyle.alcohol || 'Never'}
                </span>
              </div>
            </div>
          </div>

          {/* Model Voting Sub-table */}
          <div className="space-y-2">
            <span className="text-[11px] font-bold text-gray-800 uppercase tracking-wider block">
              Ensemble Estimator Breakdown
            </span>
            <div className="overflow-x-auto">
              <table className="w-full text-left text-xs border border-warm-border rounded-xl overflow-hidden">
                <thead className="bg-warm-bg text-warm-muted uppercase tracking-wider text-[10px] font-bold border-b border-warm-border">
                  <tr>
                    <th className="p-3">Classifier Architecture</th>
                    <th className="p-3">Class Vote</th>
                    <th className="p-3">Confidence Score</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-warm-border">
                  <tr>
                    <td className="p-3 font-semibold text-gray-900">Logistic Regression</td>
                    <td className="p-3 font-bold text-gray-800">
                      {Number(section_1_prediction?.logistic_probability || 0) >= 0.5 ? 'Positive (Class 1)' : 'Negative (Class 0)'}
                    </td>
                    <td className="p-3 font-mono font-bold text-brand-800">
                      {Math.round(Number(section_1_prediction?.logistic_probability || 0) * 100)}%
                    </td>
                  </tr>
                  <tr>
                    <td className="p-3 font-semibold text-gray-900">Random Forest Classifier</td>
                    <td className="p-3 font-bold text-gray-800">
                      {Number(section_1_prediction?.random_forest_probability || 0) >= 0.5 ? 'Positive (Class 1)' : 'Negative (Class 0)'}
                    </td>
                    <td className="p-3 font-mono font-bold text-brand-800">
                      {Math.round(Number(section_1_prediction?.random_forest_probability || 0) * 100)}%
                    </td>
                  </tr>
                  <tr>
                    <td className="p-3 font-semibold text-gray-900">XGBoost Classifier</td>
                    <td className="p-3 font-bold text-gray-800">
                      {Number(section_1_prediction?.xgboost_probability || 0) >= 0.5 ? 'Positive (Class 1)' : 'Negative (Class 0)'}
                    </td>
                    <td className="p-3 font-mono font-bold text-brand-800">
                      {Math.round(Number(section_1_prediction?.xgboost_probability || 0) * 100)}%
                    </td>
                  </tr>
                </tbody>
              </table>
            </div>
          </div>
        </div>

        {/* ========================================================= */}
        {/* SECTION 2: PHYSICIAN VERIFICATION */}
        {/* ========================================================= */}
        <div className="space-y-4 pt-2">
          <div className="flex items-center space-x-2 border-b border-warm-border pb-2">
            <span className="text-xs font-bold uppercase tracking-wider text-emerald-800 bg-emerald-50 px-2.5 py-0.5 rounded-full border border-emerald-200">
              Section 2
            </span>
            <h3 className="text-base font-bold text-gray-900">Physician Clinical Verification &amp; Sign-off</h3>
          </div>

          {/* Doctor Credentials Card */}
          <div className="bg-emerald-50/50 p-5 rounded-2xl border border-emerald-200/80 flex flex-col sm:flex-row sm:items-center justify-between gap-4">
            <div className="flex items-center space-x-3.5">
              <div className="w-12 h-12 rounded-2xl bg-white text-emerald-700 flex items-center justify-center border border-emerald-200 shadow-2xs shrink-0">
                <Stethoscope className="w-6 h-6" />
              </div>
              <div>
                <h4 className="text-sm font-bold text-gray-900">
                  {section_2_verification?.doctor_name}
                </h4>
                <p className="text-xs text-warm-muted">
                  {section_2_verification?.doctor_specialization} &bull; {section_2_verification?.doctor_hospital}
                </p>
                {section_2_verification?.medical_license && (
                  <p className="text-[10px] text-warm-muted font-mono mt-0.5">
                    License #{section_2_verification.medical_license}
                  </p>
                )}
              </div>
            </div>

            <div className="text-left sm:text-right space-y-1">
              <div className="inline-flex items-center space-x-1.5 text-emerald-800 bg-emerald-100/70 px-3 py-1 rounded-full text-xs font-bold">
                <CheckCircle2 className="w-3.5 h-3.5" />
                <span>Verified by Attending Physician</span>
              </div>
              <p className="text-[11px] text-warm-muted">
                Timestamp: {formattedVerDate} at {formattedVerTime}
              </p>
            </div>
          </div>

          {/* Doctor's Clinical Assessment Notes */}
          <div className="space-y-1.5">
            <span className="text-[11px] font-bold text-gray-800 uppercase tracking-wider block">
              Physician Clinical Assessment Notes
            </span>
            <div className="p-4 bg-warm-bg rounded-2xl border border-warm-border text-xs text-gray-900 whitespace-pre-wrap leading-relaxed">
              {section_2_verification?.doctor_notes || 'Clinical evaluation and diagnostic predictions verified.'}
            </div>
          </div>
        </div>

        {/* ========================================================= */}
        {/* SECTION 3: DOCTOR'S SUGGESTIONS & RECOMMENDATIONS */}
        {/* ========================================================= */}
        <div className="space-y-4 pt-2">
          <div className="flex items-center space-x-2 border-b border-warm-border pb-2">
            <span className="text-xs font-bold uppercase tracking-wider text-brand-800 bg-brand-50 px-2.5 py-0.5 rounded-full border border-brand-200">
              Section 3
            </span>
            <h3 className="text-base font-bold text-gray-900">Physician Suggestions &amp; Recommendations</h3>
          </div>

          <p className="text-xs text-warm-muted">
            The following instructions and clinical recommendations were directly entered by your attending physician based on your cardiovascular evaluation.
          </p>

          {/* Complete Doctor Recommendations Box */}
          <div className="p-5 bg-gradient-to-r from-warm-bg to-white rounded-2xl border-2 border-brand-800/20 shadow-xs space-y-3">
            <div className="flex items-center space-x-2 text-brand-800 font-bold text-xs uppercase tracking-wider">
              <Heart className="w-4 h-4 fill-brand-800/20" />
              <span>Attending Physician Clinical Guidance</span>
            </div>
            <div className="text-xs text-gray-900 whitespace-pre-wrap leading-relaxed font-medium">
              {section_3_recommendations?.recommendations || section_2_verification?.doctor_notes || 'Please follow up with your doctor for periodic blood pressure and lipid screening.'}
            </div>
          </div>
        </div>

        {/* Medical Disclaimer */}
        <div className="border-t border-warm-border pt-6">
          <div className="p-4 rounded-2xl bg-amber-50/60 border border-amber-200/80 text-gray-800 text-xs leading-relaxed">
            <span className="font-bold text-amber-900 block mb-1 uppercase tracking-wider text-[10px]">
              Clinical Disclaimer &amp; Confidentiality Notice
            </span>
            This official medical report combines artificial intelligence predictive scoring with clinical physician oversight. It is strictly confidential and meant solely for the patient named above and their healthcare providers. Please contact your hospital or healthcare team directly for any emergency symptoms.
          </div>
        </div>
      </div>
    </div>
  );
}
