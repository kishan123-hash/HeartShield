import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import {
  FileText,
  Upload,
  Trash2,
  Eye,
  Bot,
  AlertCircle,
  CheckCircle2,
  FileCheck,
  Clock,
  Sparkles,
  X,
  File
} from 'lucide-react';
import Sidebar from '../components/Sidebar';
import api from '../api/client';

export default function MedicalReportsPage() {
  const navigate = useNavigate();
  const [reports, setReports] = useState([]);
  const [loading, setLoading] = useState(true);
  const [uploading, setUploading] = useState(false);
  const [error, setError] = useState('');
  const [success, setSuccess] = useState('');
  const [selectedReport, setSelectedReport] = useState(null);

  // Form State for Upload
  const [file, setFile] = useState(null);
  const [reportType, setReportType] = useState('Lipid Panel');

  const fetchReports = async () => {
    setLoading(true);
    try {
      const res = await api.get('/medical-reports');
      setReports(res.data?.reports || []);
    } catch (err) {
      console.error('Error fetching medical reports:', err);
      setError('Unable to load uploaded medical reports.');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchReports();
  }, []);

  const handleFileChange = (e) => {
    if (e.target.files && e.target.files[0]) {
      const selected = e.target.files[0];
      if (selected.size > 10 * 1024 * 1024) {
        setError('File size exceeds the 10MB limit.');
        return;
      }
      setFile(selected);
      setError('');
    }
  };

  const handleUpload = async (e) => {
    e.preventDefault();
    if (!file) {
      setError('Please select a file to upload.');
      return;
    }

    setUploading(true);
    setError('');
    setSuccess('');

    const formData = new FormData();
    formData.append('file', file);
    formData.append('report_type', reportType);

    try {
      const res = await api.post('/medical-reports/upload', formData, {
        headers: {
          'Content-Type': 'multipart/form-data',
        },
      });
      setSuccess('Medical report parsed and stored successfully!');
      setFile(null);
      fetchReports();
    } catch (err) {
      console.error('Upload error:', err);
      setError(err.response?.data?.detail || 'Failed to upload and parse report.');
    } finally {
      setUploading(false);
    }
  };

  const handleDelete = async (id) => {
    if (!window.confirm('Are you sure you want to delete this medical report?')) return;
    try {
      await api.delete(`/medical-reports/${id}`);
      setReports(reports.filter((r) => r.id !== id));
      if (selectedReport?.id === id) setSelectedReport(null);
    } catch (err) {
      console.error('Delete error:', err);
      setError('Failed to delete report.');
    }
  };

  return (
    <div className="min-h-screen flex bg-warm-bg">
      <Sidebar />

      <main className="flex-1 p-6 sm:p-10 max-w-6xl mx-auto space-y-8">
        {/* Header */}
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
          <div>
            <span className="text-[11px] font-bold uppercase tracking-wider text-brand-800 bg-brand-50 px-2.5 py-0.5 rounded-full border border-brand-200">
              Clinical Document Vault
            </span>
            <h1 className="text-2xl font-black text-gray-900 tracking-tight mt-1">
              Medical Reports & Lab Extraction
            </h1>
            <p className="text-xs text-warm-muted mt-1">
              Upload blood tests, ECG readings, or discharge summaries for AI extraction and chatbot grounding.
            </p>
          </div>
        </div>

        {/* Status Alerts */}
        {error && (
          <div className="p-4 rounded-2xl bg-red-50 border border-red-200 flex items-center justify-between text-xs text-red-700">
            <div className="flex items-center space-x-2">
              <AlertCircle className="w-4 h-4 shrink-0" />
              <span>{error}</span>
            </div>
            <button onClick={() => setError('')}><X className="w-4 h-4" /></button>
          </div>
        )}
        {success && (
          <div className="p-4 rounded-2xl bg-emerald-50 border border-emerald-200 flex items-center justify-between text-xs text-emerald-700">
            <div className="flex items-center space-x-2">
              <CheckCircle2 className="w-4 h-4 shrink-0" />
              <span>{success}</span>
            </div>
            <button onClick={() => setSuccess('')}><X className="w-4 h-4" /></button>
          </div>
        )}

        {/* Upload Box */}
        <div className="bg-white p-6 sm:p-8 rounded-3xl border border-warm-border shadow-xs">
          <form onSubmit={handleUpload} className="space-y-4">
            <h3 className="text-sm font-bold text-gray-900 flex items-center space-x-2">
              <Upload className="w-4 h-4 text-brand-800" />
              <span>Upload New Clinical Document</span>
            </h3>

            <div className="grid grid-cols-1 md:grid-cols-3 gap-4 items-center">
              <div>
                <label className="block text-xs font-semibold text-gray-700 mb-1.5">
                  Report Classification
                </label>
                <select
                  value={reportType}
                  onChange={(e) => setReportType(e.target.value)}
                  className="w-full px-3.5 py-2.5 bg-warm-bg border border-warm-border rounded-xl text-xs text-gray-900 focus:outline-none focus:border-brand-800"
                >
                  <option value="Lipid Panel">Lipid Panel / Blood Chemistry</option>
                  <option value="ECG / EKG">Electrocardiogram (ECG)</option>
                  <option value="Echocardiogram">Echocardiogram Report</option>
                  <option value="Discharge Summary">Hospital Discharge Summary</option>
                  <option value="General Lab">General Blood / Urine Lab</option>
                </select>
              </div>

              <div className="md:col-span-2">
                <label className="block text-xs font-semibold text-gray-700 mb-1.5">
                  Document File (PDF, DOCX, JPG, PNG &le; 10MB)
                </label>
                <div className="flex items-center space-x-3">
                  <input
                    type="file"
                    accept=".pdf,.docx,.jpg,.jpeg,.png"
                    onChange={handleFileChange}
                    className="block w-full text-xs text-gray-500 file:mr-4 file:py-2.5 file:px-4 file:rounded-xl file:border-0 file:text-xs file:font-bold file:bg-brand-50 file:text-brand-800 hover:file:bg-brand-100 transition-all cursor-pointer"
                  />
                  <button
                    type="submit"
                    disabled={uploading || !file}
                    className="px-6 py-2.5 rounded-xl bg-brand-800 text-white font-bold text-xs hover:bg-brand-900 transition-all shadow-md shadow-brand-900/20 disabled:opacity-50 shrink-0"
                  >
                    {uploading ? 'Parsing with AI...' : 'Upload & Parse'}
                  </button>
                </div>
              </div>
            </div>
          </form>
        </div>

        {/* Uploaded Reports List */}
        <div className="bg-white rounded-3xl border border-warm-border shadow-xs overflow-hidden">
          <div className="p-6 border-b border-warm-border flex items-center justify-between">
            <h3 className="text-sm font-bold text-gray-900">Stored Medical Records</h3>
            <span className="text-xs text-warm-muted">{reports.length} records found</span>
          </div>

          {loading ? (
            <div className="p-12 text-center">
              <div className="w-8 h-8 border-3 border-brand-800 border-t-transparent rounded-full animate-spin mx-auto mb-3" />
              <p className="text-xs text-warm-muted">Loading medical documents...</p>
            </div>
          ) : reports.length === 0 ? (
            <div className="p-12 text-center space-y-3">
              <div className="w-12 h-12 bg-rose-50 text-brand-800 rounded-full flex items-center justify-center mx-auto">
                <FileText className="w-6 h-6" />
              </div>
              <p className="text-xs font-bold text-gray-900">No Medical Documents Uploaded</p>
              <p className="text-[11px] text-warm-muted max-w-sm mx-auto">
                Upload your lab tests and medical charts above so the AI Health Assistant can analyze them during consultation.
              </p>
            </div>
          ) : (
            <div className="overflow-x-auto">
              <table className="w-full text-left text-xs">
                <thead className="bg-warm-bg text-warm-muted uppercase tracking-wider text-[10px] font-bold border-b border-warm-border">
                  <tr>
                    <th className="py-4 px-6">Document Name</th>
                    <th className="py-4 px-6">Type</th>
                    <th className="py-4 px-6">Upload Date</th>
                    <th className="py-4 px-6">File Size</th>
                    <th className="py-4 px-6">OCR Extraction</th>
                    <th className="py-4 px-6 text-right">Actions</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-warm-border">
                  {reports.map((rep) => {
                    const parsedParams = rep.extracted_biomarkers || rep.extracted_text;
                    const sizeKb = rep.file_size ? Math.round(rep.file_size / 1024) : '—';

                    return (
                      <tr key={rep.id} className="hover:bg-rose-50/20 transition-colors">
                        <td className="py-4 px-6 font-semibold text-gray-900">
                          <div className="flex items-center space-x-2">
                            <File className="w-4 h-4 text-brand-800" />
                            <span className="truncate max-w-xs">{rep.original_filename || rep.file_name}</span>
                          </div>
                        </td>

                        <td className="py-4 px-6">
                          <span className="px-2.5 py-1 rounded-full text-[10px] font-bold bg-warm-bg text-gray-700 border border-warm-border">
                            {rep.report_type || 'Clinical Lab'}
                          </span>
                        </td>

                        <td className="py-4 px-6 text-warm-muted">
                          {new Date(rep.created_at).toLocaleDateString()}
                        </td>

                        <td className="py-4 px-6 font-mono text-warm-muted">
                          {sizeKb} KB
                        </td>

                        <td className="py-4 px-6">
                          {parsedParams ? (
                            <span className="inline-flex items-center space-x-1 text-[11px] text-emerald-700 font-semibold bg-emerald-50 px-2.5 py-1 rounded-full border border-emerald-200">
                              <Sparkles className="w-3 h-3 text-emerald-600" />
                              <span>Biomarkers Extracted</span>
                            </span>
                          ) : (
                            <span className="text-[11px] text-warm-muted">Raw Document</span>
                          )}
                        </td>

                        <td className="py-4 px-6 text-right">
                          <div className="flex items-center justify-end space-x-2">
                            <button
                              onClick={() => setSelectedReport(rep)}
                              className="p-1.5 rounded-lg text-gray-600 hover:text-brand-800 hover:bg-warm-bg transition-all"
                              title="Inspect Extracted Text"
                            >
                              <Eye className="w-4 h-4" />
                            </button>
                            <button
                              onClick={() => navigate(`/patient/chat?report_id=${rep.id}`)}
                              className="p-1.5 rounded-lg text-brand-800 hover:bg-rose-50 transition-all"
                              title="Discuss with AI Assistant"
                            >
                              <Bot className="w-4 h-4" />
                            </button>
                            <button
                              onClick={() => handleDelete(rep.id)}
                              className="p-1.5 rounded-lg text-red-500 hover:text-red-700 hover:bg-red-50 transition-all"
                              title="Delete Record"
                            >
                              <Trash2 className="w-4 h-4" />
                            </button>
                          </div>
                        </td>
                      </tr>
                    );
                  })}
                </tbody>
              </table>
            </div>
          )}
        </div>

        {/* Modal for viewing extracted document text */}
        {selectedReport && (
          <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/40 backdrop-blur-xs">
            <div className="bg-white rounded-3xl border border-warm-border shadow-xl max-w-2xl w-full p-6 space-y-4 max-h-[85vh] flex flex-col">
              <div className="flex items-center justify-between border-b border-warm-border pb-3">
                <div className="flex items-center space-x-2">
                  <FileText className="w-5 h-5 text-brand-800" />
                  <h3 className="text-sm font-bold text-gray-900 truncate">
                    {selectedReport.original_filename || selectedReport.file_name}
                  </h3>
                </div>
                <button
                  onClick={() => setSelectedReport(null)}
                  className="p-1 rounded-lg text-warm-muted hover:text-gray-900"
                >
                  <X className="w-5 h-5" />
                </button>
              </div>

              <div className="flex-1 overflow-y-auto space-y-3 pr-2">
                <div>
                  <span className="text-[10px] font-bold uppercase tracking-wider text-warm-muted">Extracted Clinical Content</span>
                  <div className="mt-1 p-4 bg-warm-bg rounded-2xl border border-warm-border font-mono text-xs text-gray-800 whitespace-pre-wrap leading-relaxed">
                    {selectedReport.extracted_text || 'No readable text content found in document.'}
                  </div>
                </div>
              </div>

              <div className="border-t border-warm-border pt-3 flex justify-end space-x-2">
                <button
                  onClick={() => setSelectedReport(null)}
                  className="px-5 py-2 rounded-full text-xs font-bold text-gray-700 bg-warm-bg hover:bg-warm-border"
                >
                  Close
                </button>
                <button
                  onClick={() => {
                    const rId = selectedReport.id;
                    setSelectedReport(null);
                    navigate(`/patient/chat?report_id=${rId}`);
                  }}
                  className="px-5 py-2 rounded-full text-xs font-bold text-white bg-brand-800 hover:bg-brand-900 shadow-md shadow-brand-900/20 flex items-center space-x-1.5"
                >
                  <Bot className="w-4 h-4" />
                  <span>Consult AI with this Report</span>
                </button>
              </div>
            </div>
          </div>
        )}
      </main>
    </div>
  );
}
