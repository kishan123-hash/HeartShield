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
  X
} from 'lucide-react';
import Sidebar from '../components/Sidebar';
import api from '../api/client';

export default function DoctorApprovalsPage() {
  const [approvals, setApprovals] = useState([]);
  const [loading, setLoading] = useState(true);
  const [actionLoading, setActionLoading] = useState(null);
  const [feedback, setFeedback] = useState({ type: '', text: '' });

  const fetchPendingApprovals = async () => {
    setLoading(true);
    try {
      const res = await api.get('/admin/approvals');
      setApprovals(res.data?.approvals || []);
    } catch (err) {
      console.error('Error fetching doctor approvals:', err);
      setFeedback({ type: 'error', text: 'Failed to load pending doctor applications.' });
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchPendingApprovals();
  }, []);

  const handleApproveDoctor = async (doctorId) => {
    setActionLoading(doctorId);
    setFeedback({ type: '', text: '' });
    try {
      await api.put(`/admin/doctors/${doctorId}/approve`);
      setFeedback({ type: 'success', text: `Doctor #${doctorId} has been verified and approved.` });
      setApprovals(approvals.filter((d) => d.doctor_id !== doctorId));
    } catch (err) {
      console.error('Approve doctor error:', err);
      setFeedback({ type: 'error', text: 'Failed to approve doctor verification.' });
    } finally {
      setActionLoading(null);
    }
  };

  const handleRejectDoctor = async (userId) => {
    if (!window.confirm('Reject this physician application?')) return;
    setActionLoading(userId);
    setFeedback({ type: '', text: '' });
    try {
      await api.put(`/admin/users/${userId}/reject`);
      setFeedback({ type: 'success', text: 'Physician application has been rejected.' });
      setApprovals(approvals.filter((d) => d.user_id !== userId));
    } catch (err) {
      console.error('Reject doctor error:', err);
      setFeedback({ type: 'error', text: 'Failed to reject application.' });
    } finally {
      setActionLoading(null);
    }
  };

  return (
    <div className="min-h-screen flex bg-warm-bg">
      <Sidebar />

      <main className="flex-1 p-6 sm:p-10 max-w-6xl mx-auto space-y-8">
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
                Credential Verification
              </span>
              <h1 className="text-2xl font-black text-gray-900 tracking-tight mt-1">
                Physician Licensure Approvals
              </h1>
            </div>
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

        {/* Approvals Table */}
        <div className="bg-white rounded-3xl border border-warm-border shadow-xs overflow-hidden">
          <div className="p-6 border-b border-warm-border flex items-center justify-between">
            <h3 className="text-sm font-bold text-gray-900">Pending Physician Registrations</h3>
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
                            disabled={actionLoading === doc.doctor_id}
                            className="inline-flex items-center space-x-1.5 px-3 py-1.5 rounded-lg text-xs font-bold text-white bg-emerald-600 hover:bg-emerald-700 transition-all shadow-xs disabled:opacity-50"
                          >
                            <CheckCircle2 className="w-3.5 h-3.5" />
                            <span>Approve</span>
                          </button>
                          <button
                            onClick={() => handleRejectDoctor(doc.user_id)}
                            disabled={actionLoading === doc.user_id}
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
      </main>
    </div>
  );
}
