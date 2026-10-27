import React, { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import {
  Activity,
  Search,
  Filter,
  Calendar,
  AlertTriangle,
  CheckCircle2,
  Clock,
  Heart,
  User,
  ArrowRight,
  TrendingUp,
  FileText,
  X,
  Shield,
  Stethoscope,
  ChevronRight
} from 'lucide-react';
import Sidebar from '../components/Sidebar';
import RiskGauge from '../components/RiskGauge';
import api from '../api/client';

export default function DoctorAssessmentsPage() {
  const [assessments, setAssessments] = useState([]);
  const [loading, setLoading] = useState(true);
  const [searchTerm, setSearchTerm] = useState('');
  const [selectedRiskFilter, setSelectedRiskFilter] = useState('ALL');
  const [selectedAssessmentDetail, setSelectedAssessmentDetail] = useState(null);
  const [loadingDetail, setLoadingDetail] = useState(false);
  const [patientHistoryList, setPatientHistoryList] = useState(null);
  const [loadingHistory, setLoadingHistory] = useState(false);
  const [selectedPatientName, setSelectedPatientName] = useState('');

  const fetchAssessments = async () => {
    try {
      setLoading(true);
      const res = await api.get('/doctor-assessments');
      setAssessments(res.data?.assessments || []);
    } catch (err) {
      console.error('Failed to load doctor assessments:', err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchAssessments();
  }, []);

  const handleOpenDetail = async (assessmentId) => {
    try {
      setLoadingDetail(true);
      const res = await api.get(`/doctor-assessments/${assessmentId}`);
      setSelectedAssessmentDetail(res.data);
    } catch (err) {
      console.error('Failed to load assessment details:', err);
      alert('Could not access this assessment. You only have access to your approved patients.');
    } finally {
      setLoadingDetail(false);
    }
  };

  const handleViewPatientHistory = async (patientId, patientName) => {
    try {
      setLoadingHistory(true);
      setSelectedPatientName(patientName);
      const res = await api.get(`/doctor-assessments/patient/${patientId}`);
      setPatientHistoryList(res.data?.history || []);
    } catch (err) {
      console.error('Failed to load patient history:', err);
      alert('Could not access patient history.');
    } finally {
      setLoadingHistory(false);
    }
  };

  const getRiskBadge = (level) => {
    const l = String(level || '').toUpperCase();
    if (l.includes('NO ASSESSMENT') || !level) {
      return (
        <span className="inline-flex items-center space-x-1 px-2.5 py-1 rounded-full text-xs font-semibold bg-gray-100 text-gray-700 border border-gray-200">
          <span>No assessment found</span>
        </span>
      );
    }
    if (l.includes('HIGH')) {
      return (
        <span className="inline-flex items-center space-x-1 px-2.5 py-1 rounded-full text-xs font-bold bg-red-50 text-red-700 border border-red-200">
          <AlertTriangle className="w-3 h-3 text-red-600" />
          <span>High Risk</span>
        </span>
      );
    }
    if (l.includes('MOD') || l.includes('MED')) {
      return (
        <span className="inline-flex items-center space-x-1 px-2.5 py-1 rounded-full text-xs font-bold bg-amber-50 text-amber-700 border border-amber-200">
          <Clock className="w-3 h-3 text-amber-600" />
          <span>Moderate Risk</span>
        </span>
      );
    }
    return (
      <span className="inline-flex items-center space-x-1 px-2.5 py-1 rounded-full text-xs font-bold bg-emerald-50 text-emerald-700 border border-emerald-200">
        <CheckCircle2 className="w-3 h-3 text-emerald-600" />
        <span>Low Risk</span>
      </span>
    );
  };

  const filteredAssessments = assessments.filter((item) => {
    const matchesSearch =
      item.patient_name.toLowerCase().includes(searchTerm.toLowerCase()) ||
      (item.patient_email && item.patient_email.toLowerCase().includes(searchTerm.toLowerCase()));

    const riskLevel = String(item.risk_level || '').toUpperCase();
    const matchesRisk =
      selectedRiskFilter === 'ALL' ||
      (selectedRiskFilter === 'HIGH' && riskLevel.includes('HIGH')) ||
      (selectedRiskFilter === 'MODERATE' && (riskLevel.includes('MOD') || riskLevel.includes('MED'))) ||
      (selectedRiskFilter === 'LOW' && riskLevel.includes('LOW'));

    return matchesSearch && matchesRisk;
  });

  return (
    <div className="min-h-screen flex flex-col lg:flex-row bg-warm-bg w-full min-w-0 overflow-x-hidden">
      <Sidebar />

      <main className="flex-1 p-4 sm:p-6 lg:p-10 max-w-7xl w-full mx-auto space-y-8 min-w-0">
        {/* Header */}
        <div className="bg-white rounded-3xl p-6 sm:p-8 border border-warm-border shadow-xs flex flex-col sm:flex-row items-start sm:items-center justify-between gap-6">
          <div className="space-y-1.5">
            <div className="flex items-center space-x-2">
              <span className="text-[11px] font-bold uppercase tracking-wider text-brand-800 bg-brand-50 px-2.5 py-0.5 rounded-full border border-brand-200">
                Supervised Cardiology Records
              </span>
              <span className="text-xs text-warm-muted">Approved Patient Roster Only</span>
            </div>
            <h1 className="text-2xl sm:text-3xl font-black text-gray-900 tracking-tight">
              Patient Risk Assessments
            </h1>
            <p className="text-xs sm:text-sm text-warm-muted">
              Inspect explainable AI cardiovascular evaluations for patients under your approved clinical supervision.
            </p>
          </div>

          <Link
            to="/doctor/requests"
            className="inline-flex items-center space-x-2 px-5 py-2.5 rounded-full bg-brand-800 text-white font-bold text-xs hover:bg-brand-900 shadow-sm transition-all shrink-0"
          >
            <User className="w-4 h-4" />
            <span>Manage Approved Patients</span>
          </Link>
        </div>

        {/* Filter and Search Bar */}
        <div className="bg-white p-4 sm:p-5 rounded-2xl border border-warm-border shadow-xs flex flex-col md:flex-row gap-4 items-center justify-between">
          <div className="relative w-full md:w-80">
            <Search className="w-4 h-4 text-warm-muted absolute left-3 top-1/2 -translate-y-1/2" />
            <input
              type="text"
              placeholder="Search by patient name, email..."
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
              className="w-full pl-9 pr-4 py-2 bg-warm-bg border border-warm-border rounded-xl text-xs text-gray-900 focus:outline-none focus:border-brand-800"
            />
          </div>

          <div className="flex items-center space-x-2 w-full md:w-auto overflow-x-auto">
            <span className="text-xs font-bold text-warm-muted whitespace-nowrap">Risk Category:</span>
            {['ALL', 'HIGH', 'MODERATE', 'LOW'].map((risk) => (
              <button
                key={risk}
                onClick={() => setSelectedRiskFilter(risk)}
                className={`px-3 py-1.5 rounded-xl text-xs font-semibold transition-all ${
                  selectedRiskFilter === risk
                    ? 'bg-brand-800 text-white shadow-xs'
                    : 'bg-warm-bg text-gray-600 hover:bg-rose-50/50 border border-warm-border'
                }`}
              >
                {risk}
              </button>
            ))}
          </div>
        </div>

        {/* Assessment Cards / Table */}
        {loading ? (
          <div className="p-16 text-center bg-white rounded-3xl border border-warm-border">
            <div className="w-10 h-10 border-3 border-brand-800 border-t-transparent rounded-full animate-spin mx-auto mb-3" />
            <p className="text-xs font-semibold text-warm-muted">Loading approved patient assessments...</p>
          </div>
        ) : filteredAssessments.length === 0 ? (
          <div className="p-16 text-center bg-white rounded-3xl border border-warm-border space-y-3">
            <Activity className="w-12 h-12 text-warm-muted mx-auto" />
            <h3 className="text-sm font-bold text-gray-800">No Assessments Available</h3>
            <p className="text-xs text-warm-muted max-w-sm mx-auto">
              {assessments.length === 0
                ? 'You do not have any approved patients with logged risk assessments yet. Accept patient consultation requests to view their assessments.'
                : 'No assessments match your current search or risk level filter.'}
            </p>
            {assessments.length === 0 && (
              <Link
                to="/doctor/requests"
                className="inline-block mt-2 px-5 py-2.5 rounded-xl text-xs font-bold text-white bg-brand-800 hover:bg-brand-900"
              >
                Check Patient Requests
              </Link>
            )}
          </div>
        ) : (
          <div className="bg-white rounded-3xl border border-warm-border shadow-xs overflow-hidden">
            <div className="p-6 border-b border-warm-border flex items-center justify-between">
              <div>
                <h3 className="text-sm font-bold text-gray-900">Latest Cardiac Risk Evaluations</h3>
                <p className="text-xs text-warm-muted">Chronological assessment history of supervised patients</p>
              </div>
              <span className="text-xs font-mono font-bold text-brand-800 bg-brand-50 px-2.5 py-1 rounded-full border border-brand-200">
                {filteredAssessments.length} Records
              </span>
            </div>

            <div className="overflow-x-auto">
              <table className="w-full text-left text-xs">
                <thead className="bg-warm-bg text-warm-muted uppercase tracking-wider text-[10px] font-bold border-b border-warm-border">
                  <tr>
                    <th className="py-4 px-6">Patient</th>
                    <th className="py-4 px-6">Evaluation Date</th>
                    <th className="py-4 px-6">Risk Category</th>
                    <th className="py-4 px-6">Ensemble Prob.</th>
                    <th className="py-4 px-6">Blood Pressure</th>
                    <th className="py-4 px-6">Cholesterol / Glucose</th>
                    <th className="py-4 px-6 text-right">Actions</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-warm-border">
                  {filteredAssessments.map((item) => (
                    <tr key={item.assessment_id} className="hover:bg-rose-50/20 transition-colors">
                      <td className="py-4 px-6">
                        <div className="font-bold text-gray-900">{item.patient_name}</div>
                        <div className="text-[11px] text-warm-muted font-mono">{item.patient_email}</div>
                      </td>

                      <td className="py-4 px-6 font-mono text-warm-muted">
                        {item.assessment_date
                          ? new Date(item.assessment_date).toLocaleDateString('en-GB', {
                              day: 'numeric',
                              month: 'short',
                              year: 'numeric'
                            })
                          : '—'}
                      </td>

                      <td className="py-4 px-6">
                        {getRiskBadge(item.risk_level)}
                      </td>

                      <td className="py-4 px-6 font-bold text-gray-900">
                        {item.ensemble_probability !== null && item.ensemble_probability !== undefined
                          ? `${Math.round(item.ensemble_probability * 100)}%`
                          : '—'}
                      </td>

                      <td className="py-4 px-6 font-mono text-gray-700">
                        {item.systolic_bp && item.diastolic_bp
                          ? `${Math.round(item.systolic_bp)} / ${Math.round(item.diastolic_bp)} mmHg`
                          : '—'}
                      </td>

                      <td className="py-4 px-6 text-warm-muted">
                        <div>Chol: {item.total_cholesterol ? `${Math.round(item.total_cholesterol)} mg/dL` : '—'}</div>
                        <div>Gluc: {item.blood_glucose ? `${Math.round(item.blood_glucose)} mg/dL` : '—'}</div>
                      </td>

                      <td className="py-4 px-6 text-right space-x-2">
                        {item.assessment_id ? (
                          <button
                            onClick={() => handleOpenDetail(item.assessment_id)}
                            className="inline-flex items-center space-x-1 px-3 py-1.5 rounded-lg text-xs font-bold text-white bg-brand-800 hover:bg-brand-900 transition-all shadow-xs"
                          >
                            <span>Full Detail</span>
                            <ChevronRight className="w-3.5 h-3.5" />
                          </button>
                        ) : (
                          <span className="text-xs text-warm-muted italic pr-2">No assessment found</span>
                        )}
                        <button
                          onClick={() => handleViewPatientHistory(item.patient_id, item.patient_name)}
                          className="inline-flex items-center space-x-1 px-2.5 py-1.5 rounded-lg text-xs font-semibold text-gray-700 bg-warm-bg hover:bg-gray-100 border border-warm-border transition-all"
                        >
                          <span>History</span>
                        </button>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        )}

        {/* Assessment Detail Modal */}
        {selectedAssessmentDetail && (
          <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50 backdrop-blur-xs p-4 overflow-y-auto">
            <div className="bg-white rounded-3xl max-w-2xl w-full p-6 sm:p-8 border border-warm-border shadow-2xl space-y-6 my-8 animate-in fade-in duration-200 max-h-[90vh] overflow-y-auto">
              <div className="flex items-start justify-between border-b border-warm-border pb-4">
                <div>
                  <div className="flex items-center space-x-2">
                    <span className="text-[10px] font-bold uppercase tracking-wider text-brand-800 bg-brand-50 px-2 py-0.5 rounded-full border border-brand-200">
                      Assessment #{selectedAssessmentDetail.assessment_id}
                    </span>
                    <span className="text-xs text-warm-muted">
                      {selectedAssessmentDetail.created_at
                        ? new Date(selectedAssessmentDetail.created_at).toLocaleDateString('en-GB', {
                            day: 'numeric',
                            month: 'long',
                            year: 'numeric'
                          })
                        : ''}
                    </span>
                  </div>
                  <h2 className="text-xl font-black text-gray-900 mt-1">
                    {selectedAssessmentDetail.patient?.full_name} — Cardiac Evaluation
                  </h2>
                </div>
                <button
                  onClick={() => setSelectedAssessmentDetail(null)}
                  className="p-1.5 rounded-xl text-gray-400 hover:text-gray-700 hover:bg-gray-100"
                >
                  <X className="w-5 h-5" />
                </button>
              </div>

              {/* Prediction Summary Header */}
              {selectedAssessmentDetail.prediction && (
                <div className="p-4 rounded-2xl bg-rose-50/60 border border-rose-100 flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4">
                  <div>
                    <span className="text-[10px] uppercase font-bold text-brand-800 tracking-wider">
                      AI Ensemble Prediction
                    </span>
                    <div className="flex items-center space-x-3 mt-1">
                      <span className="text-2xl font-black text-gray-900">
                        {Math.round((selectedAssessmentDetail.prediction.ensemble_probability || 0) * 100)}%
                      </span>
                      {getRiskBadge(selectedAssessmentDetail.prediction.risk_level)}
                    </div>
                  </div>

                  <div className="grid grid-cols-3 gap-2 text-center text-[10px] bg-white p-2.5 rounded-xl border border-warm-border">
                    <div>
                      <span className="block text-gray-400">Log. Reg</span>
                      <span className="font-bold text-gray-800">
                        {Math.round((selectedAssessmentDetail.prediction.logistic_probability || 0) * 100)}%
                      </span>
                    </div>
                    <div>
                      <span className="block text-gray-400">Rand. For</span>
                      <span className="font-bold text-gray-800">
                        {Math.round((selectedAssessmentDetail.prediction.random_forest_probability || 0) * 100)}%
                      </span>
                    </div>
                    <div>
                      <span className="block text-gray-400">XGBoost</span>
                      <span className="font-bold text-gray-800">
                        {Math.round((selectedAssessmentDetail.prediction.xgboost_probability || 0) * 100)}%
                      </span>
                    </div>
                  </div>
                </div>
              )}

              {/* Clinical Features Grid */}
              <div className="space-y-2">
                <h3 className="text-xs font-bold uppercase tracking-wider text-gray-700">
                  Clinical Measurements & Biomarkers
                </h3>
                <div className="grid grid-cols-2 sm:grid-cols-4 gap-3 text-xs">
                  <div className="p-3 bg-warm-bg rounded-xl border border-warm-border">
                    <span className="text-[10px] text-warm-muted block">Blood Pressure</span>
                    <span className="font-bold text-gray-900">
                      {selectedAssessmentDetail.clinical_features?.systolic_bp} / {selectedAssessmentDetail.clinical_features?.diastolic_bp} mmHg
                    </span>
                  </div>
                  <div className="p-3 bg-warm-bg rounded-xl border border-warm-border">
                    <span className="text-[10px] text-warm-muted block">Heart Rate</span>
                    <span className="font-bold text-gray-900">
                      {selectedAssessmentDetail.clinical_features?.heart_rate} bpm
                    </span>
                  </div>
                  <div className="p-3 bg-warm-bg rounded-xl border border-warm-border">
                    <span className="text-[10px] text-warm-muted block">Total Cholesterol</span>
                    <span className="font-bold text-gray-900">
                      {selectedAssessmentDetail.clinical_features?.total_cholesterol} mg/dL
                    </span>
                  </div>
                  <div className="p-3 bg-warm-bg rounded-xl border border-warm-border">
                    <span className="text-[10px] text-warm-muted block">BMI</span>
                    <span className="font-bold text-gray-900">
                      {selectedAssessmentDetail.clinical_features?.bmi} kg/m²
                    </span>
                  </div>
                  <div className="p-3 bg-warm-bg rounded-xl border border-warm-border">
                    <span className="text-[10px] text-warm-muted block">HDL Cholesterol</span>
                    <span className="font-bold text-gray-900">
                      {selectedAssessmentDetail.clinical_features?.hdl} mg/dL
                    </span>
                  </div>
                  <div className="p-3 bg-warm-bg rounded-xl border border-warm-border">
                    <span className="text-[10px] text-warm-muted block">LDL Cholesterol</span>
                    <span className="font-bold text-gray-900">
                      {selectedAssessmentDetail.clinical_features?.ldl} mg/dL
                    </span>
                  </div>
                  <div className="p-3 bg-warm-bg rounded-xl border border-warm-border">
                    <span className="text-[10px] text-warm-muted block">Blood Glucose</span>
                    <span className="font-bold text-gray-900">
                      {selectedAssessmentDetail.clinical_features?.blood_glucose} mg/dL
                    </span>
                  </div>
                  <div className="p-3 bg-warm-bg rounded-xl border border-warm-border">
                    <span className="text-[10px] text-warm-muted block">Gender / DOB</span>
                    <span className="font-bold text-gray-900 capitalize">
                      {selectedAssessmentDetail.patient?.gender || '—'}
                    </span>
                  </div>
                </div>
              </div>

              {/* Medical History & Lifestyle */}
              <div className="grid grid-cols-1 sm:grid-cols-2 gap-4 text-xs">
                {/* Medical History */}
                <div className="p-4 bg-warm-bg rounded-2xl border border-warm-border space-y-2">
                  <h4 className="font-bold text-gray-900 text-xs">Medical History</h4>
                  <div className="space-y-1.5 text-[11px]">
                    <div className="flex justify-between">
                      <span className="text-warm-muted">Hypertension:</span>
                      <span className="font-semibold text-gray-800">
                        {selectedAssessmentDetail.medical_history?.hypertension ? 'Yes' : 'No'}
                      </span>
                    </div>
                    <div className="flex justify-between">
                      <span className="text-warm-muted">Diabetes:</span>
                      <span className="font-semibold text-gray-800">
                        {selectedAssessmentDetail.medical_history?.diabetes ? 'Yes' : 'No'}
                      </span>
                    </div>
                    <div className="flex justify-between">
                      <span className="text-warm-muted">Previous Heart Disease:</span>
                      <span className="font-semibold text-gray-800">
                        {selectedAssessmentDetail.medical_history?.previous_heart_disease ? 'Yes' : 'No'}
                      </span>
                    </div>
                    <div className="flex justify-between">
                      <span className="text-warm-muted">Family Cardiac History:</span>
                      <span className="font-semibold text-gray-800">
                        {selectedAssessmentDetail.medical_history?.family_history ? 'Yes' : 'No'}
                      </span>
                    </div>
                  </div>
                </div>

                {/* Lifestyle */}
                <div className="p-4 bg-warm-bg rounded-2xl border border-warm-border space-y-2">
                  <h4 className="font-bold text-gray-900 text-xs">Lifestyle Factors</h4>
                  <div className="space-y-1.5 text-[11px]">
                    <div className="flex justify-between">
                      <span className="text-warm-muted">Smoking:</span>
                      <span className="font-semibold text-gray-800 capitalize">
                        {selectedAssessmentDetail.lifestyle?.smoking || 'Non-smoker'}
                      </span>
                    </div>
                    <div className="flex justify-between">
                      <span className="text-warm-muted">Alcohol:</span>
                      <span className="font-semibold text-gray-800 capitalize">
                        {selectedAssessmentDetail.lifestyle?.alcohol || 'None'}
                      </span>
                    </div>
                    <div className="flex justify-between">
                      <span className="text-warm-muted">Physical Activity:</span>
                      <span className="font-semibold text-gray-800 capitalize">
                        {selectedAssessmentDetail.lifestyle?.physical_activity || 'Moderate'}
                      </span>
                    </div>
                    <div className="flex justify-between">
                      <span className="text-warm-muted">Diet:</span>
                      <span className="font-semibold text-gray-800 capitalize">
                        {selectedAssessmentDetail.lifestyle?.diet || 'Balanced'}
                      </span>
                    </div>
                  </div>
                </div>
              </div>

              {/* Bottom Actions */}
              <div className="flex items-center justify-between pt-2 border-t border-warm-border">
                <Link
                  to={`/doctor/patient/${selectedAssessmentDetail.patient?.patient_id}`}
                  className="inline-flex items-center space-x-1.5 px-4 py-2 rounded-xl text-xs font-bold text-brand-800 bg-brand-50 hover:bg-brand-100"
                >
                  <FileText className="w-3.5 h-3.5" />
                  <span>Open Full Clinical Chart</span>
                </Link>

                <button
                  onClick={() => setSelectedAssessmentDetail(null)}
                  className="px-5 py-2 rounded-xl text-xs font-semibold text-gray-700 bg-gray-100 hover:bg-gray-200"
                >
                  Close
                </button>
              </div>
            </div>
          </div>
        )}

        {/* Patient History Modal */}
        {patientHistoryList && (
          <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50 backdrop-blur-xs p-4">
            <div className="bg-white rounded-3xl max-w-xl w-full p-6 sm:p-7 border border-warm-border shadow-2xl space-y-4 animate-in fade-in duration-200 max-h-[85vh] overflow-y-auto">
              <div className="flex items-center justify-between border-b border-warm-border pb-3">
                <div>
                  <h3 className="text-base font-bold text-gray-900">
                    {selectedPatientName} — Assessment History
                  </h3>
                  <p className="text-xs text-warm-muted">
                    All historical risk assessments under your supervision
                  </p>
                </div>
                <button
                  onClick={() => setPatientHistoryList(null)}
                  className="p-1 rounded-lg text-gray-400 hover:text-gray-700"
                >
                  <X className="w-5 h-5" />
                </button>
              </div>

              {patientHistoryList.length === 0 ? (
                <p className="text-xs text-warm-muted py-6 text-center">No assessments found for this patient.</p>
              ) : (
                <div className="space-y-3">
                  {patientHistoryList.map((h) => (
                    <div
                      key={h.assessment_id}
                      className="p-3.5 rounded-2xl bg-warm-bg border border-warm-border flex items-center justify-between text-xs"
                    >
                      <div>
                        <div className="font-bold text-gray-900">
                          {h.assessment_date ? new Date(h.assessment_date).toLocaleDateString() : 'Assessment'}
                        </div>
                        <div className="text-[11px] text-warm-muted mt-0.5">
                          BP: {h.systolic_bp || '—'}/{h.diastolic_bp || '—'} mmHg • HR: {h.heart_rate || '—'} bpm
                        </div>
                      </div>

                      <div className="flex items-center space-x-3">
                        {getRiskBadge(h.risk_level)}
                        <button
                          onClick={() => {
                            setPatientHistoryList(null);
                            handleOpenDetail(h.assessment_id);
                          }}
                          className="px-2.5 py-1 rounded-lg bg-white border border-warm-border text-brand-800 font-bold hover:bg-rose-50"
                        >
                          View
                        </button>
                      </div>
                    </div>
                  ))}
                </div>
              )}
            </div>
          </div>
        )}
      </main>
    </div>
  );
}
