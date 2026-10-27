import React, { useState } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import {
  Shield,
  Heart,
  Lock,
  Mail,
  User,
  AlertCircle,
  ArrowRight,
  Stethoscope,
} from 'lucide-react';
import api from '../api/client';
import Navbar from '../components/Navbar';
import Footer from '../components/Footer';

export default function RegisterPage() {
  const [role, setRole] = useState('patient'); // 'patient' or 'doctor'
  const [formData, setFormData] = useState({
    full_name: '',
    email: '',
    phone: '',
    password: '',
    confirm_password: '',
    gender: 'male',
    date_of_birth: '2000-01-01',
    // Doctor specific
    specialization: 'Cardiology',
    medical_license_number: '',
    hospital_name: 'General Hospital',
    years_of_experience: 5,
  });
  const [termsAccepted, setTermsAccepted] = useState(false);
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);

  const navigate = useNavigate();

  const handleInitialSubmit = (e) => {
    e.preventDefault();
    setError('');

    if (formData.password !== formData.confirm_password) {
      setError('Passwords do not match.');
      return;
    }

    if (formData.password.length < 6) {
      setError('Password must be at least 6 characters.');
      return;
    }

    if (!termsAccepted) {
      setError('You must agree to the Terms & Conditions.');
      return;
    }

    if (role === 'patient') {
      executePatientRegistration();
    } else {
      executeDoctorRegistration();
    }
  };

  const executePatientRegistration = async () => {
    setError('');
    setLoading(true);

    try {
      await api.post('/auth/register/patient', {
        full_name: formData.full_name.trim(),
        email: formData.email.trim(),
        phone: formData.phone.trim() || undefined,
        password: formData.password,
        gender: formData.gender,
        date_of_birth: formData.date_of_birth,
        channel: 'email',
      });

      navigate(
        `/verify-otp?email=${encodeURIComponent(formData.email.trim())}`
      );
    } catch (err) {
      console.error('Patient registration error:', err);
      const detail = err.response?.data?.detail;
      setError(
        typeof detail === 'string'
          ? detail
          : 'Registration failed. Please check your credentials.'
      );
    } finally {
      setLoading(false);
    }
  };

  const executeDoctorRegistration = async () => {
    setLoading(true);

    try {
      await api.post('/auth/register/doctor', {
        full_name: formData.full_name.trim(),
        email: formData.email.trim(),
        phone: formData.phone.trim() || undefined,
        password: formData.password,
        specialization: formData.specialization,
        medical_license_number: formData.medical_license_number || `LIC-${Date.now().toString().slice(-6)}`,
        hospital_name: formData.hospital_name,
        years_of_experience: Number(formData.years_of_experience) || 0,
      });

      navigate(`/verify-otp?email=${encodeURIComponent(formData.email.trim())}`);
    } catch (err) {
      console.error('Doctor registration error:', err);
      const detail = err.response?.data?.detail;
      setError(
        typeof detail === 'string'
          ? detail
          : 'Registration failed. This email or medical license may already be registered.'
      );
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen flex flex-col bg-warm-bg">
      <Navbar />

      <main className="flex-1 flex items-center justify-center px-4 py-8 sm:py-12">
        <div className="w-full max-w-lg bg-white rounded-3xl border border-warm-border shadow-md p-6 sm:p-10 space-y-6">
          {/* Header */}
          <div className="text-center space-y-2">
            <div className="w-14 h-14 rounded-2xl bg-gradient-to-br from-brand-800 to-brand-900 flex items-center justify-center text-white mx-auto shadow-md shadow-brand-900/20">
              <div className="relative">
                <Shield className="w-8 h-8 text-white" />
                <Heart className="w-4 h-4 text-rose-300 absolute inset-0 m-auto fill-rose-300" />
              </div>
            </div>
            <h2 className="text-2xl font-black text-gray-900 tracking-tight">Create Your Account</h2>
            <p className="text-xs text-warm-muted">Join HeartShield to monitor and protect cardiovascular health</p>
          </div>

          {/* Role Tabs */}
          <div className="grid grid-cols-2 p-1.5 bg-warm-bg rounded-2xl border border-warm-border/80">
            <button
              type="button"
              onClick={() => setRole('patient')}
              className={`py-2 text-xs font-bold rounded-xl transition-all ${
                role === 'patient'
                  ? 'bg-brand-800 text-white shadow-xs'
                  : 'text-gray-600 hover:text-brand-800'
              }`}
            >
              Patient Account
            </button>
            <button
              type="button"
              onClick={() => setRole('doctor')}
              className={`py-2 text-xs font-bold rounded-xl transition-all ${
                role === 'doctor'
                  ? 'bg-brand-800 text-white shadow-xs'
                  : 'text-gray-600 hover:text-brand-800'
              }`}
            >
              Doctor / Physician
            </button>
          </div>

          {error && (
            <div className="p-3.5 rounded-xl bg-rose-50 border border-rose-200 text-rose-700 text-xs font-semibold flex items-center space-x-2">
              <AlertCircle className="w-4 h-4 shrink-0" />
              <span>{error}</span>
            </div>
          )}

          <form onSubmit={handleInitialSubmit} className="space-y-4">
            <div>
              <label className="block text-xs font-bold text-gray-700 uppercase tracking-wider mb-1">
                Full Name
              </label>
              <div className="relative">
                <div className="absolute inset-y-0 left-0 pl-3.5 flex items-center pointer-events-none text-warm-muted">
                  <User className="w-4 h-4" />
                </div>
                <input
                  type="text"
                  required
                  placeholder="Enter full name"
                  value={formData.full_name}
                  onChange={(e) => setFormData({ ...formData, full_name: e.target.value })}
                  className="w-full pl-10 pr-4 py-2.5 rounded-xl border border-warm-border text-sm focus:outline-none focus:ring-2 focus:ring-brand-800/20 focus:border-brand-800"
                />
              </div>
            </div>

            <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
              <div>
                <label className="block text-xs font-bold text-gray-700 uppercase tracking-wider mb-1">
                  Email Address
                </label>
                <div className="relative">
                  <div className="absolute inset-y-0 left-0 pl-3.5 flex items-center pointer-events-none text-warm-muted">
                    <Mail className="w-4 h-4" />
                  </div>
                  <input
                    type="email"
                    required
                    placeholder="name@example.com"
                    value={formData.email}
                    onChange={(e) => setFormData({ ...formData, email: e.target.value })}
                    className="w-full pl-10 pr-4 py-2.5 rounded-xl border border-warm-border text-sm focus:outline-none focus:ring-2 focus:ring-brand-800/20 focus:border-brand-800"
                  />
                </div>
              </div>

              <div>
                <label className="block text-xs font-bold text-gray-700 uppercase tracking-wider mb-1">
                  Phone Number
                </label>
                <input
                  type="tel"
                  placeholder="+919876543210"
                  value={formData.phone}
                  onChange={(e) => setFormData({ ...formData, phone: e.target.value })}
                  className="w-full px-4 py-2.5 rounded-xl border border-warm-border text-sm focus:outline-none focus:ring-2 focus:ring-brand-800/20 focus:border-brand-800"
                />
              </div>
            </div>

            {/* Role Specific Fields */}
            {role === 'patient' ? (
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className="block text-xs font-bold text-gray-700 uppercase tracking-wider mb-1">
                    Gender
                  </label>
                  <select
                    value={formData.gender}
                    onChange={(e) => setFormData({ ...formData, gender: e.target.value })}
                    className="w-full px-3 py-2.5 rounded-xl border border-warm-border text-sm focus:outline-none focus:ring-2 focus:ring-brand-800/20 focus:border-brand-800"
                  >
                    <option value="male">Male</option>
                    <option value="female">Female</option>
                    <option value="other">Other</option>
                  </select>
                </div>
                <div>
                  <label className="block text-xs font-bold text-gray-700 uppercase tracking-wider mb-1">
                    Date of Birth
                  </label>
                  <input
                    type="date"
                    required
                    value={formData.date_of_birth}
                    onChange={(e) => setFormData({ ...formData, date_of_birth: e.target.value })}
                    className="w-full px-3 py-2.5 rounded-xl border border-warm-border text-sm focus:outline-none focus:ring-2 focus:ring-brand-800/20 focus:border-brand-800"
                  />
                </div>
              </div>
            ) : (
              <div className="space-y-4">
                <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                  <div>
                    <label className="block text-xs font-bold text-gray-700 uppercase tracking-wider mb-1">
                      Medical License #
                    </label>
                    <input
                      type="text"
                      required
                      placeholder="e.g. MED-8921"
                      value={formData.medical_license_number}
                      onChange={(e) => setFormData({ ...formData, medical_license_number: e.target.value })}
                      className="w-full px-4 py-2.5 rounded-xl border border-warm-border text-sm focus:outline-none focus:ring-2 focus:ring-brand-800/20 focus:border-brand-800 font-mono"
                    />
                  </div>
                  <div>
                    <label className="block text-xs font-bold text-gray-700 uppercase tracking-wider mb-1">
                      Clinical Specialty
                    </label>
                    <select
                      value={formData.specialization}
                      onChange={(e) => setFormData({ ...formData, specialization: e.target.value })}
                      className="w-full px-3 py-2.5 rounded-xl border border-warm-border text-sm focus:outline-none focus:ring-2 focus:ring-brand-800/20 focus:border-brand-800"
                    >
                      <option value="Cardiology">Cardiology</option>
                      <option value="Cardiac Surgery">Cardiac Surgery</option>
                      <option value="Internal Medicine">Internal Medicine</option>
                      <option value="Interventional Cardiology">Interventional Cardiology</option>
                    </select>
                  </div>
                </div>

                <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                  <div>
                    <label className="block text-xs font-bold text-gray-700 uppercase tracking-wider mb-1">
                      Hospital / Clinic
                    </label>
                    <input
                      type="text"
                      required
                      placeholder="Hospital Name"
                      value={formData.hospital_name}
                      onChange={(e) => setFormData({ ...formData, hospital_name: e.target.value })}
                      className="w-full px-4 py-2.5 rounded-xl border border-warm-border text-sm focus:outline-none focus:ring-2 focus:ring-brand-800/20 focus:border-brand-800"
                    />
                  </div>
                  <div>
                    <label className="block text-xs font-bold text-gray-700 uppercase tracking-wider mb-1">
                      Years of Experience
                    </label>
                    <input
                      type="number"
                      min="0"
                      required
                      value={formData.years_of_experience}
                      onChange={(e) => setFormData({ ...formData, years_of_experience: e.target.value })}
                      className="w-full px-4 py-2.5 rounded-xl border border-warm-border text-sm focus:outline-none focus:ring-2 focus:ring-brand-800/20 focus:border-brand-800"
                    />
                  </div>
                </div>
              </div>
            )}

            {/* Passwords */}
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
              <div>
                <label className="block text-xs font-bold text-gray-700 uppercase tracking-wider mb-1">
                  Password
                </label>
                <div className="relative">
                  <div className="absolute inset-y-0 left-0 pl-3.5 flex items-center pointer-events-none text-warm-muted">
                    <Lock className="w-4 h-4" />
                  </div>
                  <input
                    type="password"
                    required
                    placeholder="Min. 6 chars"
                    value={formData.password}
                    onChange={(e) => setFormData({ ...formData, password: e.target.value })}
                    className="w-full pl-10 pr-4 py-2.5 rounded-xl border border-warm-border text-sm focus:outline-none focus:ring-2 focus:ring-brand-800/20 focus:border-brand-800"
                  />
                </div>
              </div>

              <div>
                <label className="block text-xs font-bold text-gray-700 uppercase tracking-wider mb-1">
                  Confirm Password
                </label>
                <div className="relative">
                  <div className="absolute inset-y-0 left-0 pl-3.5 flex items-center pointer-events-none text-warm-muted">
                    <Lock className="w-4 h-4" />
                  </div>
                  <input
                    type="password"
                    required
                    placeholder="Confirm password"
                    value={formData.confirm_password}
                    onChange={(e) => setFormData({ ...formData, confirm_password: e.target.value })}
                    className="w-full pl-10 pr-4 py-2.5 rounded-xl border border-warm-border text-sm focus:outline-none focus:ring-2 focus:ring-brand-800/20 focus:border-brand-800"
                  />
                </div>
              </div>
            </div>

            {/* Terms Checkbox */}
            <div className="flex items-start space-x-2.5 pt-1">
              <input
                type="checkbox"
                id="terms"
                required
                checked={termsAccepted}
                onChange={(e) => setTermsAccepted(e.target.checked)}
                className="mt-1 w-4 h-4 rounded text-brand-800 focus:ring-brand-800 border-warm-border"
              />
              <label htmlFor="terms" className="text-xs text-warm-muted leading-relaxed">
                I agree to the HeartShield Clinical Terms of Service, Privacy Policy, and understand that this tool is for research & education.
              </label>
            </div>

            <button
              type="submit"
              disabled={loading}
              className="w-full inline-flex items-center justify-center space-x-2 py-3 rounded-full text-sm font-bold text-white bg-brand-800 hover:bg-brand-900 shadow-md shadow-brand-900/20 transition-all disabled:opacity-50 mt-3"
            >
              <span>{loading ? 'Processing...' : role === 'patient' ? 'Register' : 'Create Doctor Account'}</span>
              <ArrowRight className="w-4 h-4" />
            </button>
          </form>

          <div className="text-center pt-1">
            <p className="text-xs text-warm-muted">
              Already have an account?{' '}
              <Link to="/login" className="font-bold text-brand-800 hover:text-brand-900 underline">
                Sign in
              </Link>
            </p>
          </div>
        </div>
      </main>

      <Footer />
    </div>
  );
}
