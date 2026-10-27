import React, { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import {
  Stethoscope,
  Search,
  CheckCircle2,
  Clock,
  Mail,
  MapPin,
  Building,
  Award,
  Send,
  MessageCircle,
  AlertCircle,
  X
} from 'lucide-react';
import Sidebar from '../components/Sidebar';
import api from '../api/client';

export default function PatientDoctorsPage() {
  const [doctors, setDoctors] = useState([]);
  const [loading, setLoading] = useState(true);
  const [searchTerm, setSearchTerm] = useState('');
  const [selectedSpecialty, setSelectedSpecialty] = useState('All');
  const [requestModalDoctor, setRequestModalDoctor] = useState(null);
  const [consultationNote, setConsultationNote] = useState('');
  const [submitting, setSubmitting] = useState(false);
  const [alert, setAlert] = useState(null);

  const fetchDoctors = async () => {
    try {
      setLoading(true);
      const res = await api.get('/consultations/doctors');
      setDoctors(res.data || []);
    } catch (err) {
      console.error('Failed to load doctors:', err);
      setAlert({
        type: 'error',
        message: 'Could not load verified doctors directory. Please try again later.'
      });
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchDoctors();
  }, []);

  const handleOpenRequestModal = (doctor) => {
    setRequestModalDoctor(doctor);
    setConsultationNote('');
  };

  const handleCloseRequestModal = () => {
    setRequestModalDoctor(null);
    setConsultationNote('');
  };

  const handleSubmitRequest = async (e) => {
    e.preventDefault();
    if (!requestModalDoctor) return;

    try {
      setSubmitting(true);
      setAlert(null);
      await api.post('/consultations/request', {
        doctor_id: requestModalDoctor.doctor_id,
        notes: consultationNote.trim() || undefined
      });

      setAlert({
        type: 'success',
        message: `Consultation request sent to ${requestModalDoctor.full_name}. They will review and respond soon.`
      });

      handleCloseRequestModal();
      fetchDoctors();
    } catch (err) {
      console.error('Request failed:', err);
      const errMsg = err.response?.data?.detail || 'Failed to submit consultation request.';
      setAlert({
        type: 'error',
        message: errMsg
      });
    } finally {
      setSubmitting(false);
    }
  };

  // Extract unique specializations for filter
  const specialties = ['All', ...Array.from(new Set(doctors.map(d => d.specialization).filter(Boolean)))];

  const filteredDoctors = doctors.filter((doc) => {
    const matchesSearch =
      doc.full_name.toLowerCase().includes(searchTerm.toLowerCase()) ||
      (doc.specialization && doc.specialization.toLowerCase().includes(searchTerm.toLowerCase())) ||
      (doc.hospital_name && doc.hospital_name.toLowerCase().includes(searchTerm.toLowerCase()));

    const matchesSpecialty =
      selectedSpecialty === 'All' || doc.specialization === selectedSpecialty;

    return matchesSearch && matchesSpecialty;
  });

  return (
    <div className="min-h-screen flex flex-col lg:flex-row bg-warm-bg w-full min-w-0 overflow-x-hidden">
      <Sidebar />

      <main className="flex-1 p-4 sm:p-6 lg:p-10 max-w-7xl w-full mx-auto space-y-8 min-w-0">
        {/* Header Banner */}
        <div className="bg-white rounded-3xl p-6 sm:p-8 border border-warm-border shadow-xs flex flex-col sm:flex-row items-start sm:items-center justify-between gap-6">
          <div className="space-y-1.5">
            <div className="flex items-center space-x-2">
              <span className="text-[11px] font-bold uppercase tracking-wider text-brand-800 bg-brand-50 px-2.5 py-0.5 rounded-full border border-brand-200">
                Cardiology Specialists
              </span>
              <span className="text-xs text-warm-muted">Verified Practitioner Network</span>
            </div>
            <h1 className="text-2xl sm:text-3xl font-black text-gray-900 tracking-tight">
              Verified Doctors Directory
            </h1>
            <p className="text-xs sm:text-sm text-warm-muted">
              Connect with board-certified cardiologists and healthcare practitioners verified by HeartShield administrators.
            </p>
          </div>

          <Link
            to="/patient/doctor-chat"
            className="inline-flex items-center space-x-2 px-5 py-2.5 rounded-full bg-brand-800 text-white font-bold text-xs hover:bg-brand-900 shadow-sm transition-all shrink-0"
          >
            <MessageCircle className="w-4 h-4" />
            <span>Open Connected Chats</span>
          </Link>
        </div>

        {/* Alert Notification */}
        {alert && (
          <div
            className={`p-4 rounded-2xl border text-xs font-semibold flex items-center justify-between transition-all ${
              alert.type === 'success'
                ? 'bg-emerald-50 text-emerald-800 border-emerald-200'
                : 'bg-red-50 text-red-800 border-red-200'
            }`}
          >
            <div className="flex items-center space-x-2">
              {alert.type === 'success' ? (
                <CheckCircle2 className="w-5 h-5 text-emerald-600 shrink-0" />
              ) : (
                <AlertCircle className="w-5 h-5 text-red-600 shrink-0" />
              )}
              <span>{alert.message}</span>
            </div>
            <button
              onClick={() => setAlert(null)}
              className="text-gray-400 hover:text-gray-700 ml-4"
            >
              <X className="w-4 h-4" />
            </button>
          </div>
        )}

        {/* Filter and Search Bar */}
        <div className="bg-white p-4 sm:p-5 rounded-2xl border border-warm-border shadow-xs flex flex-col md:flex-row gap-4 items-center justify-between">
          <div className="relative w-full md:w-80">
            <Search className="w-4 h-4 text-warm-muted absolute left-3 top-1/2 -translate-y-1/2" />
            <input
              type="text"
              placeholder="Search by doctor name or hospital..."
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
              className="w-full pl-9 pr-4 py-2 bg-warm-bg border border-warm-border rounded-xl text-xs text-gray-900 focus:outline-none focus:border-brand-800"
            />
          </div>

          <div className="flex items-center space-x-2 w-full md:w-auto overflow-x-auto pb-1 md:pb-0">
            <span className="text-xs font-bold text-warm-muted whitespace-nowrap">Specialty:</span>
            {specialties.map((spec) => (
              <button
                key={spec}
                onClick={() => setSelectedSpecialty(spec)}
                className={`px-3 py-1.5 rounded-xl text-xs font-semibold transition-all whitespace-nowrap ${
                  selectedSpecialty === spec
                    ? 'bg-brand-800 text-white shadow-xs'
                    : 'bg-warm-bg text-gray-600 hover:bg-rose-50/50 border border-warm-border'
                }`}
              >
                {spec}
              </button>
            ))}
          </div>
        </div>

        {/* Doctors Grid */}
        {loading ? (
          <div className="p-16 text-center bg-white rounded-3xl border border-warm-border">
            <div className="w-10 h-10 border-3 border-brand-800 border-t-transparent rounded-full animate-spin mx-auto mb-3" />
            <p className="text-xs font-semibold text-warm-muted">Loading verified doctors...</p>
          </div>
        ) : filteredDoctors.length === 0 ? (
          <div className="p-16 text-center bg-white rounded-3xl border border-warm-border space-y-3">
            <Stethoscope className="w-12 h-12 text-warm-muted mx-auto" />
            <h3 className="text-sm font-bold text-gray-800">No Verified Doctors Found</h3>
            <p className="text-xs text-warm-muted max-w-sm mx-auto">
              There are currently no verified doctors matching your filter criteria. Please check back soon as administrators verify new practitioners.
            </p>
          </div>
        ) : (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
            {filteredDoctors.map((doc) => {
              const status = doc.current_request_status;

              return (
                <div
                  key={doc.doctor_id}
                  className="bg-white rounded-3xl border border-warm-border shadow-xs hover:shadow-md transition-all p-6 flex flex-col justify-between space-y-5"
                >
                  {/* Top: Avatar & Verification Badge */}
                  <div className="space-y-4">
                    <div className="flex items-start justify-between">
                      <div className="w-14 h-14 rounded-2xl bg-rose-50 border border-rose-100 flex items-center justify-center text-brand-800 font-bold text-xl overflow-hidden shrink-0 shadow-xs">
                        {doc.profile_image ? (
                          <img
                            src={doc.profile_image}
                            alt={doc.full_name}
                            className="w-full h-full object-cover"
                          />
                        ) : (
                          <span>{doc.full_name.charAt(0)}</span>
                        )}
                      </div>

                      <span className="inline-flex items-center space-x-1 px-2.5 py-1 rounded-full text-[10px] font-bold bg-emerald-50 text-emerald-700 border border-emerald-200">
                        <CheckCircle2 className="w-3 h-3 text-emerald-600" />
                        <span>Verified</span>
                      </span>
                    </div>

                    <div>
                      <h3 className="text-base font-bold text-gray-900 tracking-tight">
                        {doc.full_name}
                      </h3>
                      <p className="text-xs font-semibold text-brand-800 mt-0.5">
                        {doc.specialization || 'Cardiovascular Specialist'}
                      </p>
                    </div>

                    {/* Quick Metadata */}
                    <div className="space-y-2 pt-2 border-t border-warm-border text-xs text-warm-muted">
                      <div className="flex items-center space-x-2">
                        <Award className="w-3.5 h-3.5 text-gray-400 shrink-0" />
                        <span>{doc.years_of_experience || 0} Years Experience</span>
                      </div>

                      {doc.hospital_name && (
                        <div className="flex items-center space-x-2">
                          <Building className="w-3.5 h-3.5 text-gray-400 shrink-0" />
                          <span className="truncate">{doc.hospital_name}</span>
                        </div>
                      )}

                      {doc.hospital_address && (
                        <div className="flex items-center space-x-2">
                          <MapPin className="w-3.5 h-3.5 text-gray-400 shrink-0" />
                          <span className="truncate">{doc.hospital_address}</span>
                        </div>
                      )}

                      <div className="flex items-center space-x-2">
                        <Mail className="w-3.5 h-3.5 text-gray-400 shrink-0" />
                        <span className="truncate">{doc.email}</span>
                      </div>
                    </div>

                    {doc.bio && (
                      <p className="text-xs text-gray-600 line-clamp-2 italic pt-1">
                        "{doc.bio}"
                      </p>
                    )}
                  </div>

                  {/* Bottom Action Button */}
                  <div className="pt-4 border-t border-warm-border">
                    {status === 'approved' ? (
                      <Link
                        to={`/patient/doctor-chat?doctor=${doc.doctor_id}`}
                        className="w-full inline-flex items-center justify-center space-x-2 py-2.5 px-4 rounded-xl text-xs font-bold text-white bg-emerald-700 hover:bg-emerald-800 transition-all shadow-xs"
                      >
                        <MessageCircle className="w-3.5 h-3.5" />
                        <span>Connected • Chat Now</span>
                      </Link>
                    ) : status === 'pending' ? (
                      <button
                        disabled
                        className="w-full inline-flex items-center justify-center space-x-2 py-2.5 px-4 rounded-xl text-xs font-bold text-amber-700 bg-amber-50 border border-amber-200 cursor-not-allowed"
                      >
                        <Clock className="w-3.5 h-3.5" />
                        <span>Request Pending Review</span>
                      </button>
                    ) : (
                      <button
                        onClick={() => handleOpenRequestModal(doc)}
                        className="w-full inline-flex items-center justify-center space-x-2 py-2.5 px-4 rounded-xl text-xs font-bold text-white bg-brand-800 hover:bg-brand-900 transition-all shadow-xs shadow-brand-800/10"
                      >
                        <Send className="w-3.5 h-3.5" />
                        <span>Request Consultation</span>
                      </button>
                    )}
                  </div>
                </div>
              );
            })}
          </div>
        )}

        {/* Consultation Request Modal */}
        {requestModalDoctor && (
          <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/40 backdrop-blur-xs p-4">
            <div className="bg-white rounded-3xl max-w-md w-full p-6 sm:p-7 border border-warm-border shadow-2xl space-y-5 animate-in fade-in duration-200">
              <div className="flex items-start justify-between">
                <div>
                  <h3 className="text-base font-bold text-gray-900">
                    Request Consultation
                  </h3>
                  <p className="text-xs text-warm-muted mt-0.5">
                    Connecting with {requestModalDoctor.full_name}
                  </p>
                </div>
                <button
                  onClick={handleCloseRequestModal}
                  className="p-1 rounded-lg text-gray-400 hover:text-gray-700 hover:bg-gray-100"
                >
                  <X className="w-5 h-5" />
                </button>
              </div>

              <div className="p-3.5 rounded-2xl bg-rose-50/50 border border-rose-100/80 space-y-1">
                <span className="text-[11px] font-bold text-brand-800 uppercase tracking-wider">
                  Doctor Details
                </span>
                <p className="text-xs font-bold text-gray-900">{requestModalDoctor.full_name}</p>
                <p className="text-xs text-warm-muted">{requestModalDoctor.specialization} • {requestModalDoctor.years_of_experience} yrs exp</p>
              </div>

              <form onSubmit={handleSubmitRequest} className="space-y-4">
                <div>
                  <label className="block text-xs font-bold text-gray-700 mb-1.5">
                    Reason / Clinical Notes (Optional)
                  </label>
                  <textarea
                    rows={4}
                    value={consultationNote}
                    onChange={(e) => setConsultationNote(e.target.value)}
                    placeholder="Briefly describe your cardiovascular concern, recent symptoms, or why you are requesting this consultation..."
                    className="w-full p-3 bg-warm-bg border border-warm-border rounded-xl text-xs text-gray-900 focus:outline-none focus:border-brand-800 resize-none"
                  />
                </div>

                <div className="flex items-center justify-end space-x-3 pt-2">
                  <button
                    type="button"
                    onClick={handleCloseRequestModal}
                    className="px-4 py-2 rounded-xl text-xs font-semibold text-gray-600 hover:bg-gray-100 transition-colors"
                  >
                    Cancel
                  </button>
                  <button
                    type="submit"
                    disabled={submitting}
                    className="inline-flex items-center space-x-2 px-5 py-2.5 rounded-xl text-xs font-bold text-white bg-brand-800 hover:bg-brand-900 transition-all shadow-xs disabled:opacity-50"
                  >
                    {submitting ? (
                      <>
                        <div className="w-3.5 h-3.5 border-2 border-white border-t-transparent rounded-full animate-spin" />
                        <span>Sending...</span>
                      </>
                    ) : (
                      <>
                        <Send className="w-3.5 h-3.5" />
                        <span>Send Request</span>
                      </>
                    )}
                  </button>
                </div>
              </form>
            </div>
          </div>
        )}
      </main>
    </div>
  );
}
