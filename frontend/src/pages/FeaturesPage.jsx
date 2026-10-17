import React from 'react';
import Navbar from '../components/Navbar';
import Footer from '../components/Footer';
import {
  Layers,
  Cpu,
  BarChart3,
  HeartHandshake,
  ShieldCheck,
  FileSpreadsheet
} from 'lucide-react';

export default function FeaturesPage() {
  const features = [
    {
      icon: Layers,
      title: 'Multi-Step Risk Assessment',
      desc: 'Simple and guided input form capturing clinical measurements, medical history, and daily lifestyle habits with live client-side validation.'
    },
    {
      icon: Cpu,
      title: 'Machine Learning Models',
      desc: 'Hybrid hard-voting ensemble combining Logistic Regression, Random Forest, and XGBoost classifiers for robust prediction accuracy.'
    },
    {
      icon: BarChart3,
      title: 'Explainable AI (SHAP & LIME)',
      desc: 'Transparent factor importance showing how blood pressure, cholesterol, BMI, smoking, and blood sugar contribute to your risk score.'
    },
    {
      icon: HeartHandshake,
      title: 'Personalized Recommendations',
      desc: 'Dynamic dietary, physical exercise, sleep hygiene, and medical consultation steps grounded in AHA/ACC clinical guidance.'
    },
    {
      icon: ShieldCheck,
      title: 'Secure & Private',
      desc: 'OWASP-compliant session encryption, strict role-based data partitioning, and private document processing outside the public web root.'
    },
    {
      icon: FileSpreadsheet,
      title: 'Reports & History',
      desc: 'Comprehensive historical assessments, PDF report downloads, and interactive report chat for natural follow-up questions.'
    }
  ];

  return (
    <div className="min-h-screen flex flex-col bg-warm-bg">
      <Navbar />

      <main className="flex-1 py-16">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 space-y-12">
          {/* Header */}
          <div className="text-center max-w-3xl mx-auto space-y-4">
            <span className="text-xs font-bold uppercase tracking-wider text-brand-800 bg-brand-50 px-3 py-1 rounded-full border border-brand-200">
              Capabilities
            </span>
            <h1 className="text-3xl sm:text-4xl lg:text-5xl font-black text-gray-900 tracking-tight">
              Key Features
            </h1>
            <p className="text-base text-warm-muted leading-relaxed">
              A comprehensive platform for heart disease risk prediction, explainable clinical analytics, and lifestyle management.
            </p>
          </div>

          {/* 6 Feature Cards */}
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-8">
            {features.map((feat, idx) => {
              const Icon = feat.icon;
              return (
                <div
                  key={idx}
                  className="bg-white p-8 rounded-2xl border border-warm-border shadow-xs hover:shadow-md transition-all space-y-4"
                >
                  <div className="w-12 h-12 rounded-xl bg-rose-50 text-brand-800 flex items-center justify-center">
                    <Icon className="w-6 h-6" />
                  </div>
                  <h3 className="text-lg font-bold text-gray-900">{feat.title}</h3>
                  <p className="text-xs text-warm-muted leading-relaxed">{feat.desc}</p>
                </div>
              );
            })}
          </div>
        </div>
      </main>

      <Footer />
    </div>
  );
}
