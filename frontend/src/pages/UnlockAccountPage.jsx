import React, { useState, useEffect } from 'react';
import { useLocation, useNavigate, Link } from 'react-router-dom';
import { Shield, Lock, AlertCircle, CheckCircle2, ArrowRight } from 'lucide-react';
import api from '../api/client';
import Navbar from '../components/Navbar';
import Footer from '../components/Footer';

export default function UnlockAccountPage() {
  const [token, setToken] = useState('');
  const [password, setPassword] = useState('');
  const [validating, setValidating] = useState(true);
  const [tokenValid, setTokenValid] = useState(false);
  const [tokenError, setTokenError] = useState('');
  const [error, setError] = useState('');
  const [success, setSuccess] = useState('');
  const [loading, setLoading] = useState(false);

  const location = useLocation();
  const navigate = useNavigate();

  useEffect(() => {
    const params = new URLSearchParams(location.search);
    const qToken = params.get('token');
    if (!qToken) {
      setValidating(false);
      setTokenValid(false);
      setTokenError('No security verification token found in URL.');
      return;
    }
    setToken(qToken);

    // Validate the token against backend API
    const validateToken = async () => {
      try {
        await api.get('/auth/unlock/verify-token', {
          params: { token: qToken },
        });
        setTokenValid(true);
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

  const handleSubmit = async (e) => {
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

          {/* Form when token is valid and not yet succeeded */}
          {!validating && tokenValid && !success && (
            <form onSubmit={handleSubmit} className="space-y-4">
              <div>
                <label className="block text-xs font-bold text-gray-700 uppercase tracking-wider mb-1">
                  Confirm Current Password
                </label>
                <div className="relative">
                  <div className="absolute inset-y-0 left-0 pl-3.5 flex items-center pointer-events-none text-warm-muted">
                    <Lock className="w-4 h-4" />
                  </div>
                  <input
                    type="password"
                    required
                    placeholder="Enter your current password"
                    value={password}
                    onChange={(e) => setPassword(e.target.value)}
                    className="w-full pl-10 pr-4 py-2.5 rounded-xl border border-warm-border text-sm focus:outline-none focus:ring-2 focus:ring-brand-800/20 focus:border-brand-800"
                  />
                </div>
                <p className="text-[11px] text-warm-muted mt-1.5 leading-relaxed">
                  For your safety, confirming your password validates ownership and clears account lockout.
                </p>
              </div>

              <button
                type="submit"
                disabled={loading}
                className="w-full inline-flex items-center justify-center space-x-2 py-3 rounded-full text-sm font-bold text-white bg-brand-800 hover:bg-brand-900 shadow-md shadow-brand-900/20 transition-all disabled:opacity-50 mt-2"
              >
                <span>{loading ? 'Verifying Identity...' : 'YES, IT WAS ME — UNLOCK ACCOUNT'}</span>
                <ArrowRight className="w-4 h-4" />
              </button>

              <div className="pt-2 text-center border-t border-warm-border/60">
                <p className="text-xs text-rose-700 font-semibold mb-1">
                  Did not recognize these attempts?
                </p>
                <p className="text-[11px] text-warm-muted mb-2">
                  Do not enter your password. We strongly recommend resetting your password immediately.
                </p>
                <div className="flex justify-center space-x-4 text-xs font-bold text-brand-800">
                  <Link to="/forgot-password" className="hover:underline">
                    Patient Reset
                  </Link>
                  <span className="text-gray-300">•</span>
                  <Link to="/doctor/forgot-password" className="hover:underline">
                    Doctor Reset
                  </Link>
                </div>
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
