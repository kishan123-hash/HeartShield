import React, { useState, useEffect } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import {
  Users,
  Activity,
  AlertTriangle,
  CheckCircle2,
  Clock,
  ArrowRight,
  Shield,
  Stethoscope,
  Search,
  UserCheck,
  MessageCircle,
  XCircle,
  FileText
} from 'lucide-react';
import Sidebar from '../components/Sidebar';
import api from '../api/client';

export default function DoctorDashboardPage() {
  const navigate = useNavigate();
  const [stats, setStats] = useState({
    total_patients: 0,
    pending_reviews: 0,
    completed_assessments: 0,
    high_risk_patients: 0,
  });
  const [patients, setPatients] = useState([]);
  const [recentAssessments, setRecentAssessments] = useState([]);
  const [consultationRequests, setConsultationRequests] = useState([]);
  const [loading, setLoading] = useState(true);
  const [searchTerm, setSearchTerm] = useState('');
  const [processingReqId, setProcessingReqId] = useState(null);
  const [actionAlert, setActionAlert] = useState(null);

  const fetchDoctorData = async () => {
    setLoading(true);
    try {
      // Fetch stats
      try {
        const statsRes = await api.get('/doctors/dashboard/stats');
        setStats(statsRes.data);
      } catch (sErr) {
        console.warn('Doctor stats fetch:', sErr);
      }

      // Fetch patients
      try {
        const patientsRes = await api.get('/doctors/patients');
        setPatients(patientsRes.data?.patients || []);
      } catch (pErr) {
        console.warn('Doctor patients fetch:', pErr);
      }

      // Fetch consultation requests
      try {
        const reqRes = await api.get('/consultations/doctor-requests');
        setConsultationRequests(reqRes.data || []);
      } catch (rErr) {
        console.warn('Consultation requests fetch:', rErr);
      }

      // Fetch recent assessments
      try {
        const assessRes = await api.get('/doctors/dashboard/recent-assessments');
        setRecentAssessments(assessRes.data?.recent_assessments || []);
      } catch (aErr) {
        console.warn('Recent assessments fetch:', aErr);
      }
    } catch (err) {
      console.error('Doctor dashboard load error:', err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchDoctorData();
  }, []);

  const handleAcceptRequest = async (reqId, patientName) => {
    try {
      setProcessingReqId(reqId);
      setActionAlert(null);
      await api.put(`/consultations/${reqId}/accept`);
      setActionAlert({
        type: 'success',
        message: `Accepted consultation with ${patientName}. Mutual chat and assessment access are now active.`
      });
      fetchDoctorData();
    } catch (err) {
      console.error('Accept error:', err);
      setActionAlert({
        type: 'error',
        message: err.response?.data?.detail || 'Failed to accept consultation request.'
      });
    } finally {
      setProcessingReqId(null);
    }
  };

  const handleRejectRequest = async (reqId, patientName) => {
    try {
      setProcessingReqId(reqId);
      setActionAlert(null);
      await api.put(`/consultations/${reqId}/reject`);
      setActionAlert({
        type: 'info',
        message: `Declined consultation request from ${patientName}.`
      });
      fetchDoctorData();
    } catch (err) {
      console.error('Reject error:', err);
      setActionAlert({
        type: 'error',
        message: err.response?.data?.detail || 'Failed to decline request.'
      });
    } finally {
      setProcessingReqId(null);
    }
  };

  const pendingRequests = consultationRequests.filter(r => r.relationship_status === 'pending');

  const filteredPatients = patients.filter((p) => {
    if (!searchTerm) return true;
    return (
      (p.full_name && p.full_name.toLowerCase().includes(searchTerm.toLowerCase())) ||
      (p.email && p.email.toLowerCase().includes(searchTerm.toLowerCase()))
    );
  });

  return (
    <div className="min-h-screen flex flex-col lg:flex-row bg-warm-bg w-full min-w-0 overflow-x-hidden">
      <Sidebar />

      <main className="flex-1 p-4 sm:p-6 lg:p-10 max-w-6xl w-full mx-auto space-y-8 min-w-0">
        {/* Header */}
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
          <div>
            <div className="flex items-center space-x-2">
              <span className="text-[11px] font-bold uppercase tracking-wider text-brand-800 bg-brand-50 px-2.5 py-0.5 rounded-full border border-brand-200">
                Clinical Portal
              </span>
              <span className="text-xs text-warm-muted">Doctor On Duty</span>
            </div>
            <h1 className="text-2xl font-black text-gray-900 tracking-tight mt-1">
              Physician Diagnostic Dashboard
            </h1>
            <p className="text-xs text-warm-muted mt-1">
              Review assigned patient cardiac evaluations, validate AI ensemble recommendations, and supervise treatment pathways.
            </p>
          </div>

          <div className="flex items-center space-x-2 shrink-0">
            <Link
              to="/doctor/chat"
              className="inline-flex items-center space-x-1.5 px-4 py-2 rounded-xl text-xs font-bold text-white bg-brand-800 hover:bg-brand-900 transition-all shadow-xs"
            >
              <MessageCircle className="w-3.5 h-3.5" />
              <span>Chats</span>
            </Link>
            <Link
              to="/doctor/assessments"
              className="inline-flex items-center space-x-1.5 px-4 py-2 rounded-xl text-xs font-bold text-gray-800 bg-white hover:bg-rose-50 border border-warm-border transition-all shadow-xs"
            >
              <Activity className="w-3.5 h-3.5 text-brand-800" />
              <span>Risk Assessments</span>
            </Link>
          </div>
        </div>

        {/* Action Alert Banner */}
        {actionAlert && (
          <div
            className={`p-4 rounded-2xl border text-xs font-semibold flex items-center justify-between transition-all ${
              actionAlert.type === 'success'
                ? 'bg-emerald-50 text-emerald-800 border-emerald-200'
                : actionAlert.type === 'info'
                ? 'bg-blue-50 text-blue-800 border-blue-200'
                : 'bg-red-50 text-red-800 border-red-200'
            }`}
          >
            <div className="flex items-center space-x-2">
              <CheckCircle2 className="w-4 h-4 shrink-0 text-emerald-600" />
              <span>{actionAlert.message}</span>
            </div>
            <button onClick={() => setActionAlert(null)} className="text-gray-400 hover:text-gray-700">
              ✕
            </button>
          </div>
        )}

        {/* 4 Metric Stats Cards */}
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
          {/* Card 1 */}
          <div className="bg-white p-5 rounded-3xl border border-warm-border shadow-xs space-y-3">
            <div className="flex items-center justify-between text-warm-muted">
              <span className="text-xs font-bold text-gray-700">Assigned Patients</span>
              <div className="w-8 h-8 rounded-xl bg-blue-50 text-blue-700 flex items-center justify-center">
                <Users className="w-4 h-4" />
              </div>
            </div>
            <div className="text-2xl font-black text-gray-900">{stats.total_patients || 0}</div>
            <p className="text-[11px] text-warm-muted">Under your clinical supervision</p>
          </div>

          {/* Card 2 */}
          <div className="bg-white p-5 rounded-3xl border border-warm-border shadow-xs space-y-3">
            <div className="flex items-center justify-between text-warm-muted">
              <span className="text-xs font-bold text-gray-700">Pending Requests</span>
              <div className="w-8 h-8 rounded-xl bg-amber-50 text-amber-700 flex items-center justify-center">
                <Clock className="w-4 h-4" />
              </div>
            </div>
            <div className="text-2xl font-black text-amber-600">{pendingRequests.length}</div>
            <Link to="/doctor/requests" className="text-[11px] font-semibold text-brand-800 hover:underline block">
              Manage incoming requests →
            </Link>
          </div>

          {/* Card 3 */}
          <div className="bg-white p-5 rounded-3xl border border-warm-border shadow-xs space-y-3">
            <div className="flex items-center justify-between text-warm-muted">
              <span className="text-xs font-bold text-gray-700">Completed Assessments</span>
              <div className="w-8 h-8 rounded-xl bg-emerald-50 text-emerald-700 flex items-center justify-center">
                <CheckCircle2 className="w-4 h-4" />
              </div>
            </div>
            <div className="text-2xl font-black text-gray-900">{stats.completed_assessments || 0}</div>
            <Link to="/doctor/assessments" className="text-[11px] font-semibold text-brand-800 hover:underline block">
              Review evaluations →
            </Link>
          </div>

          {/* Card 4 */}
          <div className="bg-white p-5 rounded-3xl border border-warm-border shadow-xs space-y-3">
            <div className="flex items-center justify-between text-warm-muted">
              <span className="text-xs font-bold text-gray-700">High Risk Alerts</span>
              <div className="w-8 h-8 rounded-xl bg-red-50 text-red-600 flex items-center justify-center">
                <AlertTriangle className="w-4 h-4" />
              </div>
            </div>
            <div className="text-2xl font-black text-red-600">
              {stats.high_risk_patients !== null ? stats.high_risk_patients : '0'}
            </div>
            <p className="text-[11px] text-warm-muted">Elevated cardiovascular risk</p>
          </div>
        </div>

        {/* Feature 2: Incoming Patient Consultation Requests Section */}
        {pendingRequests.length > 0 && (
          <div className="bg-white rounded-3xl border-2 border-amber-200/80 shadow-xs p-6 space-y-4 bg-amber-50/20">
            <div className="flex items-center justify-between">
              <div className="flex items-center space-x-2">
                <div className="w-8 h-8 rounded-xl bg-amber-100 text-amber-800 flex items-center justify-center">
                  <UserCheck className="w-4 h-4" />
                </div>
                <div>
                  <h3 className="text-sm font-bold text-gray-900">
                    Incoming Patient Consultation Requests
                  </h3>
                  <p className="text-xs text-warm-muted">
                    New patients requesting cardiovascular consultation with you
                  </p>
                </div>
              </div>

              <Link
                to="/doctor/requests"
                className="text-xs font-bold text-brand-800 hover:underline"
              >
                View All ({pendingRequests.length}) →
              </Link>
            </div>

            <div className="divide-y divide-warm-border/80">
              {pendingRequests.slice(0, 3).map((req) => (
                <div key={req.id} className="py-3 flex flex-col sm:flex-row items-start sm:items-center justify-between gap-3 text-xs">
                  <div>
                    <div className="flex items-center space-x-2">
                      <span className="font-bold text-gray-900">{req.patient_name}</span>
                      <span className="text-[10px] text-warm-muted font-mono">({req.patient_email})</span>
                      <span className="text-[10px] px-2 py-0.5 rounded-full bg-amber-100 text-amber-800 font-semibold">
                        Pending
                      </span>
                    </div>
                    {req.notes && (
                      <p className="text-warm-muted text-[11px] italic mt-0.5 line-clamp-1">
                        "{req.notes}"
                      </p>
                    )}
                  </div>

                  <div className="flex items-center space-x-2 shrink-0">
                    <button
                      onClick={() => handleAcceptRequest(req.id, req.patient_name)}
                      disabled={processingReqId === req.id}
                      className="px-3 py-1.5 rounded-lg text-xs font-bold text-white bg-emerald-700 hover:bg-emerald-800 transition-all shadow-2xs disabled:opacity-50"
                    >
                      Accept
                    </button>
                    <button
                      onClick={() => handleRejectRequest(req.id, req.patient_name)}
                      disabled={processingReqId === req.id}
                      className="px-3 py-1.5 rounded-lg text-xs font-bold text-red-700 bg-red-50 hover:bg-red-100 border border-red-200 transition-all disabled:opacity-50"
                    >
                      Decline
                    </button>
                  </div>
                </div>
              ))}
            </div>
          </div>
        )}

        {/* Assigned Patients Table */}
        <div className="bg-white rounded-3xl border border-warm-border shadow-xs overflow-hidden">
          <div className="p-6 border-b border-warm-border flex flex-col sm:flex-row sm:items-center justify-between gap-4">
            <div>
              <h3 className="text-sm font-bold text-gray-900">Assigned Patient Roster</h3>
              <p className="text-xs text-warm-muted">Patients requiring ongoing cardiac tracking</p>
            </div>
            <div className="relative w-full sm:w-64">
              <Search className="w-4 h-4 text-warm-muted absolute left-3 top-1/2 -translate-y-1/2" />
              <input
                type="text"
                placeholder="Search patient name..."
                value={searchTerm}
                onChange={(e) => setSearchTerm(e.target.value)}
                className="w-full pl-9 pr-3 py-1.5 bg-warm-bg border border-warm-border rounded-xl text-xs text-gray-900 focus:outline-none focus:border-brand-800"
              />
            </div>
          </div>

          {loading ? (
            <div className="p-12 text-center">
              <div className="w-8 h-8 border-3 border-brand-800 border-t-transparent rounded-full animate-spin mx-auto mb-3" />
              <p className="text-xs text-warm-muted">Loading patient records...</p>
            </div>
          ) : filteredPatients.length === 0 ? (
            <div className="p-12 text-center space-y-2">
              <UserCheck className="w-10 h-10 text-warm-muted mx-auto" />
              <p className="text-xs font-bold text-gray-800">No Assigned Patients</p>
              <p className="text-[11px] text-warm-muted">
                Patients assigned to you or approved from consultation requests will appear here.
              </p>
            </div>
          ) : (
            <div className="overflow-x-auto">
              <table className="w-full text-left text-xs">
                <thead className="bg-warm-bg text-warm-muted uppercase tracking-wider text-[10px] font-bold border-b border-warm-border">
                  <tr>
                    <th className="py-4 px-6">Patient Name</th>
                    <th className="py-4 px-6">Gender</th>
                    <th className="py-4 px-6">Contact / Email</th>
                    <th className="py-4 px-6">Date of Birth</th>
                    <th className="py-4 px-6 text-right">Actions</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-warm-border">
                  {filteredPatients.map((pt) => (
                    <tr key={pt.patient_id} className="hover:bg-rose-50/20 transition-colors">
                      <td className="py-4 px-6 font-semibold text-gray-900">
                        {pt.full_name || 'Patient'}
                      </td>
                      <td className="py-4 px-6 capitalize text-warm-muted">
                        {pt.gender || 'Not specified'}
                      </td>
                      <td className="py-4 px-6 text-warm-muted font-mono">
                        {pt.email || pt.phone || '—'}
                      </td>
                      <td className="py-4 px-6 text-warm-muted">
                        {pt.date_of_birth ? new Date(pt.date_of_birth).toLocaleDateString() : '—'}
                      </td>
                      <td className="py-4 px-6 text-right space-x-2">
                        <Link
                          to="/doctor/chat"
                          className="inline-flex items-center space-x-1 px-2.5 py-1.5 rounded-lg text-xs font-semibold text-gray-700 bg-warm-bg hover:bg-gray-100 border border-warm-border transition-all"
                        >
                          <MessageCircle className="w-3.5 h-3.5 text-brand-800" />
                          <span>Chat</span>
                        </Link>
                        <Link
                          to={`/doctor/patient/${pt.patient_id}`}
                          className="inline-flex items-center space-x-1.5 px-3 py-1.5 rounded-lg text-xs font-bold text-white bg-brand-800 hover:bg-brand-900 transition-all shadow-xs"
                        >
                          <span>Review File</span>
                          <ArrowRight className="w-3.5 h-3.5" />
                        </Link>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </div>

        {/* Recent Assessments Feed */}
        <div className="bg-white rounded-3xl border border-warm-border shadow-xs p-6 space-y-4">
          <div className="flex items-center justify-between">
            <h3 className="text-sm font-bold text-gray-900">Recent Patient Assessments</h3>
            <Link to="/doctor/assessments" className="text-xs font-bold text-brand-800 hover:underline">
              View All Assessments →
            </Link>
          </div>

          {recentAssessments.length === 0 ? (
            <p className="text-xs text-warm-muted">No assessment found</p>
          ) : (
            <div className="divide-y divide-warm-border">
              {recentAssessments.map((ra) => (
                <div key={ra.assessment_id} className="py-3 flex items-center justify-between text-xs">
                  <div>
                    <span className="font-bold text-gray-900">{ra.patient_name}</span>
                    <span className="text-warm-muted text-[11px] ml-2">
                      ({new Date(ra.created_at).toLocaleDateString()})
                    </span>
                  </div>
                  <div className="flex items-center space-x-3">
                    <span className="px-2 py-0.5 rounded-full text-[10px] font-bold bg-warm-bg border border-warm-border text-gray-700 capitalize">
                      {ra.assessment_status || 'Pending'}
                    </span>
                    <Link
                      to={`/doctor/patient/${ra.patient_id}`}
                      className="text-xs font-bold text-brand-800 hover:underline"
                    >
                      Inspect
                    </Link>
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>
      </main>
    </div>
  );
}
