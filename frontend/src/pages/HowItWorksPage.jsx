import React from 'react';
import { Link } from 'react-router-dom';
import Navbar from '../components/Navbar';
import Footer from '../components/Footer';
import { UserPlus, FileEdit, Cpu, HeartHandshake, ArrowRight, Stethoscope } from 'lucide-react';
import { useAuth } from '../context/AuthContext';

export default function HowItWorksPage() {
  const { isAuthenticated, role } = useAuth();

  const steps = [
    {
      num: '1',
      title: 'Register',
      desc: 'Create your private account securely with your email and basic demographic profile.',
      icon: UserPlus,
    },
    {
      num: '2',
      title: 'Enter Details',
      desc: 'Fill in your latest vital signs (BP, heart rate, blood glucose) and lifestyle habits.',
      icon: FileEdit,
    },
    {
      num: '3',
      title: 'Get Prediction',
      desc: 'The ensemble model votes to generate an explainable risk prediction and SHAP breakdown.',
      icon: Cpu,
    },
    {
      num: '4',
      title: 'View Recommendations',
      desc: 'Access evidence-based lifestyle steps, download your report, or chat with the AI assistant.',
      icon: HeartHandshake,
    },
  ];

  return (
    <div className="min-h-screen flex flex-col bg-warm-bg">
      <Navbar />

      <main className="flex-1 py-16">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 space-y-16">
          {/* Header */}
          <div className="text-center max-w-3xl mx-auto space-y-4">
            <span className="text-xs font-bold uppercase tracking-wider text-brand-800 bg-brand-50 px-3 py-1 rounded-full border border-brand-200">
              Guided Flow
            </span>
            <h1 className="text-3xl sm:text-4xl lg:text-5xl font-black text-gray-900 tracking-tight">
              How It Works
            </h1>
            <p className="text-base text-warm-muted leading-relaxed">
              A simple and guided four-step process to evaluate, understand, and safeguard your cardiovascular health.
            </p>
          </div>

          {/* 4 Steps Row */}
          <div className="grid grid-cols-1 md:grid-cols-4 gap-6 relative">
            {steps.map((step, idx) => {
              const Icon = step.icon;
              return (
                <div
                  key={idx}
                  className="bg-white p-6 rounded-2xl border border-warm-border shadow-xs hover:shadow-md transition-shadow flex flex-col items-center text-center space-y-4 relative"
                >
                  <div className="w-12 h-12 rounded-full bg-brand-800 text-white font-black text-lg flex items-center justify-center shadow-md shadow-brand-900/20">
                    {step.num}
                  </div>
                  <div className="w-10 h-10 rounded-xl bg-rose-50 text-brand-800 flex items-center justify-center">
                    <Icon className="w-5 h-5" />
                  </div>
                  <div>
                    <h3 className="text-base font-bold text-gray-900">{step.title}</h3>
                    <p className="text-xs text-warm-muted mt-2 leading-relaxed">{step.desc}</p>
                  </div>
                </div>
              );
            })}
          </div>

          {/* Doctor Banner Card */}
          <div className="bg-gradient-to-r from-brand-900 via-brand-800 to-rose-900 rounded-3xl p-8 sm:p-12 text-white shadow-xl relative overflow-hidden">
            <div className="grid grid-cols-1 md:grid-cols-12 gap-8 items-center">
              <div className="md:col-span-8 space-y-4 text-center md:text-left">
                <div className="inline-flex items-center space-x-2 px-3 py-1 rounded-full bg-white/10 text-rose-200 text-xs font-semibold">
                  <Stethoscope className="w-4 h-4" />
                  <span>Clinical Collaboration</span>
                </div>
                <h2 className="text-2xl sm:text-3xl font-black tracking-tight leading-tight">
                  Early Awareness. Better Choices. A Healthier Tomorrow.
                </h2>
                <p className="text-xs sm:text-sm text-rose-100/80 max-w-xl leading-relaxed">
                  HeartShield provides a bridge between self-reported health habits and clinical physician review, empowering proactive lifestyle intervention before symptoms escalate.
                </p>
                <div className="pt-2">
                  <Link
                    to={isAuthenticated ? (role === 'doctor' ? '/doctor/dashboard' : '/patient/assessment') : '/register'}
                    className="inline-flex items-center space-x-2 px-6 py-3 rounded-full bg-white text-brand-900 font-bold text-sm hover:bg-rose-50 shadow-md transition-colors"
                  >
                    <span>Start Your Assessment</span>
                    <ArrowRight className="w-4 h-4" />
                  </Link>
                </div>
              </div>

              <div className="md:col-span-4 flex justify-center">
                <div className="w-36 h-36 rounded-full bg-white/10 border-4 border-white/20 flex items-center justify-center">
                  <Stethoscope className="w-20 h-20 text-rose-200" />
                </div>
              </div>
            </div>
          </div>
        </div>
      </main>

      <Footer />
    </div>
  );
}
