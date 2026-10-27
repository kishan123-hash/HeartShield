import React, { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import {
  UserCheck,
  CheckCircle2,
  XCircle,
  AlertCircle,
  Clock,
  ArrowLeft,
  Building,
  Award,
  Stethoscope,
  KeyRound,
  X
} from 'lucide-react';
import Sidebar from '../components/Sidebar';
import api from '../api/client';

export default function DoctorApprovalsPage() {
  const [activeTab, setActiveTab] = useState('registrations'); // 'registrations' or 'password_resets'
  const [approvals, setApprovals] = useState([]);
  const [passwordResets, setPasswordResets] = useState([]);
  const [loading, setLoading] = useState(true);
  const [actionLoading, setActionLoading] = useState(null);
  const [feedback, setFeedback] = useState({ type: '', text: '' });

  const fetchData = async () => {
    setLoading(true);
    try {
      const [appRes, resetRes] = await Promise.all([
        api.get('/admin/approvals'),
        api.get('/admin/doctor-password-resets'),
      ]);
      setApprovals(appRes.data?.approvals || []);
      setPasswordResets(resetRes.data?.requests || []);
    } catch (err) {
      console.error('Error fetching admin data:', err);
      setFeedback({ type: 'error', text: 'Failed to load administrator verification data.' });
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchData();
  }, []);

  const handleApproveDoctor = async (doctorId) => {
    setActionLoading(`doc-${doctorId}`);
    setFeedback({ type: '', text: '' });
    try {
      await api.put(`/admin/doctors/${doctorId}/approve`);
      setFeedback({ type: 'success', text: `Doctor #${doctorId} has been verified and approved.` });
      setApprovals((prev) => prev.filter((d) => d.doctor_id !== doctorId));
    } catch (err) {
      console.error('Approve doctor error:', err);
      setFeedback({ type: 'error', text: 'Failed to approve doctor verification.' });
    } finally {
      setActionLoading(null);
    }
  };

  const handleRejectDoctor = async (userId) => {
    if (!window.confirm('Reject this physician application?')) return;
    setActionLoading(`doc-user-${userId}`);
    setFeedback({ type: '', text: '' });
    try {
      await api.put(`/admin/users/${userId}/reject`);
      setFeedback({ type: 'success', text: 'Physician application has been rejected.' });
      setApprovals((prev) => prev.filter((d) => d.user_id !== userId));
    } catch (err) {
      console.error('Reject doctor error:', err);
      setFeedback({ type: 'error', text: 'Failed to reject application.' });
    } finally {
      setActionLoading(null);
    }
  };

  const handleApproveReset = async (requestId) => {
    setActionLoading(`reset-${requestId}`);
    setFeedback({ type: '', text: '' });
    try {
      await api.put(`/admin/doctor-password-resets/${requestId}/approve`);
      setFeedback({ type: 'success', text: `Password reset request #${requestId} has been approved.` });
      setPasswordResets((prev) =>
        prev.map((r) => (r.request_id === requestId ? { ...r, status: 'approved' } : r))
      );
    } catch (err) {
      console.error('Approve reset error:', err);
      const detail = err.response?.data?.detail;
      setFeedback({ type: 'error', text: typeof detail === 'string' ? detail : 'Failed to approve reset request.' });
    } finally {
      setActionLoading(null);
    }
  };

  const handleRejectReset = async (requestId) => {
    if (!window.confirm('Reject this physician password reset request?')) return;
    setActionLoading(`reset-${requestId}`);
    setFeedback({ type: '', text: '' });
    try {
      await api.put(`/admin/doctor-password-resets/${requestId}/reject`);
      setFeedback({ type: 'success', text: `Password reset request #${requestId} has been rejected.` });
      setPasswordResets((prev) =>
        prev.map((r) => (r.request_id === requestId ? { ...r, status: 'rejected' } : r))
      );
    } catch (err) {
      console.error('Reject reset error:', err);
      const detail = err.response?.data?.detail;
      setFeedback({ type: 'error', text: typeof detail === 'string' ? detail : 'Failed to reject reset request.' });
    } finally {
      setActionLoading(null);
    }
  };

  const pendingResetsCount = passwordResets.filter((r) => r.status === 'pending').length;

  return (
    <div className="min-h-screen flex flex-col lg:flex-row bg-warm-bg w-full min-w-0 overflow-x-hidden">
      <Sidebar />

      <main className="flex-1 p-4 sm:p-6 lg:p-10 max-w-6xl w-full mx-auto space-y-8 min-w-0">
        {/* Header */}
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
          <div className="flex items-center space-x-3">
            <Link
              to="/admin/dashboard"
              className="p-2 rounded-xl bg-white border border-warm-border text-warm-muted hover:text-brand-800 transition-all"
            >
              <ArrowLeft className="w-5 h-5" />
            </Link>
            <div>
              <span className="text-[11px] font-bold uppercase tracking-wider text-brand-800 bg-brand-50 px-2.5 py-0.5 rounded-full border border-brand-200">
                Administrative Governance
              </span>
              <h1 className="text-2xl font-black text-gray-900 tracking-tight mt-1">
                Physician Credentials & Authorization
              </h1>
            </div>
          </div>

          {/* Navigation Tabs */}
          <div className="flex p-1 bg-white rounded-2xl border border-warm-border">
            <button
              onClick={() => setActiveTab('registrations')}
              className={`px-4 py-2 rounded-xl text-xs font-bold transition-all ${
                activeTab === 'registrations'
                  ? 'bg-brand-800 text-white shadow-xs'
                  : 'text-gray-600 hover:text-brand-800'
              }`}
            >
              Licensure Approvals ({approvals.length})
            </button>
            <button
              onClick={() => setActiveTab('password_resets')}
              className={`px-4 py-2 rounded-xl text-xs font-bold transition-all flex items-center space-x-1.5 ${
                activeTab === 'password_resets'
                  ? 'bg-brand-800 text-white shadow-xs'
                  : 'text-gray-600 hover:text-brand-800'
              }`}
            >
              <span>Password Resets</span>
              {pendingResetsCount > 0 && (
                <span className="px-1.5 py-0.2 rounded-full text-[10px] bg-amber-200 text-amber-900 font-bold">
                  {pendingResetsCount}
                </span>
              )}
            </button>
          </div>
        </div>

        {/* Feedback Alert */}
        {feedback.text && (
          <div
            className={`p-4 rounded-2xl border flex items-center justify-between text-xs ${
              feedback.type === 'success'
                ? 'bg-emerald-50 text-emerald-700 border-emerald-200'
                : 'bg-red-50 text-red-700 border-red-200'
            }`}
          >
            <div className="flex items-center space-x-2">
              {feedback.type === 'success' ? (
                <CheckCircle2 className="w-4 h-4 shrink-0" />
              ) : (
                <AlertCircle className="w-4 h-4 shrink-0" />
              )}
              <span>{feedback.text}</span>
            </div>
            <button onClick={() => setFeedback({ type: '', text: '' })}>
              <X className="w-4 h-4" />
            </button>
          </div>
        )}

        {/* Tab 1: Physician Registrations */}
        {activeTab === 'registrations' && (
          <div className="bg-white rounded-3xl border border-warm-border shadow-xs overflow-hidden">
            <div className="p-6 border-b border-warm-border flex items-center justify-between">
              <h3 className="text-sm font-bold text-gray-900">Pending Physician Licensure Applications</h3>
              <span className="text-xs text-warm-muted">{approvals.length} pending verification</span>
            </div>

            {loading ? (
              <div className="p-12 text-center">
                <div className="w-8 h-8 border-3 border-brand-800 border-t-transparent rounded-full animate-spin mx-auto mb-3" />
                <p className="text-xs text-warm-muted">Loading pending doctor credentials...</p>
              </div>
            ) : approvals.length === 0 ? (
              <div className="p-12 text-center space-y-3">
                <div className="w-12 h-12 bg-emerald-50 text-emerald-700 rounded-full flex items-center justify-center mx-auto">
                  <CheckCircle2 className="w-6 h-6" />
                </div>
                <p className="text-xs font-bold text-gray-900">All Physician Verifications Up to Date</p>
                <p className="text-[11px] text-warm-muted">
                  There are no pending doctor registration applications awaiting administrator review.
                </p>
              </div>
            ) : (
              <div className="overflow-x-auto">
                <table className="w-full text-left text-xs">
                  <thead className="bg-warm-bg text-warm-muted uppercase tracking-wider text-[10px] font-bold border-b border-warm-border">
                    <tr>
                      <th className="py-4 px-6">Physician Details</th>
                      <th className="py-4 px-6">Medical License</th>
                      <th className="py-4 px-6">Specialty & Experience</th>
                      <th className="py-4 px-6">Hospital Affiliation</th>
                      <th className="py-4 px-6 text-right">Actions</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-warm-border">
                    {approvals.map((doc) => (
                      <tr key={doc.doctor_id} className="hover:bg-rose-50/20 transition-colors">
                        <td className="py-4 px-6">
                          <div className="space-y-0.5">
                            <span className="font-bold text-gray-900 block">{doc.full_name}</span>
                            <span className="text-warm-muted text-[11px] font-mono">{doc.email}</span>
                            {doc.phone && <span className="text-warm-muted text-[11px] block">{doc.phone}</span>}
                          </div>
                        </td>

                        <td className="py-4 px-6">
                          <span className="font-mono text-xs font-bold text-brand-800 bg-brand-50 px-2.5 py-1 rounded-lg border border-brand-200">
                            {doc.medical_license_number || 'N/A'}
                          </span>
                        </td>

                        <td className="py-4 px-6">
                          <div className="space-y-0.5">
                            <span className="font-semibold text-gray-800 block">
                              {doc.specialization || 'Cardiology'}
                            </span>
                            <span className="text-[11px] text-warm-muted">
                              {doc.years_of_experience ? `${doc.years_of_experience} years clinical practice` : '—'}
                            </span>
                          </div>
                        </td>

                        <td className="py-4 px-6">
                          <div className="space-y-0.5">
                            <span className="font-semibold text-gray-800 block">
                              {doc.hospital_name || 'Hospital Not Listed'}
                            </span>
                            {doc.hospital_address && (
                              <span className="text-[11px] text-warm-muted block truncate max-w-xs">
                                {doc.hospital_address}
                              </span>
                            )}
                          </div>
                        </td>

                        <td className="py-4 px-6 text-right">
                          <div className="flex items-center justify-end space-x-2">
                            <button
                              onClick={() => handleApproveDoctor(doc.doctor_id)}
                              disabled={actionLoading === `doc-${doc.doctor_id}`}
                              className="inline-flex items-center space-x-1.5 px-3 py-1.5 rounded-lg text-xs font-bold text-white bg-emerald-600 hover:bg-emerald-700 transition-all shadow-xs disabled:opacity-50"
                            >
                              <CheckCircle2 className="w-3.5 h-3.5" />
                              <span>Approve</span>
                            </button>
                            <button
                              onClick={() => handleRejectDoctor(doc.user_id)}
                              disabled={actionLoading === `doc-user-${doc.user_id}`}
                              className="inline-flex items-center space-x-1.5 px-3 py-1.5 rounded-lg text-xs font-bold text-red-700 bg-red-50 hover:bg-red-100 border border-red-200 transition-all disabled:opacity-50"
                            >
                              <XCircle className="w-3.5 h-3.5" />
                              <span>Reject</span>
                            </button>
                          </div>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            )}
          </div>
        )}

        {/* Tab 2: Doctor Password Reset Requests */}
        {activeTab === 'password_resets' && (
          <div className="bg-white rounded-3xl border border-warm-border shadow-xs overflow-hidden">
            <div className="p-6 border-b border-warm-border flex items-center justify-between">
              <div>
                <h3 className="text-sm font-bold text-gray-900">Physician Password Recovery Requests</h3>
                <p className="text-xs text-warm-muted">Strict administrator approval required before OTP verification.</p>
              </div>
              <span className="text-xs font-bold text-amber-900 bg-amber-50 border border-amber-200 px-2.5 py-1 rounded-full">
                {pendingResetsCount} pending approval
              </span>
            </div>

            {loading ? (
              <div className="p-12 text-center">
                <div className="w-8 h-8 border-3 border-brand-800 border-t-transparent rounded-full animate-spin mx-auto mb-3" />
                <p className="text-xs text-warm-muted">Loading reset requests...</p>
              </div>
            ) : passwordResets.length === 0 ? (
              <div className="p-12 text-center space-y-3">
                <div className="w-12 h-12 bg-emerald-50 text-emerald-700 rounded-full flex items-center justify-center mx-auto">
                  <CheckCircle2 className="w-6 h-6" />
                </div>
                <p className="text-xs font-bold text-gray-900">No Password Reset Requests</p>
                <p className="text-[11px] text-warm-muted">
                  There are currently no doctor password recovery requests awaiting approval.
                </p>
              </div>
            ) : (
              <div className="overflow-x-auto">
                <table className="w-full text-left text-xs">
                  <thead className="bg-warm-bg text-warm-muted uppercase tracking-wider text-[10px] font-bold border-b border-warm-border">
                    <tr>
                      <th className="py-4 px-6">Doctor Details</th>
                      <th className="py-4 px-6">Clinical Affiliation</th>
                      <th className="py-4 px-6">Requested At</th>
                      <th className="py-4 px-6">Status</th>
                      <th className="py-4 px-6 text-right">Admin Action</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-warm-border">
                    {passwordResets.map((req) => (
                      <tr key={req.request_id} className="hover:bg-rose-50/20 transition-colors">
                        <td className="py-4 px-6">
                          <div className="space-y-0.5">
                            <span className="font-bold text-gray-900 block">{req.full_name}</span>
                            <span className="text-warm-muted text-[11px] font-mono">{req.email}</span>
                            {req.phone && <span className="text-warm-muted text-[11px] block">{req.phone}</span>}
                          </div>
                        </td>

                        <td className="py-4 px-6">
                          <div className="space-y-0.5">
                            <span className="font-semibold text-gray-800 block">
                              {req.hospital_name || 'Hospital Not Listed'}
                            </span>
                            <span className="text-[11px] text-warm-muted block font-mono">
                              License: {req.medical_license_number || 'N/A'}
                            </span>
                          </div>
                        </td>

                        <td className="py-4 px-6">
                          <span className="text-warm-muted text-[11px]">
                            {req.created_at ? new Date(req.created_at).toLocaleString() : '—'}
                          </span>
                        </td>

                        <td className="py-4 px-6">
                          <span
                            className={`px-2.5 py-1 rounded-full text-[10px] font-bold uppercase tracking-wider border ${
                              req.status === 'pending'
                                ? 'bg-amber-50 text-amber-800 border-amber-200'
                                : req.status === 'approved'
                                ? 'bg-emerald-50 text-emerald-800 border-emerald-200'
                                : req.status === 'completed'
                                ? 'bg-blue-50 text-blue-800 border-blue-200'
                                : 'bg-rose-50 text-rose-800 border-rose-200'
                            }`}
                          >
                            {req.status}
                          </span>
                        </td>

                        <td className="py-4 px-6 text-right">
                          {req.status === 'pending' ? (
                            <div className="flex items-center justify-end space-x-2">
                              <button
                                onClick={() => handleApproveReset(req.request_id)}
                                disabled={actionLoading === `reset-${req.request_id}`}
                                className="inline-flex items-center space-x-1.5 px-3 py-1.5 rounded-lg text-xs font-bold text-white bg-emerald-600 hover:bg-emerald-700 transition-all shadow-xs disabled:opacity-50"
                              >
                                <CheckCircle2 className="w-3.5 h-3.5" />
                                <span>Approve</span>
                              </button>
                              <button
                                onClick={() => handleRejectReset(req.request_id)}
                                disabled={actionLoading === `reset-${req.request_id}`}
                                className="inline-flex items-center space-x-1.5 px-3 py-1.5 rounded-lg text-xs font-bold text-red-700 bg-red-50 hover:bg-red-100 border border-red-200 transition-all disabled:opacity-50"
                              >
                                <XCircle className="w-3.5 h-3.5" />
                                <span>Reject</span>
                              </button>
                            </div>
                          ) : (
                            <span className="text-warm-muted text-xs italic">
                              {req.status === 'approved' ? 'Awaiting Doctor OTP' : 'Action Finalized'}
                            </span>
                          )}
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            )}
          </div>
        )}
      </main>
    </div>
  );
}
