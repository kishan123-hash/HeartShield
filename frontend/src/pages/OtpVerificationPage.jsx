import React, { useState, useRef, useEffect } from 'react';
import { useLocation, useNavigate, Link } from 'react-router-dom';
import { Shield, Heart, CheckCircle2, AlertCircle, ArrowRight, Mail } from 'lucide-react';
import api from '../api/client';
import Navbar from '../components/Navbar';
import Footer from '../components/Footer';

export default function OtpVerificationPage() {
  const [otp, setOtp] = useState(['', '', '', '', '', '']);
  const [email, setEmail] = useState('');
  const channel = 'email';
  const [error, setError] = useState('');
  const [success, setSuccess] = useState('');
  const [loading, setLoading] = useState(false);
  const [countdown, setCountdown] = useState(60);

  const location = useLocation();
  const navigate = useNavigate();
  const inputsRef = useRef([]);

  useEffect(() => {
    const params = new URLSearchParams(location.search);
    const qEmail = params.get('email');
    if (qEmail) setEmail(qEmail);

    const timer = setInterval(() => {
      setCountdown((prev) => (prev > 0 ? prev - 1 : 0));
    }, 1000);

    return () => clearInterval(timer);
  }, [location]);

  const handleChange = (index, value) => {
    if (!/^\d*$/.test(value)) return;

    const newOtp = [...otp];
    newOtp[index] = value.slice(-1);
    setOtp(newOtp);

    // Auto-focus next input
    if (value && index < 5) {
      inputsRef.current[index + 1]?.focus();
    }
  };

  const handleKeyDown = (index, e) => {
    if (e.key === 'Backspace' && !otp[index] && index > 0) {
      inputsRef.current[index - 1]?.focus();
    }
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    const code = otp.join('');
    if (code.length < 6) {
      setError('Please enter all 6 digits of the OTP code.');
      return;
    }

    setLoading(true);
    setError('');

    try {
      await api.post('/auth/verify-otp', {
        email: email.trim(),
        otp: code,
        purpose: 'verification',
      });

      setSuccess('Registration completed and verified! Redirecting to login...');
      setTimeout(() => {
        navigate('/login?verified=true');
      }, 1500);
    } catch (err) {
      console.error('OTP verification error:', err);
      const detail = err.response?.data?.detail;
      setError(typeof detail === 'string' ? detail : 'Invalid or expired OTP. Please try again.');
    } finally {
      setLoading(false);
    }
  };

  const handleResend = async () => {
    if (countdown > 0) return;
    setError('');
    setSuccess('');
    try {
      const res = await api.post('/auth/send-otp', {
        email: email.trim(),
        purpose: 'verification',
        channel: 'email',
      });
      setCountdown(60);
      setSuccess(res.data?.message || 'A fresh 6-digit verification code has been dispatched to your email.');
    } catch (err) {
      const msg = err.response?.data?.detail || 'Could not resend OTP. Please verify details.';
      setError(msg);
    }
  };

  const getChannelIcon = () => <Mail className="w-4 h-4 text-brand-800" />;
  const getDestinationText = () => email;

  return (
    <div className="min-h-screen flex flex-col bg-warm-bg">
      <Navbar />

      <main className="flex-1 flex items-center justify-center px-4 py-8 sm:py-16">
        <div className="w-full max-w-md bg-white rounded-3xl border border-warm-border shadow-md p-6 sm:p-10 space-y-6 text-center">
          {/* Logo & Header */}
          <div className="space-y-2">
            <div className="w-14 h-14 rounded-2xl bg-gradient-to-br from-brand-800 to-brand-900 flex items-center justify-center text-white mx-auto shadow-md shadow-brand-900/20">
              <div className="relative">
                <Shield className="w-8 h-8 text-white" />
                <Heart className="w-4 h-4 text-rose-300 absolute inset-0 m-auto fill-rose-300" />
              </div>
            </div>
            <h2 className="text-2xl font-black text-gray-900 tracking-tight">Security Verification</h2>
            <div className="flex items-center justify-center space-x-1.5 text-xs text-warm-muted">
              {getChannelIcon()}
              <span>
                Verification code dispatched to your registered email address:
              </span>
            </div>
            <p className="text-xs font-mono font-bold text-brand-900 bg-brand-50 px-3 py-1 rounded-full border border-brand-200 inline-block">
              {getDestinationText() || 'registered destination'}
            </p>
          </div>

          {/* Feedback Messages */}
          {error && (
            <div className="p-3.5 rounded-xl bg-rose-50 border border-rose-200 text-rose-700 text-xs font-semibold flex items-center space-x-2 text-left">
              <AlertCircle className="w-4 h-4 shrink-0" />
              <span>{error}</span>
            </div>
          )}

          {success && (
            <div className="p-3.5 rounded-xl bg-emerald-50 border border-emerald-200 text-emerald-800 text-xs font-semibold flex items-center space-x-2 text-left">
              <CheckCircle2 className="w-4 h-4 shrink-0" />
              <span>{success}</span>
            </div>
          )}

          {/* Form */}
          <form onSubmit={handleSubmit} className="space-y-6">
            <div>
              <label className="block text-xs font-bold text-gray-700 uppercase tracking-wider mb-3">
                Enter 6-Digit Code
              </label>
              <div className="flex justify-center space-x-2">
                {otp.map((digit, index) => (
                  <input
                    key={index}
                    ref={(el) => (inputsRef.current[index] = el)}
                    type="text"
                    inputMode="numeric"
                    maxLength={1}
                    value={digit}
                    onChange={(e) => handleChange(index, e.target.value)}
                    onKeyDown={(e) => handleKeyDown(index, e)}
                    className="w-12 h-13 text-center text-xl font-bold font-mono rounded-xl border border-warm-border text-gray-900 focus:outline-none focus:ring-2 focus:ring-brand-800/20 focus:border-brand-800 transition-all shadow-xs"
                  />
                ))}
              </div>
            </div>

            <button
              type="submit"
              disabled={loading || otp.join('').length < 6}
              className="w-full inline-flex items-center justify-center space-x-2 py-3 rounded-full text-sm font-bold text-white bg-brand-800 hover:bg-brand-900 shadow-md shadow-brand-900/20 transition-all disabled:opacity-50"
            >
              <span>{loading ? 'Verifying Code...' : 'Complete Registration'}</span>
              <ArrowRight className="w-4 h-4" />
            </button>
          </form>

          {/* Resend Action */}
          <div className="text-center pt-2 space-y-2 border-t border-warm-border/60">
            <p className="text-xs text-warm-muted">
              Didn't receive your code?{' '}
              <button
                type="button"
                onClick={handleResend}
                disabled={countdown > 0}
                className="font-bold text-brand-800 hover:text-brand-900 underline disabled:opacity-50 disabled:no-underline"
              >
                {countdown > 0 ? `Resend in ${countdown}s` : 'Resend Code'}
              </button>
            </p>
            <div>
              <Link to="/login" className="text-xs text-warm-muted hover:text-brand-800 underline">
                Return to Login
              </Link>
            </div>
          </div>
        </div>
      </main>

      <Footer />
    </div>
  );
}
