import React, { useState, useRef, useEffect } from 'react';
import { useLocation, useNavigate, Link } from 'react-router-dom';
import { Shield, Heart, CheckCircle2, AlertCircle, ArrowRight } from 'lucide-react';
import api from '../api/client';
import Navbar from '../components/Navbar';
import Footer from '../components/Footer';

export default function OtpVerificationPage() {
  const [otp, setOtp] = useState(['', '', '', '', '', '']);
  const [email, setEmail] = useState('');
  const [error, setError] = useState('');
  const [success, setSuccess] = useState('');
  const [loading, setLoading] = useState(false);
  const [countdown, setCountdown] = useState(60);

  const location = useLocation();
  const navigate = useNavigate();
  const inputsRef = useRef([]);

  useEffect(() => {
    const qEmail = new URLSearchParams(location.search).get('email');
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
      });

      setSuccess('Email successfully verified! Redirecting to login...');
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
    try {
      await api.post('/auth/send-otp', { email: email.trim() });
      setCountdown(60);
      setSuccess('A fresh 6-digit OTP has been sent to your email.');
    } catch (err) {
      setError('Could not resend OTP. Please verify email address.');
    }
  };

  return (
    <div className="min-h-screen flex flex-col bg-warm-bg">
      <Navbar />

      <main className="flex-1 flex items-center justify-center p-4 py-16">
        <div className="w-full max-w-md bg-white rounded-3xl border border-warm-border shadow-md p-8 sm:p-10 space-y-6 text-center">
          {/* Logo & Header */}
          <div className="space-y-2">
            <div className="w-14 h-14 rounded-2xl bg-gradient-to-br from-brand-800 to-brand-900 flex items-center justify-center text-white mx-auto shadow-md shadow-brand-900/20">
              <div className="relative">
                <Shield className="w-8 h-8 text-white" />
                <Heart className="w-4 h-4 text-rose-300 absolute inset-0 m-auto fill-rose-300" />
              </div>
            </div>
            <h2 className="text-2xl font-black text-gray-900 tracking-tight">Verify Your Email</h2>
            <p className="text-xs text-warm-muted">
              Enter the 6-digit verification code sent to <br />
              <span className="font-semibold text-gray-900">{email || 'your email'}</span>
            </p>
          </div>

          {error && (
            <div className="p-3.5 rounded-xl bg-rose-50 border border-rose-200 text-rose-700 text-xs font-semibold flex items-center justify-center space-x-2">
              <AlertCircle className="w-4 h-4 shrink-0" />
              <span>{error}</span>
            </div>
          )}

          {success && (
            <div className="p-3.5 rounded-xl bg-emerald-50 border border-emerald-200 text-emerald-800 text-xs font-semibold flex items-center justify-center space-x-2">
              <CheckCircle2 className="w-4 h-4 shrink-0 text-emerald-600" />
              <span>{success}</span>
            </div>
          )}

          {/* OTP Input Boxes */}
          <form onSubmit={handleSubmit} className="space-y-6">
            <div className="flex justify-center space-x-2.5 sm:space-x-3">
              {otp.map((digit, idx) => (
                <input
                  key={idx}
                  ref={(el) => (inputsRef.current[idx] = el)}
                  type="text"
                  maxLength={1}
                  value={digit}
                  onChange={(e) => handleChange(idx, e.target.value)}
                  onKeyDown={(e) => handleKeyDown(idx, e)}
                  className="w-11 h-13 sm:w-12 sm:h-14 text-center text-xl font-black text-brand-900 rounded-xl border border-warm-border bg-warm-bg/40 focus:bg-white focus:outline-none focus:ring-2 focus:ring-brand-800 focus:border-brand-800"
                />
              ))}
            </div>

            <button
              type="submit"
              disabled={loading || otp.join('').length < 6}
              className="w-full inline-flex items-center justify-center space-x-2 py-3.5 rounded-full text-sm font-bold text-white bg-brand-800 hover:bg-brand-900 shadow-md shadow-brand-900/20 transition-all disabled:opacity-50"
            >
              <span>{loading ? 'Verifying...' : 'Verify OTP'}</span>
              <ArrowRight className="w-4 h-4" />
            </button>
          </form>

          {/* Resend Link */}
          <div className="pt-2 text-xs text-warm-muted">
            {countdown > 0 ? (
              <p>Resend OTP in <span className="font-bold text-brand-800">00:{countdown < 10 ? `0${countdown}` : countdown}</span></p>
            ) : (
              <button
                onClick={handleResend}
                className="font-bold text-brand-800 hover:text-brand-900 underline"
              >
                Resend OTP Code
              </button>
            )}
          </div>
        </div>
      </main>

      <Footer />
    </div>
  );
}
