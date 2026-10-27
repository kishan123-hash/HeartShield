import React, { useState, useEffect } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import {
  Shield,
  Heart,
  Lock,
  Mail,
  AlertCircle,
  CheckCircle2,
  ArrowRight,
  ArrowLeft,
  Eye,
  EyeOff,
  RefreshCw
} from 'lucide-react';
import api from '../api/client';
import Navbar from '../components/Navbar';
import Footer from '../components/Footer';

export default function ForgotPasswordPage() {
  // Wizard steps: 1 = Enter Email, 2 = Verify 6-digit OTP, 3 = Set New Password
  const [step, setStep] = useState(1);
  const [email, setEmail] = useState('');
  const [otp, setOtp] = useState('');
  const [resetToken, setResetToken] = useState('');
  const [newPassword, setNewPassword] = useState('');
  const [confirmPassword, setConfirmPassword] = useState('');
  const [showNewPassword, setShowNewPassword] = useState(false);
  const [showConfirmPassword, setShowConfirmPassword] = useState(false);

  const [loading, setLoading] = useState(false);
  const [resending, setResending] = useState(false);
  const [error, setError] = useState('');
  const [success, setSuccess] = useState('');
  const [cooldown, setCooldown] = useState(0);

  const navigate = useNavigate();

  // Cooldown countdown timer for OTP resend
  useEffect(() => {
    if (cooldown <= 0) return;
    const timer = setInterval(() => {
      setCooldown((prev) => (prev > 0 ? prev - 1 : 0));
    }, 1000);
    return () => clearInterval(timer);
  }, [cooldown]);

  // Email format validation
  const isValidEmail = (val) => {
    return /^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(val.trim());
  };

  // Step 1: Request OTP via email
  const handleRequestOtp = async (e) => {
    e.preventDefault();
    setError('');
    setSuccess('');

    const trimmedEmail = email.trim().toLowerCase();
    if (!trimmedEmail) {
      setError('Please enter your registered email address.');
      return;
    }

    if (!isValidEmail(trimmedEmail)) {
      setError('Please enter a valid email address (e.g. patient@example.com).');
      return;
    }

    setLoading(true);

    try {
      const res = await api.post('/auth/forgot-password', {
        identifier: trimmedEmail,
        channel: 'email',
      });

      setSuccess(
        res.data?.message ||
          'If an active patient account matches the provided email, a verification code has been dispatched.'
      );
      setStep(2);
      setCooldown(60);
    } catch (err) {
      console.error('Request OTP error:', err);
      const detail = err.response?.data?.detail;
      setError(
        typeof detail === 'string'
          ? detail
          : 'Unable to initiate password recovery. Please try again.'
      );
    } finally {
      setLoading(false);
    }
  };

  // Resend OTP in Step 2 with cooldown protection
  const handleResendOtp = async () => {
    if (cooldown > 0 || resending) return;
    setError('');
    setSuccess('');
    setResending(true);

    try {
      const res = await api.post('/auth/forgot-password', {
        identifier: email.trim().toLowerCase(),
        channel: 'email',
      });
      setSuccess(
        res.data?.message || 'A new verification code has been dispatched to your email.'
      );
      setCooldown(60);
    } catch (err) {
      console.error('Resend OTP error:', err);
      const detail = err.response?.data?.detail;
      setError(
        typeof detail === 'string'
          ? detail
          : 'Failed to resend verification code. Please wait before retrying.'
      );
    } finally {
      setResending(false);
    }
  };

  // Step 2: Verify OTP
  const handleVerifyOtp = async (e) => {
    e.preventDefault();
    setError('');
    setSuccess('');

    const cleanOtp = otp.trim();
    if (!cleanOtp || cleanOtp.length !== 6 || !/^\d{6}$/.test(cleanOtp)) {
      setError('Please enter the complete 6-digit verification code.');
      return;
    }

    setLoading(true);

    try {
      const res = await api.post('/auth/verify-otp', {
        email: email.trim().toLowerCase(),
        otp: cleanOtp,
        purpose: 'password_reset',
      });

      if (res.data?.verified) {
        if (res.data.reset_token) {
          setResetToken(res.data.reset_token);
        }
        setSuccess('Code verified successfully! Please enter your new password.');
        setStep(3);
      } else {
        setError('Verification failed. Please check the code and try again.');
      }
    } catch (err) {
      console.error('Verify OTP error:', err);
      const detail = err.response?.data?.detail;
      setError(
        typeof detail === 'string'
          ? detail
          : 'Invalid or expired verification code. Please check and try again.'
      );
    } finally {
      setLoading(false);
    }
  };

  // Step 3: Set New Password
  const handleResetPassword = async (e) => {
    e.preventDefault();
    setError('');
    setSuccess('');

    if (newPassword.length < 6) {
      setError('Password must be at least 6 characters long.');
      return;
    }

    if (newPassword !== confirmPassword) {
      setError('Passwords do not match. Please verify both fields.');
      return;
    }

    setLoading(true);

    try {
      await api.post('/auth/reset-password', {
        identifier: email.trim().toLowerCase(),
        token: resetToken || otp.trim(),
        new_password: newPassword,
      });

      setSuccess('Password updated successfully! Redirecting to sign in...');
      setTimeout(() => {
        navigate('/login?reset=success');
      }, 1500);
    } catch (err) {
      console.error('Reset password error:', err);
      const detail = err.response?.data?.detail;
      setError(
        typeof detail === 'string'
          ? detail
          : 'Unable to update password. Your session may have expired. Please restart recovery.'
      );
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen flex flex-col bg-warm-bg text-warm-dark">
      <Navbar />

      <main className="flex-1 flex items-center justify-center px-4 py-8 sm:py-16">
        <div className="w-full max-w-md bg-white rounded-3xl border border-warm-border shadow-md p-6 sm:p-10 space-y-6">
          {/* Brand Header */}
          <div className="text-center space-y-2">
            <div className="w-14 h-14 rounded-2xl bg-gradient-to-br from-brand-800 to-brand-900 flex items-center justify-center text-white mx-auto shadow-md shadow-brand-900/20">
              <div className="relative">
                <Shield className="w-8 h-8 text-white" />
                <Heart className="w-4 h-4 text-rose-300 absolute inset-0 m-auto fill-rose-300" />
              </div>
            </div>
            <div>
              <span className="text-[10px] font-bold uppercase tracking-wider text-brand-800 bg-brand-50 px-2.5 py-0.5 rounded-full border border-brand-200">
                Patient Portal
              </span>
              <h2 className="text-xl sm:text-2xl font-black text-gray-900 tracking-tight mt-1">
                {step === 1 && 'Reset Password'}
                {step === 2 && 'Verify Security Code'}
                {step === 3 && 'Set New Password'}
              </h2>
            </div>
            <p className="text-xs text-warm-muted leading-relaxed max-w-sm mx-auto">
              {step === 1 &&
                'Enter your registered email address to receive a secure 6-digit recovery code.'}
              {step === 2 && (
                <>
                  We sent a 6-digit code to{' '}
                  <span className="font-semibold text-gray-900 break-all">{email}</span>.
                </>
              )}
              {step === 3 && 'Create a strong, secure new password for your patient account.'}
            </p>
          </div>

          {/* Progress Indicator */}
          <div className="flex items-center justify-center space-x-2 pt-1 pb-2">
            <div
              className={`h-1.5 rounded-full transition-all ${
                step >= 1 ? 'w-8 bg-brand-800' : 'w-4 bg-gray-200'
              }`}
            />
            <div
              className={`h-1.5 rounded-full transition-all ${
                step >= 2 ? 'w-8 bg-brand-800' : 'w-4 bg-gray-200'
              }`}
            />
            <div
              className={`h-1.5 rounded-full transition-all ${
                step >= 3 ? 'w-8 bg-brand-800' : 'w-4 bg-gray-200'
              }`}
            />
          </div>

          {/* Alert Messages */}
          {error && (
            <div className="p-3.5 rounded-xl bg-rose-50 border border-rose-200 text-rose-700 text-xs font-semibold flex items-start space-x-2">
              <AlertCircle className="w-4 h-4 shrink-0 mt-0.5" />
              <span className="leading-relaxed">{error}</span>
            </div>
          )}

          {success && (
            <div className="p-3.5 rounded-xl bg-emerald-50 border border-emerald-200 text-emerald-800 text-xs font-semibold flex items-start space-x-2">
              <CheckCircle2 className="w-4 h-4 shrink-0 mt-0.5" />
              <span className="leading-relaxed">{success}</span>
            </div>
          )}

          {/* STEP 1: Enter Email */}
          {step === 1 && (
            <form onSubmit={handleRequestOtp} className="space-y-4">
              <div>
                <label
                  htmlFor="patient-email"
                  className="block text-xs font-bold text-gray-700 uppercase tracking-wider mb-1"
                >
                  Registered Email Address
                </label>
                <div className="relative">
                  <div className="absolute inset-y-0 left-0 pl-3.5 flex items-center pointer-events-none text-warm-muted">
                    <Mail className="w-4 h-4" />
                  </div>
                  <input
                    id="patient-email"
                    type="email"
                    required
                    autoComplete="email"
                    placeholder="patient@example.com"
                    value={email}
                    onChange={(e) => setEmail(e.target.value)}
                    className="w-full pl-10 pr-4 py-2.5 rounded-xl border border-warm-border text-sm focus:outline-none focus:ring-2 focus:ring-brand-800/20 focus:border-brand-800 transition-all"
                  />
                </div>
              </div>

              <button
                type="submit"
                disabled={loading}
                className="w-full inline-flex items-center justify-center space-x-2 py-3 rounded-full text-sm font-bold text-white bg-brand-800 hover:bg-brand-900 active:scale-[0.99] shadow-md shadow-brand-900/20 transition-all disabled:opacity-50 min-h-[44px]"
              >
                <span>{loading ? 'Sending Code...' : 'Send Recovery Code'}</span>
                <ArrowRight className="w-4 h-4" />
              </button>
            </form>
          )}

          {/* STEP 2: Verify OTP */}
          {step === 2 && (
            <form onSubmit={handleVerifyOtp} className="space-y-4">
              <div>
                <label
                  htmlFor="otp-input"
                  className="block text-xs font-bold text-gray-700 uppercase tracking-wider mb-1 text-center"
                >
                  6-Digit Verification Code
                </label>
                <input
                  id="otp-input"
                  type="text"
                  inputMode="numeric"
                  autoComplete="one-time-code"
                  pattern="\d{6}"
                  maxLength={6}
                  required
                  placeholder="000000"
                  value={otp}
                  onChange={(e) => setOtp(e.target.value.replace(/\D/g, '').slice(0, 6))}
                  className="w-full px-4 py-3 rounded-xl border border-warm-border text-center font-mono text-xl sm:text-2xl tracking-[0.3em] font-bold focus:outline-none focus:ring-2 focus:ring-brand-800/20 focus:border-brand-800 transition-all"
                />
              </div>

              <button
                type="submit"
                disabled={loading || otp.length !== 6}
                className="w-full inline-flex items-center justify-center space-x-2 py-3 rounded-full text-sm font-bold text-white bg-brand-800 hover:bg-brand-900 active:scale-[0.99] shadow-md shadow-brand-900/20 transition-all disabled:opacity-50 min-h-[44px]"
              >
                <span>{loading ? 'Verifying Code...' : 'Verify Code'}</span>
                <ArrowRight className="w-4 h-4" />
              </button>

              {/* Resend Cooldown and Edit Email */}
              <div className="flex flex-col sm:flex-row items-center justify-between text-xs text-warm-muted pt-2 gap-2">
                <button
                  type="button"
                  onClick={() => {
                    setStep(1);
                    setError('');
                    setSuccess('');
                  }}
                  className="inline-flex items-center space-x-1 text-brand-800 hover:text-brand-900 font-semibold underline"
                >
                  <ArrowLeft className="w-3.5 h-3.5" />
                  <span>Change email</span>
                </button>

                {cooldown > 0 ? (
                  <span className="text-gray-500 font-medium">
                    Resend code in <strong className="text-brand-800">{cooldown}s</strong>
                  </span>
                ) : (
                  <button
                    type="button"
                    onClick={handleResendOtp}
                    disabled={resending}
                    className="inline-flex items-center space-x-1 font-bold text-brand-800 hover:text-brand-900 underline disabled:opacity-50"
                  >
                    <RefreshCw className={`w-3.5 h-3.5 ${resending ? 'animate-spin' : ''}`} />
                    <span>Resend code</span>
                  </button>
                )}
              </div>
            </form>
          )}

          {/* STEP 3: Set New Password */}
          {step === 3 && (
            <form onSubmit={handleResetPassword} className="space-y-4">
              <div>
                <label
                  htmlFor="new-password"
                  className="block text-xs font-bold text-gray-700 uppercase tracking-wider mb-1"
                >
                  New Password
                </label>
                <div className="relative">
                  <div className="absolute inset-y-0 left-0 pl-3.5 flex items-center pointer-events-none text-warm-muted">
                    <Lock className="w-4 h-4" />
                  </div>
                  <input
                    id="new-password"
                    type={showNewPassword ? 'text' : 'password'}
                    required
                    placeholder="At least 6 characters"
                    value={newPassword}
                    onChange={(e) => setNewPassword(e.target.value)}
                    className="w-full pl-10 pr-10 py-2.5 rounded-xl border border-warm-border text-sm focus:outline-none focus:ring-2 focus:ring-brand-800/20 focus:border-brand-800 transition-all"
                  />
                  <button
                    type="button"
                    onClick={() => setShowNewPassword(!showNewPassword)}
                    className="absolute inset-y-0 right-0 pr-3.5 flex items-center text-warm-muted hover:text-gray-700"
                    aria-label={showNewPassword ? 'Hide password' : 'Show password'}
                  >
                    {showNewPassword ? <EyeOff className="w-4 h-4" /> : <Eye className="w-4 h-4" />}
                  </button>
                </div>
              </div>

              <div>
                <label
                  htmlFor="confirm-password"
                  className="block text-xs font-bold text-gray-700 uppercase tracking-wider mb-1"
                >
                  Confirm New Password
                </label>
                <div className="relative">
                  <div className="absolute inset-y-0 left-0 pl-3.5 flex items-center pointer-events-none text-warm-muted">
                    <Lock className="w-4 h-4" />
                  </div>
                  <input
                    id="confirm-password"
                    type={showConfirmPassword ? 'text' : 'password'}
                    required
                    placeholder="Re-enter new password"
                    value={confirmPassword}
                    onChange={(e) => setConfirmPassword(e.target.value)}
                    className="w-full pl-10 pr-10 py-2.5 rounded-xl border border-warm-border text-sm focus:outline-none focus:ring-2 focus:ring-brand-800/20 focus:border-brand-800 transition-all"
                  />
                  <button
                    type="button"
                    onClick={() => setShowConfirmPassword(!showConfirmPassword)}
                    className="absolute inset-y-0 right-0 pr-3.5 flex items-center text-warm-muted hover:text-gray-700"
                    aria-label={showConfirmPassword ? 'Hide password' : 'Show password'}
                  >
                    {showConfirmPassword ? (
                      <EyeOff className="w-4 h-4" />
                    ) : (
                      <Eye className="w-4 h-4" />
                    )}
                  </button>
                </div>
              </div>

              {/* Password Match / Length Helper */}
              {newPassword && (
                <div className="text-[11px] space-y-1 pt-1">
                  <div
                    className={`flex items-center space-x-1.5 ${
                      newPassword.length >= 6 ? 'text-emerald-700 font-semibold' : 'text-gray-500'
                    }`}
                  >
                    <span>{newPassword.length >= 6 ? '✓' : '•'}</span>
                    <span>At least 6 characters long</span>
                  </div>
                  {confirmPassword && (
                    <div
                      className={`flex items-center space-x-1.5 ${
                        newPassword === confirmPassword
                          ? 'text-emerald-700 font-semibold'
                          : 'text-rose-600 font-semibold'
                      }`}
                    >
                      <span>{newPassword === confirmPassword ? '✓' : '•'}</span>
                      <span>
                        {newPassword === confirmPassword
                          ? 'Passwords match'
                          : 'Passwords do not match'}
                      </span>
                    </div>
                  )}
                </div>
              )}

              <button
                type="submit"
                disabled={loading || newPassword.length < 6 || newPassword !== confirmPassword}
                className="w-full inline-flex items-center justify-center space-x-2 py-3 rounded-full text-sm font-bold text-white bg-brand-800 hover:bg-brand-900 active:scale-[0.99] shadow-md shadow-brand-900/20 transition-all disabled:opacity-50 min-h-[44px]"
              >
                <span>{loading ? 'Saving Password...' : 'Save New Password'}</span>
                <ArrowRight className="w-4 h-4" />
              </button>
            </form>
          )}

          {/* Footer Link */}
          <div className="text-center pt-2 border-t border-warm-border/60">
            <Link
              to="/login"
              className="inline-flex items-center space-x-1.5 text-xs font-bold text-brand-800 hover:text-brand-900 underline"
            >
              <ArrowLeft className="w-3.5 h-3.5" />
              <span>Return to Sign In</span>
            </Link>
          </div>
        </div>
      </main>

      <Footer />
    </div>
  );
}
