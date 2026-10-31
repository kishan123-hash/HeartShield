import React, { useState, useEffect } from 'react';
import { useLocation, useNavigate, Link } from 'react-router-dom';
import {
  Shield,
  Lock,
  Mail,
  AlertCircle,
  CheckCircle2,
  ArrowRight,
  KeyRound,
  RefreshCw,
  Eye,
  EyeOff
} from 'lucide-react';
import api from '../api/client';
import Navbar from '../components/Navbar';
import Footer from '../components/Footer';

export default function UnlockAccountPage() {
  const [token, setToken] = useState('');
  const [mode, setMode] = useState('yes'); // 'yes' = Current Password Unlock, 'reset' = NO IT WAS NOT ME (OTP + Reset)
  const [validating, setValidating] = useState(true);
  const [tokenValid, setTokenValid] = useState(false);
  const [tokenError, setTokenError] = useState('');

  // User details returned from validated token
  const [userEmail, setUserEmail] = useState('');
  const [maskedEmail, setMaskedEmail] = useState('');

  // Option 1: Current Password
  const [password, setPassword] = useState('');
  const [showPassword, setShowPassword] = useState(false);

  // Option 2: OTP & Reset Password
  const [otp, setOtp] = useState('');
  const [otpSent, setOtpSent] = useState(false);
  const [sendingOtp, setSendingOtp] = useState(false);
  const [newPassword, setNewPassword] = useState('');
  const [confirmPassword, setConfirmPassword] = useState('');
  const [showNewPassword, setShowNewPassword] = useState(false);
  const [showConfirmPassword, setShowConfirmPassword] = useState(false);
  const [cooldown, setCooldown] = useState(0);

  const [error, setError] = useState('');
  const [success, setSuccess] = useState('');
  const [loading, setLoading] = useState(false);

  const location = useLocation();
  const navigate = useNavigate();

  // Cooldown countdown timer for OTP resend
  useEffect(() => {
    if (cooldown <= 0) return;
    const timer = setInterval(() => {
      setCooldown((prev) => (prev > 0 ? prev - 1 : 0));
    }, 1000);
    return () => clearInterval(timer);
  }, [cooldown]);

  // Initial token verification
  useEffect(() => {
    const params = new URLSearchParams(location.search);
    const qToken = params.get('token');
    const qAction = params.get('action');

    if (!qToken) {
      setValidating(false);
      setTokenValid(false);
      setTokenError('No security verification token found in URL.');
      return;
    }

    setToken(qToken);
    if (qAction === 'reset') {
      setMode('reset');
    }

    const validateToken = async () => {
      try {
        const res = await api.get('/auth/unlock/verify-token', {
          params: { token: qToken },
        });
        setTokenValid(true);
        if (res.data?.email) setUserEmail(res.data.email);
        if (res.data?.masked_email) setMaskedEmail(res.data.masked_email);

        // If the user arrived via the "NO, IT WAS NOT ME" link, trigger recovery OTP dispatch
        if (qAction === 'reset') {
          try {
            const otpRes = await api.post('/auth/unlock/request-otp', {
              token: qToken,
            });
            setOtpSent(true);
            setCooldown(60);
            setSuccess(otpRes.data?.message || 'A 6-digit verification code has been dispatched.');
          } catch (otpErr) {
            console.warn('Initial OTP dispatch notice:', otpErr);
          }
        }
      } catch (err) {
        console.error('Token verification error:', err);
        const detail = err.response?.data?.detail;
        setTokenValid(false);
        setTokenError(
          typeof detail === 'string'
            ? detail
            : 'Verification link is invalid or has expired.'
        );
      } finally {
        setValidating(false);
      }
    };

    validateToken();
  }, [location]);

  // Option 1 Submit: YES, IT WAS ME (Verify Current Password)
  const handleCurrentPasswordSubmit = async (e) => {
    e.preventDefault();
    if (!password) {
      setError('Please enter your current account password.');
      return;
    }

    setError('');
    setLoading(true);

    try {
      const res = await api.post('/auth/unlock/confirm', {
        token: token,
        password: password,
      });

      setSuccess(res.data?.message || 'Account successfully unlocked! You may now sign in.');
      setTimeout(() => {
        navigate('/login');
      }, 2000);
    } catch (err) {
      console.error('Account unlock confirmation error:', err);
      const detail = err.response?.data?.detail;
      setError(
        typeof detail === 'string'
          ? detail
          : 'Verification failed. Please check your password.'
      );
    } finally {
      setLoading(false);
    }
  };

  // Option 2: Request / Resend Recovery OTP
  const handleRequestOtp = async () => {
    if (cooldown > 0 || sendingOtp) return;
    setError('');
    setSendingOtp(true);

    try {
      const res = await api.post('/auth/unlock/request-otp', {
        token: token,
      });
      setOtpSent(true);
      setCooldown(60);
      setSuccess(res.data?.message || 'A 6-digit verification code has been sent to your email.');
    } catch (err) {
      console.error('Request OTP error:', err);
      const detail = err.response?.data?.detail;
      setError(
        typeof detail === 'string'
          ? detail
          : 'Unable to send verification code. Please try again.'
      );
    } finally {
      setSendingOtp(false);
    }
  };

  // Option 2 Submit: NO, IT WAS NOT ME (Verify OTP + Reset Password)
  const handleResetPasswordSubmit = async (e) => {
    e.preventDefault();
    setError('');

    const cleanOtp = otp.trim();
    if (!cleanOtp || cleanOtp.length !== 6 || !/^\d{6}$/.test(cleanOtp)) {
      setError('Please enter the complete 6-digit verification code.');
      return;
    }

    if (newPassword.length < 6) {
      setError('New password must be at least 6 characters long.');
      return;
    }

    if (newPassword !== confirmPassword) {
      setError('Passwords do not match. Please verify both fields.');
      return;
    }

    setLoading(true);

    try {
      const res = await api.post('/auth/unlock/reset-password', {
        token: token,
        otp: cleanOtp,
        new_password: newPassword,
        confirm_password: confirmPassword,
      });

      setSuccess(
        res.data?.message ||
          'Password reset successfully and account has been unlocked! Redirecting to sign in...'
      );
      setTimeout(() => {
        navigate('/login?reset=success');
      }, 2000);
    } catch (err) {
      console.error('Reset password error:', err);
      const detail = err.response?.data?.detail;
      setError(
        typeof detail === 'string'
          ? detail
          : 'Failed to reset password. Please verify the code and try again.'
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
          {/* Header */}
          <div className="text-center space-y-2">
            <div className="w-16 h-16 bg-red-50 rounded-2xl flex items-center justify-center mx-auto text-brand-800 border border-red-100">
              <Shield className="w-8 h-8" />
            </div>
            <h2 className="text-2xl font-black text-gray-900 tracking-tight">
              Restore Account Access
            </h2>
            <p className="text-xs text-warm-muted leading-relaxed">
              We detected suspicious login activity and blocked sign-in for your protection.
              Verify your identity below to restore full account access.
            </p>
          </div>

          {/* Validating State */}
          {validating && (
            <div className="py-6 text-center text-xs font-semibold text-warm-muted flex flex-col items-center justify-center space-y-2">
              <div className="w-6 h-6 border-2 border-brand-800 border-t-transparent rounded-full animate-spin"></div>
              <span>Validating security verification link...</span>
            </div>
          )}

          {/* Token Invalid / Expired State */}
          {!validating && !tokenValid && (
            <div className="space-y-4">
              <div className="p-4 rounded-xl bg-rose-50 border border-rose-200 text-rose-700 text-xs font-semibold flex items-start space-x-2">
                <AlertCircle className="w-5 h-5 shrink-0 mt-0.5" />
                <div>
                  <p className="font-bold">Verification Link Invalid or Expired</p>
                  <p className="font-normal mt-1">{tokenError}</p>
                </div>
              </div>
              <p className="text-xs text-warm-muted text-center leading-relaxed">
                If you did not generate this request or the token has expired, you can recover access by resetting your password.
              </p>
              <div className="space-y-2 pt-2">
                <Link
                  to="/forgot-password"
                  className="w-full inline-flex items-center justify-center space-x-2 py-2.5 rounded-full text-xs font-bold text-white bg-brand-800 hover:bg-brand-900 transition-all shadow-sm"
                >
                  <span>Reset Patient Password</span>
                  <ArrowRight className="w-3.5 h-3.5" />
                </Link>
                <Link
                  to="/doctor/forgot-password"
                  className="w-full inline-flex items-center justify-center space-x-2 py-2.5 rounded-full text-xs font-bold text-gray-700 bg-gray-100 hover:bg-gray-200 transition-all"
                >
                  <span>Doctor Password Recovery</span>
                </Link>
                <Link
                  to="/login"
                  className="block text-center text-xs text-brand-800 hover:underline pt-2 font-semibold"
                >
                  Return to Sign In
                </Link>
              </div>
            </div>
          )}

          {/* Registered Email Identity Banner */}
          {!validating && tokenValid && (userEmail || maskedEmail) && (
            <div className="p-3 bg-amber-50/70 border border-amber-200 rounded-xl flex items-center space-x-2.5 text-xs text-amber-900">
              <Mail className="w-4 h-4 text-amber-700 shrink-0" />
              <div>
                <span className="font-bold">Registered Account: </span>
                <span className="font-mono">{maskedEmail || userEmail}</span>
              </div>
            </div>
          )}

          {/* Recovery Flow Switcher Tabs */}
          {!validating && tokenValid && !success && (
            <div className="grid grid-cols-2 p-1 bg-warm-bg rounded-xl border border-warm-border">
              <button
                type="button"
                onClick={() => {
                  setMode('yes');
                  setError('');
                }}
                className={`py-2 text-xs font-bold rounded-lg transition-all ${
                  mode === 'yes'
                    ? 'bg-brand-800 text-white shadow-xs'
                    : 'text-gray-600 hover:text-brand-800'
                }`}
              >
                YES, IT WAS ME
              </button>
              <button
                type="button"
                onClick={() => {
                  setMode('reset');
                  setError('');
                  if (!otpSent) handleRequestOtp();
                }}
                className={`py-2 text-xs font-bold rounded-lg transition-all ${
                  mode === 'reset'
                    ? 'bg-brand-800 text-white shadow-xs'
                    : 'text-gray-600 hover:text-brand-800'
                }`}
              >
                NO, NOT ME
              </button>
            </div>
          )}

          {/* Success Notification */}
          {success && (
            <div className="p-3.5 rounded-xl bg-emerald-50 border border-emerald-200 text-emerald-800 text-xs font-semibold flex items-center space-x-2">
              <CheckCircle2 className="w-4 h-4 shrink-0" />
              <span>{success}</span>
            </div>
          )}

          {/* Error Message */}
          {error && (
            <div className="p-3.5 rounded-xl bg-rose-50 border border-rose-200 text-rose-700 text-xs font-semibold flex items-center space-x-2">
              <AlertCircle className="w-4 h-4 shrink-0" />
              <span>{error}</span>
            </div>
          )}

          {/* OPTION 1: YES, IT WAS ME (Verify Current Password) */}
          {!validating && tokenValid && !success && mode === 'yes' && (
            <form onSubmit={handleCurrentPasswordSubmit} className="space-y-4">
              <div>
                <label className="block text-xs font-bold text-gray-700 uppercase tracking-wider mb-1">
                  Confirm Current Password
                </label>
                <div className="relative">
                  <div className="absolute inset-y-0 left-0 pl-3.5 flex items-center pointer-events-none text-warm-muted">
                    <Lock className="w-4 h-4" />
                  </div>
                  <input
                    type={showPassword ? 'text' : 'password'}
                    required
                    placeholder="Enter your current password"
                    value={password}
                    onChange={(e) => setPassword(e.target.value)}
                    className="w-full pl-10 pr-10 py-2.5 rounded-xl border border-warm-border text-sm focus:outline-none focus:ring-2 focus:ring-brand-800/20 focus:border-brand-800"
                  />
                  <button
                    type="button"
                    onClick={() => setShowPassword(!showPassword)}
                    className="absolute inset-y-0 right-0 pr-3.5 flex items-center text-warm-muted hover:text-gray-700"
                  >
                    {showPassword ? <EyeOff className="w-4 h-4" /> : <Eye className="w-4 h-4" />}
                  </button>
                </div>
                <p className="text-[11px] text-warm-muted mt-1.5 leading-relaxed">
                  Confirming your current password proves ownership and immediately clears the account lock.
                </p>
              </div>

              <button
                type="submit"
                disabled={loading}
                className="w-full inline-flex items-center justify-center space-x-2 py-3 rounded-full text-sm font-bold text-white bg-emerald-700 hover:bg-emerald-800 shadow-md shadow-emerald-800/20 transition-all disabled:opacity-50 mt-2"
              >
                <span>{loading ? 'Verifying Identity...' : 'YES, IT WAS ME — UNLOCK ACCOUNT'}</span>
                <ArrowRight className="w-4 h-4" />
              </button>

              <div className="pt-2 text-center border-t border-warm-border/60">
                <p className="text-xs text-rose-700 font-semibold mb-1">
                  Did not recognize these login attempts?
                </p>
                <button
                  type="button"
                  onClick={() => {
                    setMode('reset');
                    setError('');
                    if (!otpSent) handleRequestOtp();
                  }}
                  className="text-xs font-bold text-brand-800 hover:underline"
                >
                  NO, IT WAS NOT ME — Secure Account & Reset Password
                </button>
              </div>
            </form>
          )}

          {/* OPTION 2: NO, IT WAS NOT ME (OTP + Reset Password) */}
          {!validating && tokenValid && !success && mode === 'reset' && (
            <form onSubmit={handleResetPasswordSubmit} className="space-y-4">
              <div>
                <div className="flex items-center justify-between mb-1">
                  <label className="block text-xs font-bold text-gray-700 uppercase tracking-wider">
                    6-Digit Security Code (OTP)
                  </label>
                  <button
                    type="button"
                    onClick={handleRequestOtp}
                    disabled={cooldown > 0 || sendingOtp}
                    className="text-[11px] font-bold text-brand-800 hover:underline inline-flex items-center space-x-1 disabled:opacity-50"
                  >
                    <RefreshCw className={`w-3 h-3 ${sendingOtp ? 'animate-spin' : ''}`} />
                    <span>{cooldown > 0 ? `Resend (${cooldown}s)` : 'Resend Code'}</span>
                  </button>
                </div>
                <div className="relative">
                  <div className="absolute inset-y-0 left-0 pl-3.5 flex items-center pointer-events-none text-warm-muted">
                    <KeyRound className="w-4 h-4" />
                  </div>
                  <input
                    type="text"
                    required
                    maxLength={6}
                    placeholder="Enter 6-digit code"
                    value={otp}
                    onChange={(e) => setOtp(e.target.value.replace(/\D/g, ''))}
                    className="w-full pl-10 pr-4 py-2.5 rounded-xl border border-warm-border text-sm tracking-widest font-mono focus:outline-none focus:ring-2 focus:ring-brand-800/20 focus:border-brand-800"
                  />
                </div>
                <p className="text-[11px] text-warm-muted mt-1 leading-relaxed">
                  We sent a 6-digit verification code to your registered email address ({maskedEmail || userEmail}).
                </p>
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
                    type={showNewPassword ? 'text' : 'password'}
                    required
                    minLength={6}
                    placeholder="Enter new strong password"
                    value={newPassword}
                    onChange={(e) => setNewPassword(e.target.value)}
                    className="w-full pl-10 pr-10 py-2.5 rounded-xl border border-warm-border text-sm focus:outline-none focus:ring-2 focus:ring-brand-800/20 focus:border-brand-800"
                  />
                  <button
                    type="button"
                    onClick={() => setShowNewPassword(!showNewPassword)}
                    className="absolute inset-y-0 right-0 pr-3.5 flex items-center text-warm-muted hover:text-gray-700"
                  >
                    {showNewPassword ? <EyeOff className="w-4 h-4" /> : <Eye className="w-4 h-4" />}
                  </button>
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
                    type={showConfirmPassword ? 'text' : 'password'}
                    required
                    minLength={6}
                    placeholder="Confirm your new password"
                    value={confirmPassword}
                    onChange={(e) => setConfirmPassword(e.target.value)}
                    className="w-full pl-10 pr-10 py-2.5 rounded-xl border border-warm-border text-sm focus:outline-none focus:ring-2 focus:ring-brand-800/20 focus:border-brand-800"
                  />
                  <button
                    type="button"
                    onClick={() => setShowConfirmPassword(!showConfirmPassword)}
                    className="absolute inset-y-0 right-0 pr-3.5 flex items-center text-warm-muted hover:text-gray-700"
                  >
                    {showConfirmPassword ? <EyeOff className="w-4 h-4" /> : <Eye className="w-4 h-4" />}
                  </button>
                </div>
              </div>

              <button
                type="submit"
                disabled={loading}
                className="w-full inline-flex items-center justify-center space-x-2 py-3 rounded-full text-sm font-bold text-white bg-rose-700 hover:bg-rose-800 shadow-md shadow-rose-900/20 transition-all disabled:opacity-50 mt-2"
              >
                <span>{loading ? 'Resetting Password...' : 'RESET PASSWORD & UNLOCK ACCOUNT'}</span>
                <ArrowRight className="w-4 h-4" />
              </button>

              <div className="pt-2 text-center border-t border-warm-border/60">
                <button
                  type="button"
                  onClick={() => {
                    setMode('yes');
                    setError('');
                  }}
                  className="text-xs font-bold text-brand-800 hover:underline"
                >
                  Recognized these attempts? Back to current password unlock
                </button>
              </div>
            </form>
          )}

          {/* Success Redirect Button */}
          {success && (
            <div className="pt-2">
              <Link
                to="/login"
                className="w-full inline-flex items-center justify-center space-x-2 py-3 rounded-full text-sm font-bold text-white bg-brand-800 hover:bg-brand-900 shadow-md transition-all"
              >
                <span>Proceed to Sign In</span>
                <ArrowRight className="w-4 h-4" />
              </Link>
            </div>
          )}
        </div>
      </main>

      <Footer />
    </div>
  );
}
