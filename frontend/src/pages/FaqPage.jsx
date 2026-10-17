import React, { useState } from 'react';
import Navbar from '../components/Navbar';
import Footer from '../components/Footer';
import { ChevronDown, ChevronUp } from 'lucide-react';

export default function FaqPage() {
  const [activeCategory, setActiveCategory] = useState('General');
  const [openIndex, setOpenIndex] = useState(0);

  const categories = ['General', 'Prediction', 'Data & Privacy', 'Doctors', 'Accounts', 'Technical'];

  const faqData = {
    'General': [
      {
        q: 'What is HeartShield?',
        a: 'HeartShield is a clinical and lifestyle predictive platform that utilizes a hard-voting ensemble of Machine Learning models to calculate heart disease risk and provide explainable factor breakdowns.'
      },
      {
        q: 'Can I use this instead of seeing a doctor?',
        a: 'No. HeartShield is designed for preventive awareness, risk stratification, and educational insights. It does not replace clinical consultation, laboratory diagnostics, or prescription treatments.'
      },
      {
        q: 'What information do I need to complete an assessment?',
        a: 'You will need your current systolic and diastolic blood pressure, resting heart rate, blood glucose or cholesterol levels (if known), height, weight, and general lifestyle habits like sleep and physical activity.'
      }
    ],
    'Prediction': [
      {
        q: 'How accurate is the prediction?',
        a: 'The HeartShield hybrid ensemble achieved over 76% test accuracy on 54,000+ balanced patient records, leveraging majority hard voting across Logistic Regression, Random Forest, and XGBoost.'
      },
      {
        q: 'What is Hard Voting?',
        a: 'Hard voting is a democratic majority decision rule where each model casts a binary vote (0 = low risk, 1 = elevated risk). If two or more models vote positive, the ensemble classifies the assessment as elevated risk.'
      },
      {
        q: 'What are SHAP values?',
        a: 'SHAP (SHapley Additive exPlanations) values reveal the mathematical contribution of each clinical feature (e.g. cholesterol, systolic BP) to your final risk score, ensuring the AI model is not a black box.'
      }
    ],
    'Data & Privacy': [
      {
        q: 'Is my medical data safe and private?',
        a: 'Yes. HeartShield enforces strict OWASP standards, role-based data partitioning, encrypted JWT sessions, and private document storage outside the public web root.'
      },
      {
        q: 'Who has access to my medical reports?',
        a: 'Only you and verified clinical doctors authorized to review your patient profile can access your assessment history and uploaded reports.'
      }
    ],
    'Doctors': [
      {
        q: 'Can doctors review my predictions?',
        a: 'Yes. Verified cardiologists and physicians can inspect authorized patient assessments, review SHAP breakdowns, and record clinical feedback or customized recommendations.'
      },
      {
        q: 'How are doctors verified?',
        a: 'Doctors register with their medical license number and hospital affiliation, which is audited and approved by the system administrator before clinical access is granted.'
      }
    ],
    'Accounts': [
      {
        q: 'How do I reset my password?',
        a: 'You can use the Forgot Password link on the login page to receive an OTP and set a new password securely.'
      },
      {
        q: 'Can I update my profile after registering?',
        a: 'Yes, navigate to the Profile & Settings page from your dashboard to update contact information, emergency contacts, and lifestyle details.'
      }
    ],
    'Technical': [
      {
        q: 'What technologies power HeartShield?',
        a: 'The backend is built with FastAPI, SQLAlchemy, and MySQL/TiDB. The machine learning pipeline uses scikit-learn and XGBoost. The AI chatbot is powered by Google Gemini and RAG.'
      }
    ]
  };

  const currentFaqs = faqData[activeCategory] || faqData['General'];

  return (
    <div className="min-h-screen flex flex-col bg-warm-bg">
      <Navbar />

      <main className="flex-1 py-16">
        <div className="max-w-6xl mx-auto px-4 sm:px-6 lg:px-8 space-y-12">
          {/* Header */}
          <div className="text-center max-w-2xl mx-auto space-y-3">
            <span className="text-xs font-bold uppercase tracking-wider text-brand-800 bg-brand-50 px-3 py-1 rounded-full border border-brand-200">
              Help Center
            </span>
            <h1 className="text-3xl sm:text-4xl font-black text-gray-900 tracking-tight">
              Frequently Asked Questions
            </h1>
            <p className="text-sm text-warm-muted">
              Find answers about HeartShield predictions, explainability, safety guidelines, and account access.
            </p>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-12 gap-8 items-start">
            {/* Category Sidebar */}
            <div className="md:col-span-4 bg-white p-3 rounded-2xl border border-warm-border shadow-xs space-y-1">
              {categories.map((cat) => (
                <button
                  key={cat}
                  onClick={() => {
                    setActiveCategory(cat);
                    setOpenIndex(0);
                  }}
                  className={`w-full text-left px-4 py-3 rounded-xl text-sm font-semibold transition-all ${
                    activeCategory === cat
                      ? 'bg-brand-800 text-white shadow-xs'
                      : 'text-gray-700 hover:bg-rose-50/60 hover:text-brand-800'
                  }`}
                >
                  {cat}
                </button>
              ))}
            </div>

            {/* Accordion Questions */}
            <div className="md:col-span-8 space-y-3">
              {currentFaqs.map((faq, idx) => {
                const isOpen = openIndex === idx;
                return (
                  <div
                    key={idx}
                    className="bg-white rounded-2xl border border-warm-border shadow-xs overflow-hidden transition-all"
                  >
                    <button
                      onClick={() => setOpenIndex(isOpen ? -1 : idx)}
                      className="w-full text-left p-5 flex items-center justify-between text-sm sm:text-base font-bold text-gray-900 hover:text-brand-800 transition-colors"
                    >
                      <span>{faq.q}</span>
                      {isOpen ? (
                        <ChevronUp className="w-5 h-5 text-brand-800 shrink-0 ml-4" />
                      ) : (
                        <ChevronDown className="w-5 h-5 text-warm-muted shrink-0 ml-4" />
                      )}
                    </button>
                    {isOpen && (
                      <div className="px-5 pb-5 pt-1 text-xs sm:text-sm text-warm-muted leading-relaxed border-t border-warm-border/50">
                        {faq.a}
                      </div>
                    )}
                  </div>
                );
              })}
            </div>
          </div>
        </div>
      </main>

      <Footer />
    </div>
  );
}
