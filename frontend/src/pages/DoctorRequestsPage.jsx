import React, { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import {
  Users,
  CheckCircle2,
  XCircle,
  Clock,
  Search,
  MessageCircle,
  Activity,
  AlertCircle,
  UserCheck,
  Calendar,
  Phone,
  Mail,
  Shield,
  FileText
} from 'lucide-react';
import Sidebar from '../components/Sidebar';
import api from '../api/client';

export default function DoctorRequestsPage() {
  const [requests, setRequests] = useState([]);
  const [loading, setLoading] = useState(true);
  const [activeTab, setActiveTab] = useState('pending'); // 'pending', 'approved', 'all'
  const [searchTerm, setSearchTerm] = useState('');
  const [processingId, setProcessingId] = useState(null);
  const [alert, setAlert] = useState(null);

  const fetchRequests = async () => {
    try {
      setLoading(true);
      const res = await api.get('/consultations/doctor-requests');
      setRequests(res.data || []);
    } catch (err) {
      console.error('Error fetching consultation requests:', err);
      setAlert({
        type: 'error',
        message: 'Failed to load consultation requests.'
      });
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchRequests();
  }, []);

  const handleAccept = async (reqId, patientName) => {
    try {
      setProcessingId(reqId);
      setAlert(null);
      await api.put(`/consultations/${reqId}/accept`);
      setAlert({
        type: 'success',
        message: `Consultation request from ${patientName} accepted. Chat and assessment access are now enabled.`
      });
      fetchRequests();
    } catch (err) {
      console.error('Error accepting request:', err);
      setAlert({
        type: 'error',
        message: err.response?.data?.detail || 'Failed to accept consultation request.'
      });
    } finally {
      setProcessingId(null);
    }
  };

  const handleReject = async (reqId, patientName) => {
    if (!window.confirm(`Are you sure you want to decline the consultation request from ${patientName}?`)) {
      return;
    }
    try {
      setProcessingId(reqId);
      setAlert(null);
      await api.put(`/consultations/${reqId}/reject`);
      setAlert({
        type: 'info',
        message: `Consultation request from ${patientName} was declined.`
      });
      fetchRequests();
    } catch (err) {
      console.error('Error rejecting request:', err);
      setAlert({
        type: 'error',
        message: err.response?.data?.detail || 'Failed to decline consultation request.'
      });
    } finally {
      setProcessingId(null);
    }
  };

  const pendingRequests = requests.filter(r => r.relationship_status === 'pending');
  const approvedRequests = requests.filter(r => r.relationship_status === 'approved');

  const displayedRequests = requests.filter(req => {
    const matchesTab =
      activeTab === 'all' ||
      (activeTab === 'pending' && req.relationship_status === 'pending') ||
      (activeTab === 'approved' && req.relationship_status === 'approved');

    const matchesSearch =
      (req.patient_name && req.patient_name.toLowerCase().includes(searchTerm.toLowerCase())) ||
      (req.patient_email && req.patient_email.toLowerCase().includes(searchTerm.toLowerCase())) ||
      (req.patient_phone && req.patient_phone.includes(searchTerm));

    return matchesTab && matchesSearch;
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
                Patient Intake
              </span>
              <span className="text-xs text-warm-muted">Clinical Consultations</span>
            </div>
            <h1 className="text-2xl sm:text-3xl font-black text-gray-900 tracking-tight">
              Patient Consultation Requests
            </h1>
            <p className="text-xs sm:text-sm text-warm-muted">
              Review and manage patient consultation requests. Accepting a request enables mutual communication and clinical evaluation review.
            </p>
          </div>

          <div className="flex items-center space-x-3 shrink-0">
            <Link
              to="/doctor/chat"
              className="inline-flex items-center space-x-2 px-5 py-2.5 rounded-full bg-brand-800 text-white font-bold text-xs hover:bg-brand-900 shadow-sm transition-all"
            >
              <MessageCircle className="w-4 h-4" />
              <span>Open Chats</span>
            </Link>
          </div>
        </div>

        {/* Alert Notification */}
        {alert && (
          <div
            className={`p-4 rounded-2xl border text-xs font-semibold flex items-center justify-between transition-all ${
              alert.type === 'success'
                ? 'bg-emerald-50 text-emerald-800 border-emerald-200'
                : alert.type === 'info'
                ? 'bg-blue-50 text-blue-800 border-blue-200'
                : 'bg-red-50 text-red-800 border-red-200'
            }`}
          >
            <div className="flex items-center space-x-2">
              {alert.type === 'success' ? (
                <CheckCircle2 className="w-5 h-5 text-emerald-600 shrink-0" />
              ) : (
                <AlertCircle className="w-5 h-5 text-brand-800 shrink-0" />
              )}
              <span>{alert.message}</span>
            </div>
            <button onClick={() => setAlert(null)} className="text-gray-400 hover:text-gray-700">
              ✕
            </button>
          </div>
        )}

        {/* Tabs and Search Controls */}
        <div className="bg-white p-4 sm:p-5 rounded-2xl border border-warm-border shadow-xs flex flex-col md:flex-row gap-4 items-center justify-between">
          <div className="flex items-center space-x-2 w-full md:w-auto">
            <button
              onClick={() => setActiveTab('pending')}
              className={`px-4 py-2 rounded-xl text-xs font-bold transition-all flex items-center space-x-2 ${
                activeTab === 'pending'
                  ? 'bg-brand-800 text-white shadow-xs'
                  : 'bg-warm-bg text-gray-600 hover:bg-rose-50/50 border border-warm-border'
              }`}
            >
              <span>Pending Requests</span>
              <span className={`px-1.5 py-0.5 rounded-full text-[10px] ${
                activeTab === 'pending' ? 'bg-white/20 text-white' : 'bg-amber-100 text-amber-800'
              }`}>
                {pendingRequests.length}
              </span>
            </button>

            <button
              onClick={() => setActiveTab('approved')}
              className={`px-4 py-2 rounded-xl text-xs font-bold transition-all flex items-center space-x-2 ${
                activeTab === 'approved'
                  ? 'bg-brand-800 text-white shadow-xs'
                  : 'bg-warm-bg text-gray-600 hover:bg-rose-50/50 border border-warm-border'
              }`}
            >
              <span>Approved Patients</span>
              <span className={`px-1.5 py-0.5 rounded-full text-[10px] ${
                activeTab === 'approved' ? 'bg-white/20 text-white' : 'bg-emerald-100 text-emerald-800'
              }`}>
                {approvedRequests.length}
              </span>
            </button>

            <button
              onClick={() => setActiveTab('all')}
              className={`px-4 py-2 rounded-xl text-xs font-bold transition-all ${
                activeTab === 'all'
                  ? 'bg-brand-800 text-white shadow-xs'
                  : 'bg-warm-bg text-gray-600 hover:bg-rose-50/50 border border-warm-border'
              }`}
            >
              All Requests ({requests.length})
            </button>
          </div>

          <div className="relative w-full md:w-72">
            <Search className="w-4 h-4 text-warm-muted absolute left-3 top-1/2 -translate-y-1/2" />
            <input
              type="text"
              placeholder="Search by patient name, email..."
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
              className="w-full pl-9 pr-4 py-2 bg-warm-bg border border-warm-border rounded-xl text-xs text-gray-900 focus:outline-none focus:border-brand-800"
            />
          </div>
        </div>

        {/* Requests List */}
        {loading ? (
          <div className="p-16 text-center bg-white rounded-3xl border border-warm-border">
            <div className="w-10 h-10 border-3 border-brand-800 border-t-transparent rounded-full animate-spin mx-auto mb-3" />
            <p className="text-xs font-semibold text-warm-muted">Loading consultation requests...</p>
          </div>
        ) : displayedRequests.length === 0 ? (
          <div className="p-16 text-center bg-white rounded-3xl border border-warm-border space-y-3">
            <UserCheck className="w-12 h-12 text-warm-muted mx-auto" />
            <h3 className="text-sm font-bold text-gray-800">
              {activeTab === 'pending'
                ? 'No Pending Requests'
                : activeTab === 'approved'
                ? 'No Approved Patients Yet'
                : 'No Requests Found'}
            </h3>
            <p className="text-xs text-warm-muted max-w-sm mx-auto">
              {activeTab === 'pending'
                ? 'New consultation requests from patients will appear here for your review and approval.'
                : 'Patients you approve will appear here with active communication links.'}
            </p>
          </div>
        ) : (
          <div className="space-y-4">
            {displayedRequests.map((req) => {
              const isPending = req.relationship_status === 'pending';
              const isApproved = req.relationship_status === 'approved';
              const isProcessing = processingId === req.id;

              return (
                <div
                  key={req.id}
                  className="bg-white rounded-3xl border border-warm-border shadow-xs p-6 flex flex-col md:flex-row items-start md:items-center justify-between gap-6 hover:border-brand-300 transition-all"
                >
                  {/* Left: Patient Profile & Details */}
                  <div className="space-y-3 flex-1">
                    <div className="flex items-center space-x-3">
                      <div className="w-12 h-12 rounded-2xl bg-rose-50 border border-rose-100 flex items-center justify-center text-brand-800 font-black text-lg shrink-0">
                        {req.patient_name ? req.patient_name.charAt(0) : 'P'}
                      </div>
                      <div>
                        <div className="flex items-center space-x-2">
                          <h3 className="text-base font-bold text-gray-900 tracking-tight">
                            {req.patient_name}
                          </h3>
                          <span className={`px-2.5 py-0.5 rounded-full text-[10px] font-bold uppercase tracking-wider ${
                            isApproved
                              ? 'bg-emerald-50 text-emerald-700 border border-emerald-200'
                              : isPending
                              ? 'bg-amber-50 text-amber-700 border border-amber-200'
                              : 'bg-gray-100 text-gray-600 border border-gray-200'
                          }`}>
                            {req.relationship_status}
                          </span>
                        </div>
                        <p className="text-xs text-warm-muted font-mono mt-0.5">
                          {req.patient_email} {req.patient_phone && `• ${req.patient_phone}`}
                        </p>
                      </div>
                    </div>

                    {/* Metadata Grid */}
                    <div className="grid grid-cols-2 sm:grid-cols-4 gap-3 pt-2 text-xs text-warm-muted border-t border-warm-border">
                      <div>
                        <span className="block text-[10px] uppercase font-bold text-gray-400">Gender</span>
                        <span className="font-semibold text-gray-800 capitalize">{req.patient_gender || 'Not specified'}</span>
                      </div>
                      <div>
                        <span className="block text-[10px] uppercase font-bold text-gray-400">Date of Birth</span>
                        <span className="font-semibold text-gray-800">
                          {req.patient_dob ? new Date(req.patient_dob).toLocaleDateString() : '—'}
                        </span>
                      </div>
                      <div>
                        <span className="block text-[10px] uppercase font-bold text-gray-400">Emergency Contact</span>
                        <span className="font-semibold text-gray-800 truncate block">
                          {req.patient_emergency_contact || 'None listed'}
                        </span>
                      </div>
                      <div>
                        <span className="block text-[10px] uppercase font-bold text-gray-400">Requested On</span>
                        <span className="font-semibold text-gray-800">
                          {req.created_at ? new Date(req.created_at).toLocaleDateString('en-GB', { day: 'numeric', month: 'short', year: 'numeric' }) : 'Recent'}
                        </span>
                      </div>
                    </div>

                    {req.notes && (
                      <div className="p-3 bg-warm-bg rounded-xl border border-warm-border text-xs text-gray-700">
                        <span className="font-bold text-gray-900 mr-1.5">Patient Note:</span>
                        <span>"{req.notes}"</span>
                      </div>
                    )}
                  </div>

                  {/* Right Action Buttons */}
                  <div className="flex flex-row md:flex-col items-center justify-end gap-2 w-full md:w-48 shrink-0 pt-4 md:pt-0 border-t md:border-t-0 border-warm-border">
                    {isPending ? (
                      <>
                        <button
                          onClick={() => handleAccept(req.id, req.patient_name)}
                          disabled={isProcessing}
                          className="flex-1 md:w-full inline-flex items-center justify-center space-x-1.5 px-4 py-2.5 rounded-xl text-xs font-bold text-white bg-emerald-700 hover:bg-emerald-800 transition-all shadow-xs disabled:opacity-50"
                        >
                          <CheckCircle2 className="w-3.5 h-3.5" />
                          <span>Accept Request</span>
                        </button>
                        <button
                          onClick={() => handleReject(req.id, req.patient_name)}
                          disabled={isProcessing}
                          className="flex-1 md:w-full inline-flex items-center justify-center space-x-1.5 px-4 py-2.5 rounded-xl text-xs font-bold text-red-700 bg-red-50 hover:bg-red-100 border border-red-200 transition-all disabled:opacity-50"
                        >
                          <XCircle className="w-3.5 h-3.5" />
                          <span>Decline</span>
                        </button>
                      </>
                    ) : isApproved ? (
                      <>
                        <Link
                          to="/doctor/chat"
                          className="flex-1 md:w-full inline-flex items-center justify-center space-x-1.5 px-4 py-2.5 rounded-xl text-xs font-bold text-white bg-brand-800 hover:bg-brand-900 transition-all shadow-xs"
                        >
                          <MessageCircle className="w-3.5 h-3.5" />
                          <span>Open Chat</span>
                        </Link>
                        <Link
                          to={`/doctor/patient/${req.patient_id}`}
                          className="flex-1 md:w-full inline-flex items-center justify-center space-x-1.5 px-4 py-2 rounded-xl text-xs font-semibold text-gray-700 bg-warm-bg hover:bg-rose-50 border border-warm-border transition-all"
                        >
                          <Activity className="w-3.5 h-3.5" />
                          <span>View Records</span>
                        </Link>
                      </>
                    ) : (
                      <span className="text-xs font-semibold text-gray-500 italic">
                        Request Declined
                      </span>
                    )}
                  </div>
                </div>
              );
            })}
          </div>
        )}
      </main>
    </div>
  );
}
