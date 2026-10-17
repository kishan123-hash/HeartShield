import React from 'react';
import { NavLink, useNavigate } from 'react-router-dom';
import {
  LayoutDashboard,
  Activity,
  Clock,
  FileText,
  Bot,
  Sparkles,
  Bell,
  Settings,
  LogOut,
  Shield,
  Heart,
  Users,
  UserCheck,
  MessageSquare
} from 'lucide-react';
import { useAuth } from '../context/AuthContext';

export default function Sidebar() {
  const { user, role, logout } = useAuth();
  const navigate = useNavigate();

  const handleLogout = () => {
    logout();
    navigate('/login');
  };

  const patientLinks = [
    { name: 'Dashboard', path: '/patient/dashboard', icon: LayoutDashboard },
    { name: 'Risk Assessment', path: '/patient/assessment', icon: Activity },
    { name: 'Prediction History', path: '/patient/history', icon: Clock },
    { name: 'Medical Reports', path: '/patient/medical-reports', icon: FileText },
    { name: 'AI Health Chat', path: '/patient/chat', icon: Bot, badge: 'Gemini' },
    { name: 'Notifications', path: '/patient/notifications', icon: Bell },
    { name: 'Feedback', path: '/patient/feedback', icon: MessageSquare },
    { name: 'Profile & Settings', path: '/patient/settings', icon: Settings },
  ];

  const doctorLinks = [
    { name: 'Doctor Dashboard', path: '/doctor/dashboard', icon: LayoutDashboard },
    { name: 'Assigned Patients', path: '/doctor/dashboard', icon: Users },
    { name: 'Profile & Settings', path: '/patient/settings', icon: Settings },
  ];

  const adminLinks = [
    { name: 'Admin Dashboard', path: '/admin/dashboard', icon: LayoutDashboard },
    { name: 'Doctor Approvals', path: '/admin/approvals', icon: UserCheck },
    { name: 'System Settings', path: '/patient/settings', icon: Settings },
  ];

  const links = role === 'admin' ? adminLinks : role === 'doctor' ? doctorLinks : patientLinks;

  return (
    <aside className="w-64 bg-white border-r border-warm-border min-h-screen flex flex-col justify-between p-4 shrink-0 shadow-xs">
      <div>
        {/* Brand Header */}
        <div className="flex items-center space-x-3 px-3 py-4 mb-6 border-b border-warm-border">
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
        <nav className="space-y-1.5">
          {links.map((item) => {
            const Icon = item.icon;
            return (
              <NavLink
                key={item.name}
                to={item.path}
                className={({ isActive }) =>
                  `flex items-center justify-between px-3.5 py-2.5 rounded-xl text-sm font-medium transition-all ${
                    isActive
                      ? 'bg-brand-800 text-white font-semibold shadow-sm shadow-brand-800/20'
                      : 'text-gray-600 hover:text-brand-800 hover:bg-rose-50/60'
                  }`
                }
              >
                <div className="flex items-center space-x-3">
                  <Icon className="w-4 h-4 shrink-0" />
                  <span>{item.name}</span>
                </div>
                {item.badge && (
                  <span className="text-[10px] bg-rose-200 text-brand-900 font-bold px-2 py-0.5 rounded-full">
                    {item.badge}
                  </span>
                )}
              </NavLink>
            );
          })}
        </nav>
      </div>

      {/* User profile & Logout */}
      <div className="pt-4 border-t border-warm-border">
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
          className="w-full flex items-center justify-center space-x-2 px-3 py-2 text-xs font-semibold text-rose-700 hover:bg-rose-100/60 rounded-xl transition-colors"
        >
          <LogOut className="w-4 h-4" />
          <span>Sign Out</span>
        </button>
      </div>
    </aside>
  );
}
