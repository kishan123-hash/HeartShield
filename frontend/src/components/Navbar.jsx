import React from 'react';
import { Link, useLocation } from 'react-router-dom';
import { Heart, Shield, LogIn, LayoutDashboard } from 'lucide-react';
import { useAuth } from '../context/AuthContext';

export default function Navbar() {
  const location = useLocation();
  const { isAuthenticated, role, logout } = useAuth();

  const navLinks = [
    { name: 'Home', path: '/' },
    { name: 'About Us', path: '/about' },
    { name: 'Features', path: '/features' },
    { name: 'How It Works', path: '/how-it-works' },
    { name: 'FAQ', path: '/faq' },
    { name: 'Contact', path: '/contact' },
  ];

  const getDashboardPath = () => {
    if (role === 'doctor') return '/doctor/dashboard';
    if (role === 'admin') return '/admin/dashboard';
    return '/patient/dashboard';
  };

  return (
    <header className="sticky top-0 z-50 bg-white/95 backdrop-blur-md border-b border-warm-border shadow-xs">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 h-20 flex items-center justify-between">
        {/* Brand Logo */}
        {/* Brand Logo */}
<Link to="/" className="flex items-center space-x-3 group">
  <img
    src="/heartshield-logo.png"
    alt="HeartShield"
    className="h-16 w-auto object-contain transition-transform group-hover:scale-105"
  />
</Link>

        {/* Navigation Links */}
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

        {/* Auth CTA Buttons */}
        <div className="flex items-center space-x-3">
          {isAuthenticated ? (
            <>
              <Link
                to={getDashboardPath()}
                className="inline-flex items-center space-x-2 px-4 py-2.5 rounded-full text-sm font-semibold bg-brand-800 text-white hover:bg-brand-900 shadow-sm transition-all"
              >
                <LayoutDashboard className="w-4 h-4" />
                <span>Dashboard</span>
              </Link>
              <button
                onClick={logout}
                className="px-4 py-2.5 rounded-full text-sm font-medium text-gray-700 hover:text-brand-800 hover:bg-brand-50 border border-warm-border transition-all"
              >
                Logout
              </button>
            </>
          ) : (
            <>
              <Link
                to="/login"
                className="inline-flex items-center space-x-1.5 px-5 py-2.5 rounded-full text-sm font-semibold bg-brand-800 text-white hover:bg-brand-900 shadow-sm transition-all shadow-brand-800/10 hover:shadow-md"
              >
                <LogIn className="w-4 h-4" />
                <span>Login</span>
              </Link>
            </>
          )}
        </div>
      </div>
    </header>
  );
}
