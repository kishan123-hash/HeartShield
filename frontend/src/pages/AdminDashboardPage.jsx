import React, { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import {
  ShieldAlert,
  Users,
  Stethoscope,
  Activity,
  CheckCircle2,
  Clock,
  UserCheck,
  Search,
  Settings,
  AlertCircle,
  TrendingUp,
  ArrowRight
} from 'lucide-react';
import Sidebar from '../components/Sidebar';
import api from '../api/client';

export default function AdminDashboardPage() {
  const [stats, setStats] = useState({
    total_users: 0,
    total_patients: 0,
    total_doctors: 0,
    total_assessments: 0,
    pending_doctors: 0,
    approved_doctors: 0,
  });
  const [users, setUsers] = useState([]);
  const [loading, setLoading] = useState(true);
  const [searchTerm, setSearchTerm] = useState('');
  const [filterRole, setFilterRole] = useState('ALL');

  useEffect(() => {
    const fetchAdminData = async () => {
      setLoading(true);
      try {
        // Fetch dashboard statistics
        const dashRes = await api.get('/admin/dashboard');
        if (dashRes.data?.statistics) {
          setStats(dashRes.data.statistics);
        }

        // Fetch users
        const usersRes = await api.get('/admin/users');
        setUsers(usersRes.data?.users || []);
      } catch (err) {
        console.error('Admin data load error:', err);
      } finally {
        setLoading(false);
      }
    };

    fetchAdminData();
  }, []);

  const filteredUsers = users.filter((u) => {
    if (filterRole !== 'ALL' && u.role !== filterRole) return false;
    if (!searchTerm) return true;
    const term = searchTerm.toLowerCase();
    return (
      (u.full_name && u.full_name.toLowerCase().includes(term)) ||
      (u.email && u.email.toLowerCase().includes(term))
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
                System Administration
              </span>
              <span className="text-xs text-warm-muted">Root Privileges</span>
            </div>
            <h1 className="text-2xl font-black text-gray-900 tracking-tight mt-1">
              Platform Governance Dashboard
            </h1>
            <p className="text-xs text-warm-muted mt-1">
              Supervise clinical user accounts, manage physician credentials, and monitor system-wide assessment activity.
            </p>
          </div>

          <Link
            to="/admin/approvals"
            className="inline-flex items-center space-x-2 px-5 py-2.5 rounded-full text-xs font-bold text-white bg-brand-800 hover:bg-brand-900 transition-all shadow-md shadow-brand-900/20 shrink-0"
          >
            <UserCheck className="w-4 h-4" />
            <span>Doctor Approvals ({stats.pending_doctors || 0})</span>
          </Link>
        </div>

        {/* Metric Cards Grid */}
        <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
          <div className="bg-white p-5 rounded-3xl border border-warm-border shadow-xs space-y-2">
            <span className="text-[11px] font-bold text-warm-muted uppercase tracking-wider">Total Users</span>
            <div className="text-2xl font-black text-gray-900">{stats.total_users || 0}</div>
            <p className="text-[11px] text-warm-muted">Active accounts registered</p>
          </div>

          <div className="bg-white p-5 rounded-3xl border border-warm-border shadow-xs space-y-2">
            <span className="text-[11px] font-bold text-warm-muted uppercase tracking-wider">Patients</span>
            <div className="text-2xl font-black text-brand-800">{stats.total_patients || 0}</div>
            <p className="text-[11px] text-warm-muted">Undergoing health evaluations</p>
          </div>

          <div className="bg-white p-5 rounded-3xl border border-warm-border shadow-xs space-y-2">
            <span className="text-[11px] font-bold text-warm-muted uppercase tracking-wider">Physicians</span>
            <div className="text-2xl font-black text-emerald-700">{stats.total_doctors || 0}</div>
            <p className="text-[11px] text-warm-muted">
              {stats.approved_doctors || 0} Verified &middot; {stats.pending_doctors || 0} Pending
            </p>
          </div>

          <div className="bg-white p-5 rounded-3xl border border-warm-border shadow-xs space-y-2">
            <span className="text-[11px] font-bold text-warm-muted uppercase tracking-wider">Assessments</span>
            <div className="text-2xl font-black text-gray-900">{stats.total_assessments || 0}</div>
            <p className="text-[11px] text-warm-muted">Ensemble predictions run</p>
          </div>
        </div>

        {/* User Management Directory */}
        <div className="bg-white rounded-3xl border border-warm-border shadow-xs overflow-hidden">
          <div className="p-6 border-b border-warm-border flex flex-col sm:flex-row sm:items-center justify-between gap-4">
            <div>
              <h3 className="text-sm font-bold text-gray-900">User Directory</h3>
              <p className="text-xs text-warm-muted">Registered platform accounts and verification status</p>
            </div>

            <div className="flex flex-col sm:flex-row items-center gap-3">
              <div className="relative w-full sm:w-60">
                <Search className="w-4 h-4 text-warm-muted absolute left-3 top-1/2 -translate-y-1/2" />
                <input
                  type="text"
                  placeholder="Search user by name or email..."
                  value={searchTerm}
                  onChange={(e) => setSearchTerm(e.target.value)}
                  className="w-full pl-9 pr-3 py-1.5 bg-warm-bg border border-warm-border rounded-xl text-xs text-gray-900 focus:outline-none focus:border-brand-800"
                />
              </div>

              <div className="flex space-x-1">
                {['ALL', 'patient', 'doctor', 'admin'].map((r) => (
                  <button
                    key={r}
                    onClick={() => setFilterRole(r)}
                    className={`px-3 py-1 rounded-lg text-xs font-bold capitalize transition-all ${
                      filterRole === r
                        ? 'bg-brand-800 text-white'
                        : 'bg-warm-bg text-warm-muted hover:text-gray-900 border border-warm-border'
                    }`}
                  >
                    {r}
                  </button>
                ))}
              </div>
            </div>
          </div>

          {loading ? (
            <div className="p-12 text-center">
              <div className="w-8 h-8 border-3 border-brand-800 border-t-transparent rounded-full animate-spin mx-auto mb-3" />
              <p className="text-xs text-warm-muted">Loading user database...</p>
            </div>
          ) : filteredUsers.length === 0 ? (
            <div className="p-12 text-center space-y-2">
              <Users className="w-10 h-10 text-warm-muted mx-auto" />
              <p className="text-xs font-bold text-gray-800">No Users Found</p>
            </div>
          ) : (
            <div className="overflow-x-auto">
              <table className="w-full text-left text-xs">
                <thead className="bg-warm-bg text-warm-muted uppercase tracking-wider text-[10px] font-bold border-b border-warm-border">
                  <tr>
                    <th className="py-4 px-6">User Name</th>
                    <th className="py-4 px-6">Email Address</th>
                    <th className="py-4 px-6">Role</th>
                    <th className="py-4 px-6">Account Status</th>
                    <th className="py-4 px-6">Registered On</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-warm-border">
                  {filteredUsers.map((u) => (
                    <tr key={u.id} className="hover:bg-rose-50/20 transition-colors">
                      <td className="py-4 px-6 font-semibold text-gray-900">
                        {u.full_name || 'HeartShield User'}
                      </td>
                      <td className="py-4 px-6 font-mono text-warm-muted">
                        {u.email}
                      </td>
                      <td className="py-4 px-6">
                        <span
                          className={`px-2.5 py-1 rounded-full text-[10px] font-bold uppercase tracking-wider ${
                            u.role === 'admin'
                              ? 'bg-purple-50 text-purple-700 border border-purple-200'
                              : u.role === 'doctor'
                              ? 'bg-blue-50 text-blue-700 border border-blue-200'
                              : 'bg-emerald-50 text-emerald-700 border border-emerald-200'
                          }`}
                        >
                          {u.role}
                        </span>
                      </td>
                      <td className="py-4 px-6">
                        <div className="flex items-center space-x-1.5">
                          <span
                            className={`w-2 h-2 rounded-full ${
                              u.is_active ? 'bg-emerald-500' : 'bg-red-400'
                            }`}
                          />
                          <span className="text-gray-700 capitalize font-medium">
                            {u.is_active ? 'Active' : 'Suspended'}
                          </span>
                        </div>
                      </td>
                      <td className="py-4 px-6 text-warm-muted">
                        {u.created_at ? new Date(u.created_at).toLocaleDateString() : '—'}
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
