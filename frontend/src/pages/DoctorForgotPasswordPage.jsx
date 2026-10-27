import React, { useState } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import {
  Shield,
  Heart,
  Lock,
  Mail,
  Clock,
  CheckCircle2,
  XCircle,
  AlertCircle,
  ArrowRight,
  RefreshCw,
  Stethoscope
} from 'lucide-react';
import api from '../api/client';
import Navbar from '../components/Navbar';
import Footer from '../components/Footer';

export default function DoctorForgotPasswordPage() {
  const [email, setEmail] = useState('');
  const [requestSubmitted, setRequestSubmitted] = useState(false);
  const [requestStatus, setRequestStatus] = useState('none'); // 'none', 'pending', 'approved', 'rejected', 'completed'
  const [channel, setChannel] = useState('email'); // 'email', 'sms', 'whatsapp'
  const [otpSent, setOtpSent] = useState(false);
  const [otp, setOtp] = useState('');
  const [newPassword, setNewPassword] = useState('');
  const [confirmPassword, setConfirmPassword] = useState('');
  const [error, setError] = useState('');
  const [success, setSuccess] = useState('');
  const [loading, setLoading] = useState(false);
  const [checkingStatus, setCheckingStatus] = useState(false);

  const navigate = useNavigate();

  // Step 1: Submit Request to Administrator
  const handleSubmitRequest = async (e) => {
    e.preventDefault();
    setError('');
    setSuccess('');
    setLoading(true);

    try {
      const res = await api.post('/auth/doctor/forgot-password/request', {
        email: email.trim().toLowerCase(),
      });
      setRequestSubmitted(true);
      setRequestStatus('pending');
      setSuccess(res.data?.message || 'Your request has been submitted and is awaiting administrator approval.');
    } catch (err) {
      console.error('Doctor reset request error:', err);
      const detail = err.response?.data?.detail;
      setError(typeof detail === 'string' ? detail : 'Unable to submit request. Please verify your email.');
    } finally {
      setLoading(false);
    }
  };

  // Check Status
  const handleCheckStatus = async () => {
    if (!email) return;
    setError('');
    setCheckingStatus(true);

    try {
      const res = await api.get(`/auth/doctor/forgot-password/status?email=${encodeURIComponent(email.trim().toLowerCase())}`);
      const st = res.data?.status || 'none';
      setRequestStatus(st);
      if (st === 'approved') {
        setSuccess('Administrator has approved your password reset request! Choose your OTP delivery channel below.');
      } else if (st === 'pending') {
        setError('Your request is still awaiting administrator review and approval.');
      } else if (st === 'rejected') {
        setError('Your password reset request was rejected by the administrator. Password change is prohibited.');
      } else if (st === 'completed') {
        setError('This request has already been completed. Please submit a new request if needed.');
      } else {
        setError('No active request found for this physician email address.');
      }
    } catch (err) {
      console.error('Status check error:', err);
      setError('Unable to check approval status.');
    } finally {
      setCheckingStatus(false);
    }
  };

  // Step 2: Send OTP (Only enabled when approved)
  const handleSendOtp = async () => {
    setError('');
    setSuccess('');
    setLoading(true);

    try {
      const res = await api.post('/auth/doctor/forgot-password/send-otp', {
        email: email.trim().toLowerCase(),
        channel: channel,
      });
      setOtpSent(true);
      setSuccess(res.data?.message || `Verification code sent via ${channel.toUpperCase()}.`);
    } catch (err) {
      console.error('Doctor send OTP error:', err);
      const detail = err.response?.data?.detail;
      setError(typeof detail === 'string' ? detail : 'Failed to deliver OTP. Please check channel availability.');
    } finally {
      setLoading(false);
    }
  };

  // Step 3: Complete Reset
  const handleResetPassword = async (e) => {
    e.preventDefault();
    setError('');

    if (newPassword !== confirmPassword) {
      setError('Passwords do not match.');
      return;
    }

    if (newPassword.length < 6) {
      setError('Password must be at least 6 characters.');
      return;
    }

    if (otp.trim().length !== 6) {
      setError('Please enter the 6-digit verification code.');
      return;
    }

    setLoading(true);

    try {
      await api.post('/auth/doctor/forgot-password/reset', {
        email: email.trim().toLowerCase(),
        otp: otp.trim(),
        new_password: newPassword,
      });

      setSuccess('Physician password updated successfully! Redirecting to login...');
      setTimeout(() => {
        navigate('/login?reset=success');
      }, 1500);
    } catch (err) {
      console.error('Doctor reset completion error:', err);
      const detail = err.response?.data?.detail;
      setError(typeof detail === 'string' ? detail : 'Verification code invalid or request expired.');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen flex flex-col bg-warm-bg">
      <Navbar />

      <main className="flex-1 flex items-center justify-center px-4 py-8 sm:py-16">
        <div className="w-full max-w-lg bg-white rounded-3xl border border-warm-border shadow-md p-6 sm:p-10 space-y-6">
          {/* Header */}
          <div className="text-center space-y-2">
            <div className="w-14 h-14 rounded-2xl bg-gradient-to-br from-brand-800 to-brand-900 flex items-center justify-center text-white mx-auto shadow-md shadow-brand-900/20">
              <Stethoscope className="w-7 h-7" />
            </div>
            <div>
              <span className="text-[10px] font-bold uppercase tracking-wider text-brand-800 bg-brand-50 px-2.5 py-0.5 rounded-full border border-brand-200">
                Physician Security Protocol
              </span>
              <h2 className="text-2xl font-black text-gray-900 tracking-tight mt-1">
                Doctor Password Recovery
              </h2>
            </div>
            <p className="text-xs text-warm-muted leading-relaxed">
              Clinical accounts require administrator authorization before a password reset can be initiated.
            </p>
          </div>

          {/* Feedback Alerts */}
          {error && (
            <div className="p-3.5 rounded-xl bg-rose-50 border border-rose-200 text-rose-700 text-xs font-semibold flex items-start space-x-2">
              <AlertCircle className="w-4 h-4 shrink-0 mt-0.5" />
              <span>{error}</span>
            </div>
          )}

          {success && (
            <div className="p-3.5 rounded-xl bg-emerald-50 border border-emerald-200 text-emerald-800 text-xs font-semibold flex items-start space-x-2">
              <CheckCircle2 className="w-4 h-4 shrink-0 mt-0.5" />
              <span>{success}</span>
            </div>
          )}

          {/* Step 1: Initial Request Form */}
          {!requestSubmitted && requestStatus !== 'approved' && (
            <form onSubmit={handleSubmitRequest} className="space-y-4">
              <div>
                <label className="block text-xs font-bold text-gray-700 uppercase tracking-wider mb-1">
                  Registered Physician Email
                </label>
                <div className="relative">
                  <div className="absolute inset-y-0 left-0 pl-3.5 flex items-center pointer-events-none text-warm-muted">
                    <Mail className="w-4 h-4" />
                  </div>
                  <input
                    type="email"
                    required
                    placeholder="doctor@hospital.org"
                    value={email}
                    onChange={(e) => setEmail(e.target.value)}
                    className="w-full pl-10 pr-4 py-2.5 rounded-xl border border-warm-border text-sm focus:outline-none focus:ring-2 focus:ring-brand-800/20 focus:border-brand-800"
                  />
                </div>
              </div>

              <button
                type="submit"
                disabled={loading}
                className="w-full inline-flex items-center justify-center space-x-2 py-3 rounded-full text-sm font-bold text-white bg-brand-800 hover:bg-brand-900 shadow-md shadow-brand-900/20 transition-all disabled:opacity-50"
              >
                <span>{loading ? 'Submitting Request...' : 'Submit Request to Administrator'}</span>
                <ArrowRight className="w-4 h-4" />
              </button>
            </form>
          )}

          {/* Step 2: Request is Pending Approval */}
          {requestSubmitted && requestStatus === 'pending' && (
            <div className="space-y-5 rounded-2xl bg-amber-50/70 border border-amber-200/80 p-5 text-center">
              <div className="w-10 h-10 rounded-full bg-amber-100 text-amber-800 flex items-center justify-center mx-auto">
                <Clock className="w-5 h-5 animate-pulse" />
              </div>
              <div>
                <h3 className="text-sm font-bold text-amber-900">Awaiting Administrator Approval</h3>
                <p className="text-xs text-amber-800/90 mt-1 leading-relaxed">
                  Your request has been logged. An administrator must approve this credential reset from the governance console before you can proceed with OTP verification.
                </p>
              </div>

              <div className="flex flex-col sm:flex-row gap-2 pt-2">
                <button
                  type="button"
                  onClick={handleCheckStatus}
                  disabled={checkingStatus}
                  className="flex-1 inline-flex items-center justify-center space-x-2 py-2.5 rounded-xl text-xs font-bold text-amber-900 bg-white border border-amber-300 hover:bg-amber-100/50 transition-all disabled:opacity-50"
                >
                  <RefreshCw className={`w-3.5 h-3.5 ${checkingStatus ? 'animate-spin' : ''}`} />
                  <span>{checkingStatus ? 'Checking...' : 'Check Approval Status'}</span>
                </button>
              </div>
            </div>
          )}

          {/* Step 2b: Request was Rejected */}
          {requestStatus === 'rejected' && (
            <div className="space-y-4 rounded-2xl bg-rose-50 border border-rose-200 p-5 text-center">
              <div className="w-10 h-10 rounded-full bg-rose-100 text-rose-700 flex items-center justify-center mx-auto">
                <XCircle className="w-5 h-5" />
              </div>
              <div>
                <h3 className="text-sm font-bold text-rose-900">Request Rejected by Administrator</h3>
                <p className="text-xs text-rose-700 mt-1">
                  Your password recovery request was not approved. Password alteration is blocked. Please contact your hospital system administrator.
                </p>
              </div>
            </div>
          )}

          {/* Step 3: Approved -> OTP Dispatch */}
          {requestStatus === 'approved' && !otpSent && (
            <div className="space-y-5">
              <div className="p-4 rounded-2xl bg-emerald-50 border border-emerald-200 flex items-center space-x-3">
                <CheckCircle2 className="w-5 h-5 text-emerald-700 shrink-0" />
                <div>
                  <p className="text-xs font-bold text-emerald-900">Administrator Approval Granted</p>
                  <p className="text-[11px] text-emerald-700">
                    Your password recovery request has been verified. Click below to receive a 6-digit OTP code at your registered email address ({email}).
                  </p>
                </div>
              </div>

              <button
                type="button"
                onClick={handleSendOtp}
                disabled={loading}
                className="w-full inline-flex items-center justify-center space-x-2 py-3 rounded-full text-sm font-bold text-white bg-brand-800 hover:bg-brand-900 shadow-md shadow-brand-900/20 transition-all disabled:opacity-50"
              >
                <span>{loading ? 'Dispatching OTP...' : 'Send Verification OTP to Email'}</span>
                <ArrowRight className="w-4 h-4" />
              </button>
            </div>
          )}

          {/* Step 4: Approved & OTP Sent -> Enter OTP and New Password */}
          {requestStatus === 'approved' && otpSent && (
            <form onSubmit={handleResetPassword} className="space-y-4">
              <div>
                <label className="block text-xs font-bold text-gray-700 uppercase tracking-wider mb-1">
                  6-Digit Verification Code
                </label>
                <input
                  type="text"
                  required
                  maxLength={6}
                  placeholder="123456"
                  value={otp}
                  onChange={(e) => setOtp(e.target.value.replace(/\D/g, ''))}
                  className="w-full px-4 py-2.5 rounded-xl border border-warm-border text-sm font-mono tracking-widest text-center focus:outline-none focus:ring-2 focus:ring-brand-800/20 focus:border-brand-800"
                />
              </div>

              <div>
                <label className="block text-xs font-bold text-gray-700 uppercase tracking-wider mb-1">
                  New Password
                </label>
                <div className="relative">
                  <div className="absolute inset-y-0 left-0 pl-3.5 flex items-center pointer-events-none text-warm-muted">
                    <Lock className="w-4 h-4" />
                  </div>
                  <input
                    type="password"
                    required
                    placeholder="Enter new password"
                    value={newPassword}
                    onChange={(e) => setNewPassword(e.target.value)}
                    className="w-full pl-10 pr-4 py-2.5 rounded-xl border border-warm-border text-sm focus:outline-none focus:ring-2 focus:ring-brand-800/20 focus:border-brand-800"
                  />
                </div>
              </div>

              <div>
                <label className="block text-xs font-bold text-gray-700 uppercase tracking-wider mb-1">
                  Confirm New Password
                </label>
                <div className="relative">
                  <div className="absolute inset-y-0 left-0 pl-3.5 flex items-center pointer-events-none text-warm-muted">
                    <Lock className="w-4 h-4" />
                  </div>
                  <input
                    type="password"
                    required
                    placeholder="Confirm new password"
                    value={confirmPassword}
                    onChange={(e) => setConfirmPassword(e.target.value)}
                    className="w-full pl-10 pr-4 py-2.5 rounded-xl border border-warm-border text-sm focus:outline-none focus:ring-2 focus:ring-brand-800/20 focus:border-brand-800"
                  />
                </div>
              </div>

              <button
                type="submit"
                disabled={loading}
                className="w-full inline-flex items-center justify-center space-x-2 py-3 rounded-full text-sm font-bold text-white bg-brand-800 hover:bg-brand-900 shadow-md shadow-brand-900/20 transition-all disabled:opacity-50"
              >
                <span>{loading ? 'Saving Password...' : 'Reset Physician Password'}</span>
                <ArrowRight className="w-4 h-4" />
              </button>

              <div className="text-center pt-2">
                <button
                  type="button"
                  onClick={handleSendOtp}
                  disabled={loading}
                  className="text-xs font-semibold text-brand-800 hover:text-brand-900 underline"
                >
                  Resend OTP code
                </button>
              </div>
            </form>
          )}

          {/* Footer Back Link */}
          <div className="text-center pt-2">
            <Link to="/login" className="text-xs font-bold text-brand-800 hover:text-brand-900 underline">
              Return to Sign In
            </Link>
          </div>
        </div>
      </main>

      <Footer />
    </div>
  );
}
