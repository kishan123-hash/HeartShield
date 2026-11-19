import React, { useState, useEffect } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import {
  FileCheck,
  CheckCircle2,
  Stethoscope,
  Activity,
  Calendar,
  Clock,
  ArrowRight,
  Search,
  Filter,
  ShieldCheck,
  AlertCircle,
  RefreshCw,
  ChevronRight,
  TrendingUp
} from 'lucide-react';
import Sidebar from '../components/Sidebar';
import api from '../api/client';

export default function PatientVerifiedReportsPage() {
  const navigate = useNavigate();
  const [reports, setReports] = useState([]);
  const [loading, setLoading] = useState(true);
  const [searchTerm, setSearchTerm] = useState('');
  const [filterRisk, setFilterRisk] = useState('ALL');
  const [errorMsg, setErrorMsg] = useState('');

  const fetchVerifiedReports = async () => {
    setLoading(true);
    setErrorMsg('');
    try {
      const res = await api.get('/patients/me/verified-reports');
      setReports(res.data?.reports || []);
    } catch (err) {
      console.error('Error fetching verified reports:', err);
      setErrorMsg('Failed to load verified reports. Please try again.');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchVerifiedReports();
  }, []);

  const filteredReports = reports.filter((r) => {
    if (filterRisk !== 'ALL' && (r.risk_category || '').toUpperCase() !== filterRisk) {
      return false;
    }
    if (!searchTerm) return true;
    const term = searchTerm.toLowerCase();
    return (
      (r.report_code && r.report_code.toLowerCase().includes(term)) ||
      (r.doctor_name && r.doctor_name.toLowerCase().includes(term)) ||
      (r.patient_name && r.patient_name.toLowerCase().includes(term)) ||
      (r.risk_category && r.risk_category.toLowerCase().includes(term))
    );
  });

  const getRiskBadge = (risk) => {
    const r = (risk || '').toUpperCase();
    if (r.includes('HIGH')) {
      return <span className="px-2.5 py-0.5 rounded-full text-[10px] font-bold bg-red-100 text-red-800">High Risk</span>;
    }
    if (r.includes('MOD') || r.includes('MED')) {
      return <span className="px-2.5 py-0.5 rounded-full text-[10px] font-bold bg-amber-100 text-amber-800">Moderate Risk</span>;
    }
    return <span className="px-2.5 py-0.5 rounded-full text-[10px] font-bold bg-emerald-100 text-emerald-800">Low Risk</span>;
  };

  return (
    <div className="min-h-screen flex flex-col lg:flex-row bg-warm-bg w-full min-w-0 overflow-x-hidden">
      <Sidebar />

      <main className="flex-1 p-4 sm:p-6 lg:p-10 max-w-6xl w-full mx-auto space-y-8 min-w-0">
        {/* Header */}
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
          <div>
            <div className="flex items-center space-x-2">
              <span className="text-[11px] font-bold uppercase tracking-wider text-brand-800 bg-brand-50 px-2.5 py-0.5 rounded-full border border-brand-200">
                Patient Medical Portal
              </span>
              <span className="text-xs text-warm-muted">Clinical Governance</span>
            </div>
            <h1 className="text-2xl font-black text-gray-900 tracking-tight mt-1 flex items-center space-x-2">
              <FileCheck className="w-6 h-6 text-brand-800" />
              <span>Verified Reports</span>
            </h1>
            <p className="text-xs text-warm-muted mt-1">
              Official cardiovascular health evaluation reports reviewed, validated, and signed off by your attending physician.
            </p>
          </div>

          <button
            onClick={fetchVerifiedReports}
            disabled={loading}
            className="inline-flex items-center space-x-2 px-4 py-2 rounded-full text-xs font-bold text-gray-700 bg-white border border-warm-border hover:bg-rose-50 transition-all shadow-xs shrink-0 self-start sm:self-auto"
          >
            <RefreshCw className={`w-3.5 h-3.5 ${loading ? 'animate-spin' : ''}`} />
            <span>Refresh</span>
          </button>
        </div>

        {/* Error Alert */}
        {errorMsg && (
          <div className="p-4 rounded-2xl bg-red-50 border border-red-200 text-xs text-red-700 flex items-center space-x-2">
            <AlertCircle className="w-4 h-4 shrink-0" />
            <span>{errorMsg}</span>
          </div>
        )}

        {/* Search & Filter Toolbar */}
        <div className="bg-white p-4 sm:p-5 rounded-3xl border border-warm-border shadow-xs space-y-3">
          <div className="flex flex-col sm:flex-row gap-3 items-center justify-between">
            {/* Search Input */}
            <div className="relative w-full sm:w-80">
              <Search className="w-4 h-4 text-warm-muted absolute left-3.5 top-1/2 -translate-y-1/2" />
              <input
                type="text"
                placeholder="Search by Report ID, Doctor, or Risk..."
                value={searchTerm}
                onChange={(e) => setSearchTerm(e.target.value)}
                className="w-full pl-9 pr-3 py-2 bg-warm-bg border border-warm-border rounded-xl text-xs text-gray-900 focus:outline-none focus:border-brand-800 transition-all placeholder:text-warm-muted"
              />
            </div>

            {/* Filter Tabs */}
            <div className="flex items-center space-x-1.5 w-full sm:w-auto overflow-x-auto pb-1 sm:pb-0">
              {[
                { id: 'ALL', label: `All (${reports.length})` },
                { id: 'LOW', label: 'Low Risk' },
                { id: 'MODERATE', label: 'Moderate Risk' },
                { id: 'HIGH', label: 'High Risk' },
              ].map((tab) => (
                <button
                  key={tab.id}
                  onClick={() => setFilterRisk(tab.id)}
                  className={`px-3 py-1.5 rounded-lg text-xs font-bold transition-all whitespace-nowrap ${
                    filterRisk === tab.id
                      ? 'bg-brand-800 text-white shadow-xs'
                      : 'text-gray-600 hover:text-brand-800 hover:bg-rose-50'
                  }`}
                >
                  {tab.label}
                </button>
              ))}
            </div>
          </div>
        </div>

        {/* Reports Content */}
        {loading ? (
          <div className="bg-white p-12 rounded-3xl border border-warm-border shadow-xs text-center space-y-3">
            <div className="w-8 h-8 border-3 border-brand-800 border-t-transparent rounded-full animate-spin mx-auto" />
            <p className="text-xs text-warm-muted">Loading your verified clinical reports...</p>
          </div>
        ) : filteredReports.length === 0 ? (
          <div className="bg-white p-12 rounded-3xl border border-warm-border shadow-xs text-center space-y-3">
            <div className="w-12 h-12 rounded-2xl bg-warm-bg text-warm-muted flex items-center justify-center mx-auto">
              <ShieldCheck className="w-6 h-6 text-brand-800" />
            </div>
            <h3 className="text-sm font-bold text-gray-900">No verified reports available</h3>
            <p className="text-xs text-warm-muted max-w-md mx-auto">
              {searchTerm || filterRisk !== 'ALL'
                ? 'No reports match your selected search or risk filter.'
                : 'When your attending physician reviews and validates your risk evaluation, your signed official report will appear here.'}
            </p>
          </div>
        ) : (
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            {filteredReports.map((report) => {
              const origDate = report.original_prediction_date
                ? new Date(report.original_prediction_date).toLocaleDateString('en-US', {
                    month: 'short',
                    day: 'numeric',
                    year: 'numeric',
                  })
                : '—';

              const verDate = report.verification_date
                ? new Date(report.verification_date).toLocaleDateString('en-US', {
                    month: 'short',
                    day: 'numeric',
                    year: 'numeric',
                  })
                : '—';

              const verTime = report.verification_date
                ? new Date(report.verification_date).toLocaleTimeString('en-US', {
                    hour: '2-digit',
                    minute: '2-digit',
                  })
                : '';

              return (
                <div
                  key={report.report_id}
                  className="bg-white p-6 rounded-3xl border border-warm-border shadow-xs hover:shadow-md hover:border-brand-300 transition-all space-y-4 flex flex-col justify-between"
                >
                  <div className="space-y-3">
                    {/* Top Row: Report ID & Verification Badge */}
                    <div className="flex items-center justify-between">
                      <div className="flex items-center space-x-2">
                        <span className="text-xs font-mono font-bold text-brand-800 bg-brand-50 px-2.5 py-0.5 rounded-full border border-brand-200">
                          {report.report_code || `HS-VR-${report.report_id}`}
                        </span>
                      </div>
                      <div className="flex items-center space-x-1.5 text-emerald-700 bg-emerald-50 px-2.5 py-0.5 rounded-full border border-emerald-200">
                        <CheckCircle2 className="w-3.5 h-3.5" />
                        <span className="text-[10px] font-bold uppercase tracking-wider">Verified</span>
                      </div>
                    </div>

                    {/* Patient and Risk Summary */}
                    <div className="flex items-start justify-between gap-4 pt-1">
                      <div>
                        <span className="text-[10px] font-bold text-warm-muted uppercase tracking-wider block">
                          Patient Name
                        </span>
                        <h4 className="text-sm font-bold text-gray-900 mt-0.5">
                          {report.patient_name}
                        </h4>
                        <div className="text-[11px] text-warm-muted mt-0.5 flex items-center space-x-1.5">
                          <Calendar className="w-3 h-3 text-warm-muted" />
                          <span>Prediction Date: {origDate}</span>
                        </div>
                      </div>

                      {/* Calculated Risk Block */}
                      <div className="text-right">
                        <div className="text-xl font-black text-brand-800">
                          {report.risk_percentage}%
                        </div>
                        <div className="mt-0.5">{getRiskBadge(report.risk_category)}</div>
                      </div>
                    </div>

                    {/* Attending Physician Section */}
                    <div className="p-3 bg-warm-bg rounded-2xl border border-warm-border flex items-center justify-between text-xs">
                      <div className="flex items-center space-x-2">
                        <div className="w-8 h-8 rounded-full bg-brand-100 text-brand-800 flex items-center justify-center shrink-0">
                          <Stethoscope className="w-4 h-4" />
                        </div>
                        <div>
                          <span className="text-[10px] font-bold text-warm-muted uppercase block">
                            Attending Physician
                          </span>
                          <span className="font-bold text-gray-900">{report.doctor_name}</span>
                        </div>
                      </div>
                      <div className="text-right">
                        <span className="text-[10px] font-bold text-warm-muted uppercase block">
                          Verified Date &amp; Time
                        </span>
                        <span className="font-semibold text-gray-800">
                          {verDate} {verTime}
                        </span>
                      </div>
                    </div>

                    {/* Clinical Notes Preview if available */}
                    {report.doctor_notes && (
                      <div className="text-xs text-warm-muted italic line-clamp-2 bg-warm-bg/50 p-2.5 rounded-xl border border-warm-border/60">
                        "{report.doctor_notes}"
                      </div>
                    )}
                  </div>

                  {/* Open Report Button */}
                  <div className="pt-2 border-t border-warm-border/60">
                    <button
                      onClick={() => navigate(`/patient/verified-reports/${report.report_id}`)}
                      className="w-full inline-flex items-center justify-center space-x-2 py-2.5 rounded-full text-xs font-bold text-white bg-brand-800 hover:bg-brand-900 transition-all shadow-md shadow-brand-900/15"
                    >
                      <FileCheck className="w-4 h-4" />
                      <span>View Complete Verified Report</span>
                      <ChevronRight className="w-4 h-4" />
                    </button>
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
