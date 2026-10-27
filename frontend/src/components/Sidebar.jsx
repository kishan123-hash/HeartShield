import React, { useState } from 'react';
import { NavLink, useNavigate, useLocation } from 'react-router-dom';
import {
  LayoutDashboard,
  Activity,
  Clock,
  FileText,
  Bot,
  Bell,
  Settings,
  LogOut,
  UserCheck,
  MessageSquare,
  MessageCircle,
  Stethoscope,
  Menu,
  X
} from 'lucide-react';
import { useAuth } from '../context/AuthContext';

export default function Sidebar() {
  const { user, role, logout } = useAuth();
  const navigate = useNavigate();
  const location = useLocation();
  const [mobileOpen, setMobileOpen] = useState(false);

  const handleLogout = () => {
    logout();
    navigate('/login');
  };

  const patientLinks = [
    { name: 'Dashboard', path: '/patient/dashboard', icon: LayoutDashboard },
    { name: 'Doctors', path: '/patient/doctors', icon: Stethoscope },
    { name: 'Chat with Doctor', path: '/patient/doctor-chat', icon: MessageCircle },
    { name: 'Risk Assessment', path: '/patient/assessment', icon: Activity },
    { name: 'Prediction History', path: '/patient/history', icon: Clock },
    { name: 'Medical Reports', path: '/patient/medical-reports', icon: FileText },
    { name: 'AI Health Chat', path: '/patient/chat', icon: Bot, badge: 'Gemini' },
    { name: 'Notifications', path: '/patient/notifications', icon: Bell },
    { name: 'Feedback', path: '/patient/feedback', icon: MessageSquare },
    { name: 'Profile & Settings', path: '/patient/settings', icon: Settings },
  ];

  // STRICT REQUIREMENT PRESERVED: "Assigned Patients" removed, only these 5 items:
  const doctorLinks = [
    { name: 'Doctor Dashboard', path: '/doctor/dashboard', icon: LayoutDashboard },
    { name: 'Patient Requests', path: '/doctor/requests', icon: UserCheck },
    { name: 'Chats', path: '/doctor/chat', icon: MessageCircle },
    { name: 'Risk Assessments', path: '/doctor/assessments', icon: Activity },
    { name: 'Profile & Settings', path: '/patient/settings', icon: Settings },
  ];

  const adminLinks = [
    { name: 'Admin Dashboard', path: '/admin/dashboard', icon: LayoutDashboard },
    { name: 'Doctor Approvals', path: '/admin/approvals', icon: UserCheck },
    { name: 'System Settings', path: '/patient/settings', icon: Settings },
  ];

  const links = role === 'admin' ? adminLinks : role === 'doctor' ? doctorLinks : patientLinks;

  const renderNavLinks = (onItemClick) => (
    <nav className="space-y-1.5 flex-1 overflow-y-auto">
      {links.map((item) => {
        const Icon = item.icon;
        const isActive = location.pathname === item.path;
        return (
          <NavLink
            key={item.name}
            to={item.path}
            onClick={onItemClick}
            className={`flex items-center justify-between px-3.5 py-2.5 rounded-xl text-sm font-medium transition-all ${
              isActive
                ? 'bg-brand-800 text-white font-semibold shadow-sm shadow-brand-800/20'
                : 'text-gray-600 hover:text-brand-800 hover:bg-rose-50/60'
            }`}
          >
            <div className="flex items-center space-x-3 min-w-0">
              <Icon className="w-4 h-4 shrink-0" />
              <span className="truncate">{item.name}</span>
            </div>
            {item.badge && (
              <span className="text-[10px] bg-rose-200 text-brand-900 font-bold px-2 py-0.5 rounded-full shrink-0 ml-1">
                {item.badge}
              </span>
            )}
          </NavLink>
        );
      })}
    </nav>
  );

  const renderUserSection = () => (
    <div className="pt-4 border-t border-warm-border shrink-0">
      <div className="flex items-center justify-between p-2 rounded-xl bg-warm-bg/70 mb-3 border border-warm-border/60">
        <div className="flex items-center space-x-2.5 min-w-0">
          <div className="w-8 h-8 rounded-full bg-brand-800 text-white font-bold text-xs flex items-center justify-center shrink-0">
            {user?.full_name ? user.full_name[0].toUpperCase() : 'U'}
          </div>
          <div className="min-w-0">
            <p className="text-xs font-bold text-gray-900 truncate">{user?.full_name || 'User'}</p>
            <p className="text-[10px] text-warm-muted truncate capitalize">{role || 'Patient'}</p>
          </div>
        </div>
      </div>

      <button
        onClick={handleLogout}
        className="w-full flex items-center justify-center space-x-2 px-3 py-2 text-xs font-semibold text-rose-700 hover:bg-rose-100/60 rounded-xl transition-colors min-h-[38px]"
      >
        <LogOut className="w-4 h-4 shrink-0" />
        <span>Sign Out</span>
      </button>
    </div>
  );

  return (
    <>
      {/* 1. Mobile Top Navigation Header (< lg) */}
      <div className="lg:hidden w-full bg-white border-b border-warm-border px-4 py-3 flex items-center justify-between sticky top-0 z-40 shadow-xs shrink-0">
        <div className="flex items-center space-x-2.5 min-w-0">
          <img
            src="/heartshield-logo.png"
            alt="HeartShield"
            className="w-8 h-8 object-contain shrink-0"
          />
          <div className="flex items-center space-x-1.5 min-w-0">
            <span className="text-base font-black tracking-tight text-brand-800">Heart</span>
            <span className="text-base font-black tracking-tight text-brand-900">Shield</span>
            <span className="text-[9px] tracking-wider uppercase font-semibold text-brand-700 bg-brand-50 px-2 py-0.5 rounded-full border border-brand-200 shrink-0">
              {role || 'Portal'}
            </span>
          </div>
        </div>

        <button
          type="button"
          onClick={() => setMobileOpen(!mobileOpen)}
          className="p-2 rounded-xl text-gray-700 hover:text-brand-800 hover:bg-rose-50 focus:outline-none focus:ring-2 focus:ring-brand-800/20 shrink-0 min-h-[44px] min-w-[44px] flex items-center justify-center"
          aria-label={mobileOpen ? 'Close navigation drawer' : 'Open navigation drawer'}
        >
          {mobileOpen ? <X className="w-5 h-5" /> : <Menu className="w-5 h-5" />}
        </button>
      </div>

      {/* 2. Mobile Drawer Slide-over + Backdrop (< lg) */}
      {mobileOpen && (
        <div className="lg:hidden fixed inset-0 z-50 flex">
          {/* Backdrop overlay */}
          <div
            className="fixed inset-0 bg-black/40 backdrop-blur-xs transition-opacity"
            onClick={() => setMobileOpen(false)}
            aria-hidden="true"
          />

          {/* Drawer container */}
          <div className="relative w-72 max-w-[85vw] bg-white h-full shadow-2xl flex flex-col justify-between p-4 z-50 animate-in slide-in-from-left duration-200">
            <div>
              {/* Drawer Brand & Close Button */}
              <div className="flex items-center justify-between pb-4 mb-4 border-b border-warm-border">
                <div className="flex items-center space-x-2.5">
                  <img
                    src="/heartshield-logo.png"
                    alt="HeartShield"
                    className="w-8 h-8 object-contain shrink-0"
                  />
                  <div>
                    <div className="flex items-center space-x-1">
                      <span className="text-base font-black text-brand-800">Heart</span>
                      <span className="text-base font-black text-brand-900">Shield</span>
                    </div>
                    <span className="text-[9px] uppercase font-semibold text-brand-700 bg-brand-50 px-2 py-0.5 rounded-full border border-brand-200">
                      {role || 'Portal'}
                    </span>
                  </div>
                </div>

                <button
                  type="button"
                  onClick={() => setMobileOpen(false)}
                  className="p-1.5 rounded-lg text-gray-500 hover:text-gray-800 hover:bg-gray-100 min-h-[38px] min-w-[38px] flex items-center justify-center"
                  aria-label="Close menu"
                >
                  <X className="w-5 h-5" />
                </button>
              </div>

              {/* Drawer Links */}
              {renderNavLinks(() => setMobileOpen(false))}
            </div>

            {/* Drawer User & Logout */}
            {renderUserSection()}
          </div>
        </div>
      )}

      {/* 3. Desktop Persistent Sidebar (>= lg) */}
      <aside className="hidden lg:flex w-64 bg-white border-r border-warm-border min-h-screen flex-col justify-between p-4 shrink-0 shadow-xs">
        <div className="flex flex-col flex-1 overflow-hidden">
          {/* Brand Header */}
          <div className="flex items-center space-x-3 px-3 py-4 mb-6 border-b border-warm-border shrink-0">
            <img
              src="/heartshield-logo.png"
              alt="HeartShield"
              className="w-10 h-10 object-contain shrink-0"
            />
            <div>
              <div className="flex items-center space-x-1">
                <span className="text-lg font-black tracking-tight text-brand-800">Heart</span>
                <span className="text-lg font-black tracking-tight text-brand-900">Shield</span>
              </div>
              <span className="text-[10px] tracking-wider uppercase font-semibold text-brand-700 bg-brand-50 px-2 py-0.5 rounded-full">
                {role || 'Portal'}
              </span>
            </div>
          </div>

          {/* Navigation Menu */}
          {renderNavLinks()}
        </div>

        {/* User Profile & Logout */}
        {renderUserSection()}
      </aside>
    </>
  );
}
