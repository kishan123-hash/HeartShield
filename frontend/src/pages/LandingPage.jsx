import React from 'react';
import { Link } from 'react-router-dom';
import { Shield, Heart, Activity, Cpu, Sparkles, Lock, ArrowRight, CheckCircle2 } from 'lucide-react';
import Navbar from '../components/Navbar';
import Footer from '../components/Footer';
import { useAuth } from '../context/AuthContext';

export default function LandingPage() {
  const { isAuthenticated, role } = useAuth();

  const ctaPath = isAuthenticated
    ? role === 'doctor'
      ? '/doctor/dashboard'
      : role === 'admin'
      ? '/admin/dashboard'
      : '/patient/assessment'
    : '/register';

  return (
    <div className="min-h-screen flex flex-col bg-warm-bg">
      <Navbar />

      <main className="flex-1">
        {/* HERO SECTION */}
        <section className="relative overflow-hidden pt-12 pb-20 lg:py-24">
          <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
            <div className="grid grid-cols-1 lg:grid-cols-12 gap-12 items-center">
              {/* Left Column Text */}
              <div className="lg:col-span-7 space-y-6 text-center lg:text-left">
                <div className="inline-flex items-center space-x-2 px-3.5 py-1.5 rounded-full bg-brand-50 border border-brand-200 text-brand-800 text-xs font-bold tracking-wide uppercase shadow-2xs">
                  <Activity className="w-4 h-4 text-brand-700 animate-pulse" />
                  <span>Hybrid Explainable AI • Hard-Voting Ensemble</span>
                </div>

                <h1 className="text-4xl sm:text-5xl lg:text-6xl font-black text-gray-900 tracking-tight leading-[1.15]">
                  Understand Your Heart.{' '}
                  <span className="text-brand-800 underline decoration-rose-300 decoration-wavy decoration-2">
                    Protect Your Future.
                  </span>
                </h1>

                <p className="text-base sm:text-lg text-warm-muted max-w-2xl mx-auto lg:mx-0 leading-relaxed">
                  AI-powered heart disease risk assessment combining clinical vitals and lifestyle habits with explainable majority voting predictions and personalized guidance.
                </p>

                {/* CTAs */}
                <div className="flex flex-col sm:flex-row items-center justify-center lg:justify-start gap-4 pt-2">
                  <Link
                    to={ctaPath}
                    className="w-full sm:w-auto inline-flex items-center justify-center space-x-2 px-8 py-3.5 rounded-full text-base font-bold text-white bg-brand-800 hover:bg-brand-900 shadow-md shadow-brand-900/25 hover:shadow-lg transition-all"
                  >
                    <span>Check Your Risk</span>
                    <ArrowRight className="w-5 h-5" />
                  </Link>

                  <Link
                    to="/how-it-works"
                    className="w-full sm:w-auto inline-flex items-center justify-center px-8 py-3.5 rounded-full text-base font-semibold text-gray-800 bg-white hover:bg-brand-50 border border-warm-border shadow-2xs transition-all"
                  >
                    Learn More
                  </Link>
                </div>

                {/* Trust badges */}
                <div className="pt-6 flex flex-wrap items-center justify-center lg:justify-start gap-6 text-xs text-warm-muted">
                  <div className="flex items-center space-x-1.5">
                    <CheckCircle2 className="w-4 h-4 text-emerald-600" />
                    <span>Logistic Regression + RF + XGBoost</span>
                  </div>
                  <div className="flex items-center space-x-1.5">
                    <CheckCircle2 className="w-4 h-4 text-emerald-600" />
                    <span>Gemini RAG Assistant</span>
                  </div>
                  <div className="flex items-center space-x-1.5">
                    <CheckCircle2 className="w-4 h-4 text-emerald-600" />
                    <span>SHAP Explainability</span>
                  </div>
                </div>
              </div>

              {/* Right Column 3D Visual */}
              <div className="lg:col-span-5 flex justify-center">
                <div className="relative w-64 h-64 sm:w-80 sm:h-80 lg:w-96 lg:h-96 max-w-full">
                  {/* Glowing decorative rings */}
                  <div className="absolute inset-0 rounded-full bg-gradient-to-tr from-rose-200/50 to-brand-100/40 blur-2xl transform scale-110"></div>
                  
                  {/* Central Heart Card with pulse wave */}
                  <div className="relative w-full h-full rounded-3xl bg-gradient-to-br from-white to-rose-50/80 border border-rose-100 shadow-xl flex flex-col items-center justify-center p-8 text-center overflow-hidden">
                    <div className="w-32 h-32 rounded-full bg-gradient-to-br from-brand-700 via-rose-600 to-rose-400 p-1 flex items-center justify-center shadow-lg shadow-brand-900/30 animate-pulse mb-4">
                      <div className="w-full h-full rounded-full bg-white flex items-center justify-center">
                        <img
  src="/heartshield-logo.png"
  alt="HeartShield Logo"
  className="w-20 h-20 object-contain"
/>
                      </div>
                    </div>

                    <h3 className="text-xl font-black text-gray-900 tracking-tight">HeartShield AI</h3>
                    <p className="text-xs text-warm-muted mt-1">Real-time Hybrid Hard-Voting Diagnostics</p>

                    {/* Vitals preview pill */}
                    <div className="mt-4 flex items-center space-x-3 bg-white/90 px-4 py-2 rounded-xl border border-warm-border/80 shadow-2xs">
                      <div className="text-left">
                        <span className="text-[10px] uppercase font-bold text-warm-muted">Accuracy</span>
                        <p className="text-sm font-black text-emerald-600">76.0%</p>
                      </div>
                      <div className="h-6 w-px bg-warm-border"></div>
                      <div className="text-left">
                        <span className="text-[10px] uppercase font-bold text-warm-muted">Models</span>
                        <p className="text-sm font-black text-brand-800">3 Voters</p>
                      </div>
                      <div className="h-6 w-px bg-warm-border"></div>
                      <div className="text-left">
                        <span className="text-[10px] uppercase font-bold text-warm-muted">Voting</span>
                        <p className="text-sm font-black text-gray-900">Hard Majority</p>
                      </div>
                    </div>
                  </div>
                </div>
              </div>
            </div>

            {/* 4 VALUE CARDS (Screen 1 Bottom) */}
            <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-6 mt-16">
              {/* Card 1 */}
              <div className="bg-white p-6 rounded-2xl border border-warm-border shadow-xs hover:shadow-md transition-shadow">
                <div className="w-12 h-12 rounded-xl bg-rose-50 flex items-center justify-center text-brand-800 mb-4">
                  <Cpu className="w-6 h-6" />
                </div>
                <h3 className="text-base font-bold text-gray-900 tracking-tight">Accurate Prediction</h3>
                <p className="text-xs text-warm-muted mt-2 leading-relaxed">
                  Trained on 54,000+ balanced patient records using Logistic Regression, Random Forest, and XGBoost hard voting.
                </p>
              </div>

              {/* Card 2 */}
              <div className="bg-white p-6 rounded-2xl border border-warm-border shadow-xs hover:shadow-md transition-shadow">
                <div className="w-12 h-12 rounded-xl bg-rose-50 flex items-center justify-center text-brand-800 mb-4">
                  <Activity className="w-6 h-6" />
                </div>
                <h3 className="text-base font-bold text-gray-900 tracking-tight">Explainable AI</h3>
                <p className="text-xs text-warm-muted mt-2 leading-relaxed">
                  Understand the exact key risk factors influencing your prediction through transparent SHAP & LIME metrics.
                </p>
              </div>

              {/* Card 3 */}
              <div className="bg-white p-6 rounded-2xl border border-warm-border shadow-xs hover:shadow-md transition-shadow">
                <div className="w-12 h-12 rounded-xl bg-rose-50 flex items-center justify-center text-brand-800 mb-4">
                  <Sparkles className="w-6 h-6" />
                </div>
                <h3 className="text-base font-bold text-gray-900 tracking-tight">Personalized Guidance</h3>
                <p className="text-xs text-warm-muted mt-2 leading-relaxed">
                  Tailored lifestyle, dietary, exercise, and clinical recommendations aligned with authoritative AHA/ACC guidelines.
                </p>
              </div>

              {/* Card 4 */}
              <div className="bg-white p-6 rounded-2xl border border-warm-border shadow-xs hover:shadow-md transition-shadow">
                <div className="w-12 h-12 rounded-xl bg-rose-50 flex items-center justify-center text-brand-800 mb-4">
                  <Lock className="w-6 h-6" />
                </div>
                <h3 className="text-base font-bold text-gray-900 tracking-tight">Trusted & Secure</h3>
                <p className="text-xs text-warm-muted mt-2 leading-relaxed">
                  Strict role-based isolation, encrypted sessions, OWASP-compliant API protections, and private document processing.
                </p>
              </div>
            </div>
          </div>
        </section>
      </main>

      <Footer />
    </div>
  );
}
