import React from 'react';
import { Link } from 'react-router-dom';
import { Shield, Heart, Mail, Phone, MapPin } from 'lucide-react';

export default function Footer() {
  return (
    <footer className="bg-brand-950 text-rose-100/80 border-t border-brand-900 mt-20">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-14">
        <div className="grid grid-cols-1 md:grid-cols-4 gap-10">
          {/* Brand Col */}
          <div className="md:col-span-1 space-y-4">
            <div className="flex items-center space-x-3">
              <div className="w-10 h-10 rounded-xl bg-white/10 flex items-center justify-center text-white border border-white/20">
                <Shield className="w-6 h-6 text-rose-300" />
              </div>
              <div>
                <span className="text-xl font-black text-white tracking-tight">HeartShield</span>
                <p className="text-[10px] tracking-wider text-rose-300/80 uppercase font-medium">Cardiovascular AI</p>
              </div>
            </div>
            <p className="text-xs text-rose-200/70 leading-relaxed">
              A Hybrid Explainable AI Model for Heart Disease Prediction Using Clinical and Lifestyle Data.
            </p>
          </div>

          {/* Quick Links */}
          <div>
            <h4 className="text-sm font-semibold text-white uppercase tracking-wider mb-4">Platform</h4>
            <ul className="space-y-2 text-xs">
              <li><Link to="/about" className="hover:text-white transition-colors">About HeartShield</Link></li>
              <li><Link to="/features" className="hover:text-white transition-colors">Ensemble ML Models</Link></li>
              <li><Link to="/how-it-works" className="hover:text-white transition-colors">How It Works</Link></li>
              <li><Link to="/faq" className="hover:text-white transition-colors">Clinical FAQ</Link></li>
            </ul>
          </div>

          {/* Clinical & Safety */}
          <div>
            <h4 className="text-sm font-semibold text-white uppercase tracking-wider mb-4">Safety & Ethics</h4>
            <ul className="space-y-2 text-xs">
              <li><span className="text-rose-300/90 font-medium">Explainable AI (SHAP & LIME)</span></li>
              <li><span className="text-rose-300/90 font-medium">AHA/ACC Guidelines Grounding</span></li>
              <li><span className="text-rose-300/90 font-medium">OWASP Top 10 Security Reference</span></li>
              <li><span className="text-rose-300/90 font-medium">Zero-Latency Emergency Triage</span></li>
            </ul>
          </div>

          {/* Contact */}
          <div>
            <h4 className="text-sm font-semibold text-white uppercase tracking-wider mb-4">Contact & Support</h4>
            <div className="space-y-3 text-xs text-rose-200/80">
              <div className="flex items-center space-x-2">
                <Mail className="w-4 h-4 text-rose-400" />
                <span>support@heartshield.io</span>
              </div>
              <div className="flex items-center space-x-2">
                <Phone className="w-4 h-4 text-rose-400" />
                <span>+91 98765 43210</span>
              </div>
              <div className="flex items-center space-x-2">
                <MapPin className="w-4 h-4 text-rose-400" />
                <span>ITM Gwalior, Madhya Pradesh, India</span>
              </div>
            </div>
          </div>
        </div>

        {/* Bottom bar with Medical Disclaimer */}
        <div className="mt-12 pt-8 border-t border-brand-900/80 flex flex-col md:flex-row items-center justify-between text-xs text-rose-300/60 gap-4">
          <p>© {new Date().getFullYear()} HeartShield Project. Built for research and clinical education.</p>
          <p className="max-w-2xl text-center md:text-right text-[11px] leading-relaxed text-rose-300/50">
            Disclaimer: HeartShield is an academic AI research project and not a licensed diagnostic device. Consult a physician for acute medical conditions.
          </p>
        </div>
      </div>
    </footer>
  );
}
