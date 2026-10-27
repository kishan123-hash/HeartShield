import React, { useState } from 'react';
import { Link, useLocation } from 'react-router-dom';
import { LogIn, LayoutDashboard, Menu, X } from 'lucide-react';
import { useAuth } from '../context/AuthContext';

export default function Navbar() {
  const location = useLocation();
  const { isAuthenticated, role, logout } = useAuth();
  const [mobileMenuOpen, setMobileMenuOpen] = useState(false);

  const publicLinks = [
    { name: 'Home', path: '/' },
    { name: 'About Us', path: '/about' },
    { name: 'Features', path: '/features' },
    { name: 'How It Works', path: '/how-it-works' },
    { name: 'FAQ', path: '/faq' },
    { name: 'Contact', path: '/contact' },
  ];

  const patientNavLinks = [
    { name: 'Dashboard', path: '/patient/dashboard' },
    { name: 'Doctors', path: '/patient/doctors' },
    { name: 'Chat with Doctor', path: '/patient/doctor-chat' },
    { name: 'Risk Assessment', path: '/patient/assessment' },
    { name: 'Features', path: '/features' },
    { name: 'Contact', path: '/contact' },
  ];

  const doctorNavLinks = [
    { name: 'Dashboard', path: '/doctor/dashboard' },
    { name: 'Patient Requests', path: '/doctor/requests' },
    { name: 'Chats', path: '/doctor/chat' },
    { name: 'Risk Assessments', path: '/doctor/assessments' },
    { name: 'Contact', path: '/contact' },
  ];

  const navLinks =
    isAuthenticated && role === 'patient'
      ? patientNavLinks
      : isAuthenticated && role === 'doctor'
      ? doctorNavLinks
      : publicLinks;

  const getDashboardPath = () => {
    if (role === 'doctor') return '/doctor/dashboard';
    if (role === 'admin') return '/admin/dashboard';
    return '/patient/dashboard';
  };

  return (
    <header className="sticky top-0 z-50 bg-white/95 backdrop-blur-md border-b border-warm-border shadow-xs">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 h-16 sm:h-20 flex items-center justify-between">
        {/* Brand Logo */}
        <Link to="/" className="flex items-center space-x-2 sm:space-x-3 group shrink-0">
          <img
            src="/heartshield-logo.png"
            alt="HeartShield"
            className="h-10 sm:h-14 md:h-16 w-auto object-contain transition-transform group-hover:scale-105"
          />
        </Link>

        {/* Desktop Navigation Links */}
        <nav className="hidden md:flex items-center space-x-1 lg:space-x-2">
          {navLinks.map((link) => {
            const isActive = location.pathname === link.path;
            return (
              <Link
                key={link.name}
                to={link.path}
                className={`px-3 py-2 rounded-lg text-sm font-medium transition-colors ${
                  isActive
                    ? 'text-brand-800 bg-brand-50 font-semibold'
                    : 'text-gray-600 hover:text-brand-800 hover:bg-rose-50/50'
                }`}
              >
                {link.name}
              </Link>
            );
          })}
        </nav>

        {/* Actions & Mobile Menu Toggle */}
        <div className="flex items-center space-x-2 sm:space-x-3">
          {isAuthenticated ? (
            <>
              <Link
                to={getDashboardPath()}
                className="inline-flex items-center space-x-1.5 sm:space-x-2 px-3 sm:px-4 py-2 sm:py-2.5 rounded-full text-xs sm:text-sm font-semibold bg-brand-800 text-white hover:bg-brand-900 shadow-sm transition-all"
              >
                <LayoutDashboard className="w-3.5 h-3.5 sm:w-4 sm:h-4 shrink-0" />
                <span>Dashboard</span>
              </Link>
              <button
                onClick={logout}
                className="hidden sm:inline-flex px-3 sm:px-4 py-2 sm:py-2.5 rounded-full text-xs sm:text-sm font-medium text-gray-700 hover:text-brand-800 hover:bg-brand-50 border border-warm-border transition-all"
              >
                Logout
              </button>
            </>
          ) : (
            <Link
              to="/login"
              className="inline-flex items-center space-x-1.5 px-3.5 sm:px-5 py-2 sm:py-2.5 rounded-full text-xs sm:text-sm font-semibold bg-brand-800 text-white hover:bg-brand-900 shadow-sm transition-all shadow-brand-800/10 hover:shadow-md"
            >
              <LogIn className="w-3.5 h-3.5 sm:w-4 sm:h-4 shrink-0" />
              <span>Login</span>
            </Link>
          )}

          {/* Mobile Menu Toggle Button */}
          <button
            type="button"
            onClick={() => setMobileMenuOpen(!mobileMenuOpen)}
            className="md:hidden p-2 rounded-xl text-gray-600 hover:text-brand-800 hover:bg-rose-50 focus:outline-none focus:ring-2 focus:ring-brand-800/20"
            aria-label={mobileMenuOpen ? 'Close navigation menu' : 'Open navigation menu'}
          >
            {mobileMenuOpen ? <X className="w-5 h-5" /> : <Menu className="w-5 h-5" />}
          </button>
        </div>
      </div>

      {/* Mobile Dropdown Menu */}
      {mobileMenuOpen && (
        <div className="md:hidden border-t border-warm-border bg-white px-4 pt-3 pb-5 space-y-1.5 shadow-lg animate-in slide-in-from-top duration-200">
          {navLinks.map((link) => {
            const isActive = location.pathname === link.path;
            return (
              <Link
                key={link.name}
                to={link.path}
                onClick={() => setMobileMenuOpen(false)}
                className={`block px-3.5 py-2.5 rounded-xl text-sm font-medium transition-all ${
                  isActive
                    ? 'text-brand-800 bg-brand-50 font-bold'
                    : 'text-gray-700 hover:text-brand-800 hover:bg-rose-50/60'
                }`}
              >
                {link.name}
              </Link>
            );
          })}

          {isAuthenticated && (
            <div className="pt-2 border-t border-warm-border">
              <button
                onClick={() => {
                  setMobileMenuOpen(false);
                  logout();
                }}
                className="w-full text-left px-3.5 py-2.5 rounded-xl text-sm font-medium text-rose-700 hover:bg-rose-50 transition-all"
              >
                Sign Out
              </button>
            </div>
          )}
        </div>
      )}
    </header>
  );
}
