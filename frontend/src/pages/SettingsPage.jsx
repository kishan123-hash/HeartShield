import React, { useState, useEffect } from 'react';
import {
  Settings,
  User,
  Bell,
  Shield,
  Save,
  CheckCircle2,
  AlertCircle,
  Lock,
  Eye,
  Sliders,
  X
} from 'lucide-react';
import Sidebar from '../components/Sidebar';
import api from '../api/client';
import { useAuth } from '../context/AuthContext';

export default function SettingsPage() {
  const { user, login } = useAuth();

  const [activeTab, setActiveTab] = useState('profile');
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [success, setSuccess] = useState('');
  const [error, setError] = useState('');

  // Profile Form State
  const [profileData, setProfileData] = useState({
    full_name: '',
    email: '',
    phone: '',
  });

  // Notification Preferences State
  const [notifications, setNotifications] = useState({
    email_notifications: true,
    assessment_notifications: true,
    doctor_notifications: true,
    system_notifications: true,
  });

  // Privacy State
  const [privacy, setPrivacy] = useState({
    profile_visibility: true,
    data_sharing: false,
  });

  // Password Change State
  const [passwords, setPasswords] = useState({
    current_password: '',
    new_password: '',
    confirm_password: '',
  });

  useEffect(() => {
    const fetchSettings = async () => {
      setLoading(true);
      try {
        const res = await api.get('/settings');
        if (res.data?.profile) {
          setProfileData({
            full_name: res.data.profile.full_name || '',
            email: res.data.profile.email || '',
            phone: res.data.profile.phone || '',
          });
        }
        if (res.data?.notifications) {
          setNotifications(res.data.notifications);
        }
        if (res.data?.privacy) {
          setPrivacy(res.data.privacy);
        }
      } catch (err) {
        console.warn('Settings load notice:', err);
      } finally {
        setLoading(false);
      }
    };

    fetchSettings();
  }, []);

  const handleProfileSave = async (e) => {
    e.preventDefault();
    setSaving(true);
    setError('');
    setSuccess('');
    try {
      await api.put('/settings/profile', null, {
        params: {
          full_name: profileData.full_name,
          phone: profileData.phone,
        },
      });
      setSuccess('Profile information updated successfully.');
    } catch (err) {
      console.error('Profile update error:', err);
      setError(err.response?.data?.detail || 'Failed to update profile.');
    } finally {
      setSaving(false);
    }
  };

  const handleNotificationSave = async () => {
    setSaving(true);
    setError('');
    setSuccess('');
    try {
      await api.put('/settings/notifications', null, {
        params: notifications,
      });
      setSuccess('Notification preferences saved.');
    } catch (err) {
      console.error('Notification settings error:', err);
      setError('Failed to update notifications.');
    } finally {
      setSaving(false);
    }
  };

  const handlePrivacySave = async () => {
    setSaving(true);
    setError('');
    setSuccess('');
    try {
      await api.put('/settings/privacy', null, {
        params: privacy,
      });
      setSuccess('Privacy controls updated.');
    } catch (err) {
      console.error('Privacy settings error:', err);
      setError('Failed to update privacy settings.');
    } finally {
      setSaving(false);
    }
  };

  return (
    <div className="min-h-screen flex bg-warm-bg">
      <Sidebar />

      <main className="flex-1 p-6 sm:p-10 max-w-4xl mx-auto space-y-8">
        {/* Header */}
        <div>
          <span className="text-[11px] font-bold uppercase tracking-wider text-brand-800 bg-brand-50 px-2.5 py-0.5 rounded-full border border-brand-200">
            Account Management
          </span>
          <h1 className="text-2xl font-black text-gray-900 tracking-tight mt-1">
            Settings & Preferences
          </h1>
          <p className="text-xs text-warm-muted mt-1">
            Manage your personal profile, clinical notifications, data privacy, and security controls.
          </p>
        </div>

        {/* Alerts */}
        {error && (
          <div className="p-4 rounded-2xl bg-red-50 border border-red-200 text-xs text-red-700 flex items-center justify-between">
            <div className="flex items-center space-x-2">
              <AlertCircle className="w-4 h-4 shrink-0" />
              <span>{error}</span>
            </div>
            <button onClick={() => setError('')}><X className="w-4 h-4" /></button>
          </div>
        )}
        {success && (
          <div className="p-4 rounded-2xl bg-emerald-50 border border-emerald-200 text-xs text-emerald-700 flex items-center justify-between">
            <div className="flex items-center space-x-2">
              <CheckCircle2 className="w-4 h-4 shrink-0" />
              <span>{success}</span>
            </div>
            <button onClick={() => setSuccess('')}><X className="w-4 h-4" /></button>
          </div>
        )}

        {/* Navigation Tabs */}
        <div className="flex space-x-2 border-b border-warm-border pb-2 overflow-x-auto">
          {[
            { id: 'profile', label: 'User Profile', icon: User },
            { id: 'notifications', label: 'Notifications', icon: Bell },
            { id: 'privacy', label: 'Privacy & Sharing', icon: Shield },
          ].map((tab) => {
            const Icon = tab.icon;
            return (
              <button
                key={tab.id}
                onClick={() => setActiveTab(tab.id)}
                className={`flex items-center space-x-2 px-5 py-2.5 rounded-full text-xs font-bold transition-all ${
                  activeTab === tab.id
                    ? 'bg-brand-800 text-white shadow-xs'
                    : 'text-gray-600 hover:text-brand-800 hover:bg-rose-50/60'
                }`}
              >
                <Icon className="w-4 h-4" />
                <span>{tab.label}</span>
              </button>
            );
          })}
        </div>

        {/* Tab 1: Profile */}
        {activeTab === 'profile' && (
          <div className="bg-white p-6 sm:p-8 rounded-3xl border border-warm-border shadow-xs">
            <form onSubmit={handleProfileSave} className="space-y-5">
              <h3 className="text-sm font-bold text-gray-900">Personal Demographic Information</h3>

              <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                <div>
                  <label className="block text-xs font-bold text-gray-700 mb-1.5">Full Name</label>
                  <input
                    type="text"
                    value={profileData.full_name}
                    onChange={(e) => setProfileData({ ...profileData, full_name: e.target.value })}
                    className="w-full px-4 py-2.5 bg-warm-bg border border-warm-border rounded-xl text-xs text-gray-900 focus:outline-none focus:border-brand-800"
                  />
                </div>

                <div>
                  <label className="block text-xs font-bold text-gray-700 mb-1.5">Email Address</label>
                  <input
                    type="email"
                    disabled
                    value={profileData.email}
                    className="w-full px-4 py-2.5 bg-gray-100 border border-warm-border rounded-xl text-xs text-gray-500 cursor-not-allowed font-mono"
                  />
                </div>

                <div>
                  <label className="block text-xs font-bold text-gray-700 mb-1.5">Phone Number</label>
                  <input
                    type="tel"
                    value={profileData.phone}
                    onChange={(e) => setProfileData({ ...profileData, phone: e.target.value })}
                    className="w-full px-4 py-2.5 bg-warm-bg border border-warm-border rounded-xl text-xs text-gray-900 focus:outline-none focus:border-brand-800 font-mono"
                  />
                </div>

                <div>
                  <label className="block text-xs font-bold text-gray-700 mb-1.5">Role Authorization</label>
                  <input
                    type="text"
                    disabled
                    value={user?.role || 'patient'}
                    className="w-full px-4 py-2.5 bg-gray-100 border border-warm-border rounded-xl text-xs text-gray-500 capitalize cursor-not-allowed font-bold"
                  />
                </div>
              </div>

              <div className="pt-2">
                <button
                  type="submit"
                  disabled={saving}
                  className="inline-flex items-center space-x-2 px-6 py-2.5 rounded-full text-xs font-bold text-white bg-brand-800 hover:bg-brand-900 transition-all shadow-md shadow-brand-900/20 disabled:opacity-50"
                >
                  <Save className="w-4 h-4" />
                  <span>{saving ? 'Saving...' : 'Save Profile Changes'}</span>
                </button>
              </div>
            </form>
          </div>
        )}

        {/* Tab 2: Notifications */}
        {activeTab === 'notifications' && (
          <div className="bg-white p-6 sm:p-8 rounded-3xl border border-warm-border shadow-xs space-y-6">
            <div>
              <h3 className="text-sm font-bold text-gray-900">Communication Alerts</h3>
              <p className="text-xs text-warm-muted">Choose which updates you wish to receive</p>
            </div>

            <div className="space-y-4">
              {[
                {
                  id: 'email_notifications',
                  title: 'Email Summary Alerts',
                  desc: 'Receive periodic email summaries of cardiac predictions and guideline updates',
                },
                {
                  id: 'assessment_notifications',
                  title: 'Assessment Completion Alerts',
                  desc: 'Notify when machine learning models finish processing your biometrics',
                },
                {
                  id: 'doctor_notifications',
                  title: 'Doctor Notes & Validation',
                  desc: 'Immediate alerts whenever your attending cardiologist adds clinical notes',
                },
                {
                  id: 'system_notifications',
                  title: 'Platform Maintenance Notices',
                  desc: 'System health announcements, algorithm upgrades, and security warnings',
                },
              ].map((item) => (
                <div key={item.id} className="flex items-center justify-between p-3.5 bg-warm-bg rounded-2xl border border-warm-border/60">
                  <div>
                    <h4 className="text-xs font-bold text-gray-900">{item.title}</h4>
                    <p className="text-[11px] text-warm-muted mt-0.5">{item.desc}</p>
                  </div>
                  <input
                    type="checkbox"
                    checked={notifications[item.id] ?? true}
                    onChange={(e) =>
                      setNotifications({ ...notifications, [item.id]: e.target.checked })
                    }
                    className="w-4 h-4 text-brand-800 accent-brand-800 rounded cursor-pointer"
                  />
                </div>
              ))}
            </div>

            <button
              onClick={handleNotificationSave}
              disabled={saving}
              className="inline-flex items-center space-x-2 px-6 py-2.5 rounded-full text-xs font-bold text-white bg-brand-800 hover:bg-brand-900 transition-all shadow-md shadow-brand-900/20 disabled:opacity-50"
            >
              <Save className="w-4 h-4" />
              <span>{saving ? 'Saving...' : 'Update Preferences'}</span>
            </button>
          </div>
        )}

        {/* Tab 3: Privacy */}
        {activeTab === 'privacy' && (
          <div className="bg-white p-6 sm:p-8 rounded-3xl border border-warm-border shadow-xs space-y-6">
            <div>
              <h3 className="text-sm font-bold text-gray-900">Privacy & Clinical Data Governance</h3>
              <p className="text-xs text-warm-muted">Control medical records visibility and anonymized research contributions</p>
            </div>

            <div className="space-y-4">
              <div className="flex items-center justify-between p-3.5 bg-warm-bg rounded-2xl border border-warm-border/60">
                <div>
                  <h4 className="text-xs font-bold text-gray-900">Physician Visibility</h4>
                  <p className="text-[11px] text-warm-muted mt-0.5">
                    Permit verified board-certified cardiologists in the HeartShield network to review your risk profile
                  </p>
                </div>
                <input
                  type="checkbox"
                  checked={privacy.profile_visibility ?? true}
                  onChange={(e) =>
                    setPrivacy({ ...privacy, profile_visibility: e.target.checked })
                  }
                  className="w-4 h-4 text-brand-800 accent-brand-800 rounded cursor-pointer"
                />
              </div>

              <div className="flex items-center justify-between p-3.5 bg-warm-bg rounded-2xl border border-warm-border/60">
                <div>
                  <h4 className="text-xs font-bold text-gray-900">Anonymized ML Model Improvement</h4>
                  <p className="text-[11px] text-warm-muted mt-0.5">
                    Contribute de-identified numerical vitals to improve our hard-voting ensemble accuracy
                  </p>
                </div>
                <input
                  type="checkbox"
                  checked={privacy.data_sharing ?? false}
                  onChange={(e) =>
                    setPrivacy({ ...privacy, data_sharing: e.target.checked })
                  }
                  className="w-4 h-4 text-brand-800 accent-brand-800 rounded cursor-pointer"
                />
              </div>
            </div>

            <button
              onClick={handlePrivacySave}
              disabled={saving}
              className="inline-flex items-center space-x-2 px-6 py-2.5 rounded-full text-xs font-bold text-white bg-brand-800 hover:bg-brand-900 transition-all shadow-md shadow-brand-900/20 disabled:opacity-50"
            >
              <Save className="w-4 h-4" />
              <span>{saving ? 'Saving...' : 'Save Privacy Controls'}</span>
            </button>
          </div>
        )}
      </main>
    </div>
  );
}
