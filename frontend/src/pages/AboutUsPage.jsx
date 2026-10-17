import React from 'react';
import Navbar from '../components/Navbar';
import Footer from '../components/Footer';
import { Eye, Target, Award, UserCheck } from 'lucide-react';

export default function AboutUsPage() {
  const teamMembers = [
    { name: 'Vaishnavi Parashar', role: 'Machine Learning (ML) Model Development and Frontend UI/UX Design' },
    { name: 'Yogendra Jain', role: 'LLM Integration, Retrieval-Augmented Generation (RAG), and API Integration' },
    { name: 'Kishan Sharma', role: 'Backend Development and API Integration' },
    { name: 'Shaurya Pandey', role: 'Frontend Development' },
  ];

  return (
    <div className="min-h-screen flex flex-col bg-warm-bg">
      <Navbar />

      <main className="flex-1 py-16">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 space-y-16">
          {/* Header */}
          <div className="text-center max-w-3xl mx-auto space-y-4">
            <span className="text-xs font-bold uppercase tracking-wider text-brand-800 bg-brand-50 px-3 py-1 rounded-full border border-brand-200">
              Our Journey
            </span>
            <h1 className="text-3xl sm:text-4xl lg:text-5xl font-black text-gray-900 tracking-tight">
              About HeartShield
            </h1>
            <p className="text-base text-warm-muted leading-relaxed">
              We are building an AI-powered platform to help individuals understand their heart disease risk through accurate prediction, explainable insights, and personalized recommendations.
            </p>
          </div>

          {/* 3 Pillar Cards (Vision, Mission, Values) */}
          <div className="grid grid-cols-1 md:grid-cols-3 gap-8">
            <div className="bg-white p-8 rounded-2xl border border-warm-border shadow-xs text-center space-y-4 hover:shadow-md transition-shadow">
              <div className="w-14 h-14 rounded-2xl bg-rose-50 text-brand-800 mx-auto flex items-center justify-center">
                <Eye className="w-7 h-7" />
              </div>
              <h3 className="text-xl font-bold text-gray-900">Our Vision</h3>
              <p className="text-sm text-warm-muted leading-relaxed">
                Make proactive cardiovascular health insights and early detection tools accessible, transparent, and actionable for everyone.
              </p>
            </div>

            <div className="bg-white p-8 rounded-2xl border border-warm-border shadow-xs text-center space-y-4 hover:shadow-md transition-shadow">
              <div className="w-14 h-14 rounded-2xl bg-rose-50 text-brand-800 mx-auto flex items-center justify-center">
                <Target className="w-7 h-7" />
              </div>
              <h3 className="text-xl font-bold text-gray-900">Our Mission</h3>
              <p className="text-sm text-warm-muted leading-relaxed">
                Combine state-of-the-art machine learning, verified medical knowledge, and secure web engineering for reliable early risk awareness.
              </p>
            </div>

            <div className="bg-white p-8 rounded-2xl border border-warm-border shadow-xs text-center space-y-4 hover:shadow-md transition-shadow">
              <div className="w-14 h-14 rounded-2xl bg-rose-50 text-brand-800 mx-auto flex items-center justify-center">
                <Award className="w-7 h-7" />
              </div>
              <h3 className="text-xl font-bold text-gray-900">Our Values</h3>
              <p className="text-sm text-warm-muted leading-relaxed">
                Clinical Accuracy, Transparent Model Explanations, Strict User Privacy, and Meaningful Social Impact.
              </p>
            </div>
          </div>

          {/* Team Section */}
          <div className="space-y-8">
            <div className="text-center space-y-2">
              <h2 className="text-2xl font-bold text-gray-900 tracking-tight">Our Project Team</h2>
              <p className="text-sm text-warm-muted">B.Tech Minor Project Team • ITM Gwalior</p>
            </div>

            <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-6">
              {teamMembers.map((member, idx) => (
                <div key={idx} className="bg-white p-6 rounded-2xl border border-warm-border shadow-xs text-center space-y-3">
                  <div className="w-20 h-20 rounded-full bg-gradient-to-br from-brand-700 to-rose-400 text-white font-bold text-xl flex items-center justify-center mx-auto shadow-md">
                    {member.name.split(' ').map(n => n[0]).join('')}
                  </div>
                  <div>
                    <h4 className="text-base font-bold text-gray-900">{member.name}</h4>
                    <p className="text-xs text-warm-muted mt-0.5">{member.role}</p>
                  </div>
                </div>
              ))}
            </div>
          </div>
        </div>
      </main>

      <Footer />
    </div>
  );
}
