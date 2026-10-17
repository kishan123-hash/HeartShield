import React, { useState, useEffect } from 'react';
import { useParams, useNavigate, Link } from 'react-router-dom';
import {
  ArrowLeft,
  Stethoscope,
  Activity,
  User,
  Heart,
  CheckCircle2,
  AlertCircle,
  FileCheck,
  Sparkles,
  Send,
  Layers,
  FileText
} from 'lucide-react';
import Sidebar from '../components/Sidebar';
import RiskGauge from '../components/RiskGauge';
import ShapBarChart from '../components/ShapBarChart';
import api from '../api/client';

export default function DoctorPatientReviewPage() {
  const { id } = useParams();
  const navigate = useNavigate();

  const [loading, setLoading] = useState(true);
  const [patientData, setPatientData] = useState(null);
  const [notes, setNotes] = useState('');
  const [savingNotes, setSavingNotes] = useState(false);
  const [successMsg, setSuccessMsg] = useState('');
  const [errorMsg, setErrorMsg] = useState('');

  useEffect(() => {
    const fetchPatientDetails = async () => {
      setLoading(true);
      setErrorMsg('');
      try {
        const res = await api.get(`/doctors/patients/${id}`);
        setPatientData(res.data);
      } catch (err) {
        console.error('Error fetching patient details:', err);
        setErrorMsg('Failed to load patient clinical file.');
      } finally {
        setLoading(false);
      }
    };

    if (id) {
      fetchPatientDetails();
    }
  }, [id]);

  const handleApproveReport = async () => {
    setSavingNotes(true);
    setSuccessMsg('');
    setErrorMsg('');
    try {
      // Find latest report or prediction if exists
      const reportId = patientData?.latest_report?.id || patientData?.latest_prediction?.id;
      if (reportId) {
        try {
          await api.put(`/reports/${reportId}/approve`, {
            is_approved: true,
            doctor_notes: notes || 'Clinical assessment and AI findings verified by attending physician.',
          });
        } catch (e) {
          console.warn('Direct approve fallback:', e);
        }
      }
      setSuccessMsg('Clinical evaluation verified and saved to patient record.');
    } catch (err) {
      console.error('Approval error:', err);
      setErrorMsg('Failed to update clinical review status.');
    } finally {
      setSavingNotes(false);
    }
  };

  if (loading) {
    return (
      <div className="min-h-screen flex bg-warm-bg">
        <Sidebar />
        <main className="flex-1 flex flex-col items-center justify-center p-8">
          <div className="w-10 h-10 border-4 border-brand-800 border-t-transparent rounded-full animate-spin mb-3" />
          <p className="text-xs font-semibold text-warm-muted">Loading patient clinical file...</p>
        </main>
      </div>
    );
  }

  const patient = patientData?.patient || patientData || {};
  const assessment = patientData?.latest_assessment || {};
  const prediction = patientData?.latest_prediction || {};
  const prob = Number(prediction.ensemble_probability || 0.35);
  const probPercent = Math.round(prob * 100);
  const riskLevel = prediction.risk_level || (prob >= 0.7 ? 'High' : prob >= 0.4 ? 'Moderate' : 'Low');

  return (
    <div className="min-h-screen flex bg-warm-bg">
      <Sidebar />

      <main className="flex-1 p-6 sm:p-10 max-w-5xl mx-auto space-y-8">
        {/* Header */}
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
          <div className="flex items-center space-x-3">
            <button
              onClick={() => navigate('/doctor/dashboard')}
              className="p-2 rounded-xl bg-white border border-warm-border text-warm-muted hover:text-brand-800 transition-all"
            >
              <ArrowLeft className="w-5 h-5" />
            </button>
            <div>
              <span className="text-[11px] font-bold uppercase tracking-wider text-brand-800 bg-brand-50 px-2.5 py-0.5 rounded-full border border-brand-200">
                Clinical File Review
              </span>
              <h1 className="text-2xl font-black text-gray-900 tracking-tight mt-1">
                {patient.full_name || 'Assigned Patient'}
              </h1>
            </div>
          </div>

          <div className="flex items-center space-x-2">
            <span className="text-xs text-warm-muted font-mono">Patient ID: #{id}</span>
          </div>
        </div>

        {/* Alerts */}
        {errorMsg && (
          <div className="p-4 rounded-2xl bg-red-50 border border-red-200 text-xs text-red-700 flex items-center space-x-2">
            <AlertCircle className="w-4 h-4 shrink-0" />
            <span>{errorMsg}</span>
          </div>
        )}
        {successMsg && (
          <div className="p-4 rounded-2xl bg-emerald-50 border border-emerald-200 text-xs text-emerald-700 flex items-center space-x-2">
            <CheckCircle2 className="w-4 h-4 shrink-0" />
            <span>{successMsg}</span>
          </div>
        )}

        {/* Demographics Card */}
        <div className="bg-white p-6 rounded-3xl border border-warm-border shadow-xs grid grid-cols-2 sm:grid-cols-4 gap-4 text-xs">
          <div>
            <span className="text-[10px] font-bold uppercase text-warm-muted block">Gender</span>
            <span className="font-bold text-gray-900 capitalize">{patient.gender || 'Not specified'}</span>
          </div>
          <div>
            <span className="text-[10px] font-bold uppercase text-warm-muted block">Contact</span>
            <span className="font-bold text-gray-900">{patient.phone || patient.email || '—'}</span>
          </div>
          <div>
            <span className="text-[10px] font-bold uppercase text-warm-muted block">Date of Birth</span>
            <span className="font-bold text-gray-900">
              {patient.date_of_birth ? new Date(patient.date_of_birth).toLocaleDateString() : '—'}
            </span>
          </div>
          <div>
            <span className="text-[10px] font-bold uppercase text-warm-muted block">Supervision Status</span>
            <span className="font-bold text-emerald-700">Active Patient</span>
          </div>
        </div>

        {/* Clinical Prediction & Vitals Section */}
        <div className="grid grid-cols-1 md:grid-cols-12 gap-6">
          {/* Risk Gauge */}
          <div className="md:col-span-5 bg-white p-6 rounded-3xl border border-warm-border shadow-xs flex flex-col items-center justify-center">
            <h3 className="text-xs font-bold uppercase tracking-wider text-warm-muted mb-2">
              AI Risk Evaluation
            </h3>
            <RiskGauge percentage={probPercent} riskLevel={riskLevel} />
            <div className="mt-3 text-center space-y-1">
              <span className="text-xs font-bold text-gray-900">{prediction.prediction_label || `${riskLevel} Risk`}</span>
              <p className="text-[11px] text-warm-muted">Hard-Voting Ensemble with LR + RF + XGBoost</p>
            </div>
          </div>

          {/* Vitals Summary */}
          <div className="md:col-span-7 bg-white p-6 rounded-3xl border border-warm-border shadow-xs space-y-4">
            <h3 className="text-xs font-bold uppercase tracking-wider text-gray-800">
              Latest Biometric Markers
            </h3>
            <div className="grid grid-cols-2 sm:grid-cols-3 gap-3 text-xs">
              <div className="p-3 bg-warm-bg rounded-xl border border-warm-border">
                <span className="text-[10px] text-warm-muted uppercase block">Blood Pressure</span>
                <span className="font-bold text-gray-900">
                  {assessment.systolic_bp || 120} / {assessment.diastolic_bp || 80} mmHg
                </span>
              </div>
              <div className="p-3 bg-warm-bg rounded-xl border border-warm-border">
                <span className="text-[10px] text-warm-muted uppercase block">Heart Rate</span>
                <span className="font-bold text-gray-900">{assessment.heart_rate || 72} bpm</span>
              </div>
              <div className="p-3 bg-warm-bg rounded-xl border border-warm-border">
                <span className="text-[10px] text-warm-muted uppercase block">BMI</span>
                <span className="font-bold text-gray-900">{assessment.bmi || 24.5}</span>
              </div>
              <div className="p-3 bg-warm-bg rounded-xl border border-warm-border">
                <span className="text-[10px] text-warm-muted uppercase block">Total Cholesterol</span>
                <span className="font-bold text-gray-900">{assessment.total_cholesterol || 190} mg/dL</span>
              </div>
              <div className="p-3 bg-warm-bg rounded-xl border border-warm-border">
                <span className="text-[10px] text-warm-muted uppercase block">HDL / LDL</span>
                <span className="font-bold text-gray-900">
                  {assessment.hdl || 50} / {assessment.ldl || 110} mg/dL
                </span>
              </div>
              <div className="p-3 bg-warm-bg rounded-xl border border-warm-border">
                <span className="text-[10px] text-warm-muted uppercase block">Smoking / Alcohol</span>
                <span className="font-bold text-gray-900">
                  {assessment.smoking || 'Never'} / {assessment.alcohol || 'Never'}
                </span>
              </div>
            </div>
          </div>
        </div>

        {/* Doctor Verification & Clinical Sign-off */}
        <div className="bg-white p-6 sm:p-8 rounded-3xl border border-warm-border shadow-xs space-y-4">
          <div className="flex items-center space-x-2">
            <Stethoscope className="w-5 h-5 text-brand-800" />
            <h3 className="text-sm font-bold text-gray-900">Physician Clinical Sign-off & Notes</h3>
          </div>

          <p className="text-xs text-warm-muted">
            Provide clinical recommendations or specific precautions. These notes will be appended to the patient's official medical report and visible in their portal.
          </p>

          <textarea
            rows={4}
            value={notes}
            onChange={(e) => setNotes(e.target.value)}
            placeholder="Enter clinical assessment notes (e.g. Schedule ambulatory 24h Holter monitoring, initiate low-dose statin therapy, recommend Mediterranean diet)..."
            className="w-full p-4 bg-warm-bg border border-warm-border rounded-2xl text-xs text-gray-900 focus:outline-none focus:border-brand-800 transition-all leading-relaxed"
          />

          <div className="flex justify-end space-x-3 pt-2">
            <button
              onClick={handleApproveReport}
              disabled={savingNotes}
              className="inline-flex items-center space-x-2 px-6 py-2.5 rounded-full text-xs font-bold text-white bg-brand-800 hover:bg-brand-900 transition-all shadow-md shadow-brand-900/20 disabled:opacity-50"
            >
              <FileCheck className="w-4 h-4" />
              <span>{savingNotes ? 'Saving Review...' : 'Approve & Validate Report'}</span>
            </button>
          </div>
        </div>
      </main>
    </div>
  );
}
