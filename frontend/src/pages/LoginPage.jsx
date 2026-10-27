import React, { useState } from 'react';
import { Link, useNavigate, useLocation } from 'react-router-dom';
import { Shield, Heart, Lock, Mail, AlertCircle, CheckCircle2, ArrowRight } from 'lucide-react';
import api from '../api/client';
import { useAuth } from '../context/AuthContext';
import Navbar from '../components/Navbar';
import Footer from '../components/Footer';

export default function LoginPage() {
  const [role, setRole] = useState('patient'); // 'patient' or 'doctor'
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);

  const { login } = useAuth();
  const navigate = useNavigate();
  const location = useLocation();

  const isExpired = new URLSearchParams(location.search).get('expired');
  const isResetSuccess = new URLSearchParams(location.search).get('reset') === 'success';
  const isVerified = new URLSearchParams(location.search).get('verified') === 'true';

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError('');
    setLoading(true);

    try {
      const res = await api.post('/auth/login', {
        email: email.trim(),
        password: password,
      });

      const { access_token, user } = res.data;
      login(access_token, user);

      // Role-based redirection
      if (user.role === 'doctor') {
        navigate('/doctor/dashboard');
      } else if (user.role === 'admin') {
        navigate('/admin/dashboard');
      } else {
        navigate('/patient/dashboard');
      }
    } catch (err) {
      console.error('Login error:', err);
      const detail = err.response?.data?.detail;
      setError(
        typeof detail === 'string'
          ? detail
          : 'Invalid email or password. Please verify your credentials.'
      );
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen flex flex-col bg-warm-bg">
      <Navbar />

      <main className="flex-1 flex items-center justify-center px-4 py-8 sm:py-12">
        <div className="w-full max-w-md bg-white rounded-3xl border border-warm-border shadow-md p-6 sm:p-10 space-y-6">
          {/* Logo & Header */}
          <div className="text-center space-y-2">
            <img
              src="/heartshield-logo.png"
              alt="HeartShield Logo"
              className="w-20 h-20 object-contain mx-auto"
            />
            <h2 className="text-2xl font-black text-gray-900 tracking-tight">Welcome Back</h2>
            <p className="text-xs text-warm-muted">Sign in to your HeartShield account</p>
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
              Patient Sign In
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

          {/* Success Notices */}
          {isResetSuccess && (
            <div className="p-3.5 rounded-xl bg-emerald-50 border border-emerald-200 text-emerald-800 text-xs font-semibold flex items-center space-x-2">
              <CheckCircle2 className="w-4 h-4 shrink-0" />
              <span>Password updated successfully. Please log in with your new password.</span>
            </div>
          )}

          {isVerified && (
            <div className="p-3.5 rounded-xl bg-emerald-50 border border-emerald-200 text-emerald-800 text-xs font-semibold flex items-center space-x-2">
              <CheckCircle2 className="w-4 h-4 shrink-0" />
              <span>Registration completed and verified! You may now sign in.</span>
            </div>
          )}

          {/* Expired Session Notice */}
          {isExpired && (
            <div className="p-3 rounded-xl bg-amber-50 border border-amber-200 text-amber-800 text-xs flex items-center space-x-2">
              <AlertCircle className="w-4 h-4 shrink-0" />
              <span>Your session has expired. Please log in again.</span>
            </div>
          )}

          {/* Error Message */}
          {error && (
            <div className="p-3.5 rounded-xl bg-rose-50 border border-rose-200 text-rose-700 text-xs font-semibold flex items-center space-x-2">
              <AlertCircle className="w-4 h-4 shrink-0" />
              <span>{error}</span>
            </div>
          )}

          {/* Form */}
          <form onSubmit={handleSubmit} className="space-y-4">
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
                  placeholder={role === 'doctor' ? 'doctor@hospital.org' : 'Enter your email'}
                  value={email}
                  onChange={(e) => setEmail(e.target.value)}
                  className="w-full pl-10 pr-4 py-2.5 rounded-xl border border-warm-border text-sm focus:outline-none focus:ring-2 focus:ring-brand-800/20 focus:border-brand-800"
                />
              </div>
            </div>

            <div>
              <div className="flex items-center justify-between mb-1">
                <label className="block text-xs font-bold text-gray-700 uppercase tracking-wider">
                  Password
                </label>
                {role === 'patient' ? (
                  <Link
                    to="/forgot-password"
                    className="text-xs font-semibold text-brand-800 hover:text-brand-900"
                  >
                    Forgot Password?
                  </Link>
                ) : (
                  <Link
                    to="/doctor/forgot-password"
                    className="text-xs font-semibold text-brand-800 hover:text-brand-900"
                  >
                    Forgot Password?
                  </Link>
                )}
              </div>
              <div className="relative">
                <div className="absolute inset-y-0 left-0 pl-3.5 flex items-center pointer-events-none text-warm-muted">
                  <Lock className="w-4 h-4" />
                </div>
                <input
                  type="password"
                  required
                  placeholder="Enter your password"
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  className="w-full pl-10 pr-4 py-2.5 rounded-xl border border-warm-border text-sm focus:outline-none focus:ring-2 focus:ring-brand-800/20 focus:border-brand-800"
                />
              </div>
            </div>

            <button
              type="submit"
              disabled={loading}
              className="w-full inline-flex items-center justify-center space-x-2 py-3 rounded-full text-sm font-bold text-white bg-brand-800 hover:bg-brand-900 shadow-md shadow-brand-900/20 transition-all disabled:opacity-50 mt-2"
            >
              <span>{loading ? 'Authenticating...' : 'Sign In'}</span>
              <ArrowRight className="w-4 h-4" />
            </button>
          </form>

          {/* Footer Link */}
          <div className="text-center pt-2">
            <p className="text-xs text-warm-muted">
              Don't have an account?{' '}
              <Link to="/register" className="font-bold text-brand-800 hover:text-brand-900 underline">
                Register here
              </Link>
            </p>
          </div>
        </div>
      </main>

      <Footer />
    </div>
  );
}
