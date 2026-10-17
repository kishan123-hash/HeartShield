import React, { useState, useEffect } from 'react';
import {
  Bell,
  CheckCircle2,
  Trash2,
  AlertCircle,
  Clock,
  Sparkles,
  Info,
  CheckCheck
} from 'lucide-react';
import Sidebar from '../components/Sidebar';
import api from '../api/client';

export default function NotificationsPage() {
  const [notifications, setNotifications] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');

  const fetchNotifications = async () => {
    setLoading(true);
    try {
      const res = await api.get('/notifications');
      setNotifications(res.data?.notifications || []);
    } catch (err) {
      console.warn('Notifications fetch error:', err);
      setError('Unable to load notifications.');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchNotifications();
  }, []);

  const handleMarkAsRead = async (id) => {
    try {
      await api.put(`/notifications/${id}/read`);
      setNotifications(
        notifications.map((n) => (n.id === id ? { ...n, is_read: true } : n))
      );
    } catch (err) {
      console.error('Mark as read error:', err);
    }
  };

  const handleMarkAllRead = async () => {
    try {
      await api.put('/notifications/read-all');
      setNotifications(notifications.map((n) => ({ ...n, is_read: true })));
    } catch (err) {
      console.error('Mark all read error:', err);
    }
  };

  const handleDelete = async (id) => {
    try {
      await api.delete(`/notifications/${id}`);
      setNotifications(notifications.filter((n) => n.id !== id));
    } catch (err) {
      console.error('Delete notification error:', err);
    }
  };

  const unreadCount = notifications.filter((n) => !n.is_read).length;

  return (
    <div className="min-h-screen flex bg-warm-bg">
      <Sidebar />

      <main className="flex-1 p-6 sm:p-10 max-w-4xl mx-auto space-y-8">
        {/* Header */}
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
          <div>
            <span className="text-[11px] font-bold uppercase tracking-wider text-brand-800 bg-brand-50 px-2.5 py-0.5 rounded-full border border-brand-200">
              Activity & Alerts
            </span>
            <h1 className="text-2xl font-black text-gray-900 tracking-tight mt-1">
              Notifications Center
            </h1>
            <p className="text-xs text-warm-muted mt-1">
              Stay informed about assessment completions, physician notes, and health reminders.
            </p>
          </div>

          {unreadCount > 0 && (
            <button
              onClick={handleMarkAllRead}
              className="inline-flex items-center space-x-1.5 px-4 py-2 rounded-full text-xs font-bold text-brand-800 bg-brand-50 hover:bg-brand-100 border border-brand-200 transition-all shrink-0"
            >
              <CheckCheck className="w-4 h-4" />
              <span>Mark All as Read ({unreadCount})</span>
            </button>
          )}
        </div>

        {/* Notifications List */}
        <div className="bg-white rounded-3xl border border-warm-border shadow-xs overflow-hidden">
          {loading ? (
            <div className="p-12 text-center">
              <div className="w-8 h-8 border-3 border-brand-800 border-t-transparent rounded-full animate-spin mx-auto mb-3" />
              <p className="text-xs text-warm-muted">Loading your notifications...</p>
            </div>
          ) : notifications.length === 0 ? (
            <div className="p-12 text-center space-y-3">
              <div className="w-12 h-12 bg-rose-50 text-brand-800 rounded-full flex items-center justify-center mx-auto">
                <Bell className="w-6 h-6" />
              </div>
              <p className="text-xs font-bold text-gray-900">All Caught Up!</p>
              <p className="text-[11px] text-warm-muted">
                You have no active alerts or unread notifications at this time.
              </p>
            </div>
          ) : (
            <div className="divide-y divide-warm-border">
              {notifications.map((n) => (
                <div
                  key={n.id}
                  className={`p-5 flex items-start justify-between space-x-4 transition-colors ${
                    n.is_read ? 'bg-white' : 'bg-rose-50/40'
                  }`}
                >
                  <div className="flex items-start space-x-3.5">
                    <div
                      className={`w-2.5 h-2.5 rounded-full mt-1.5 shrink-0 ${
                        n.is_read ? 'bg-transparent' : 'bg-brand-800'
                      }`}
                    />
                    <div className="space-y-1">
                      <div className="flex items-center space-x-2">
                        <h4 className="text-xs font-bold text-gray-900">{n.title}</h4>
                        <span className="text-[10px] px-2 py-0.5 rounded-full bg-warm-bg text-warm-muted border border-warm-border capitalize">
                          {n.notification_type || 'Notification'}
                        </span>
                      </div>
                      <p className="text-xs text-gray-700 leading-relaxed">{n.message}</p>
                      <span className="text-[10px] text-warm-muted block pt-1">
                        {n.created_at ? new Date(n.created_at).toLocaleString() : ''}
                      </span>
                    </div>
                  </div>

                  <div className="flex items-center space-x-2 shrink-0">
                    {!n.is_read && (
                      <button
                        onClick={() => handleMarkAsRead(n.id)}
                        className="p-1.5 rounded-lg text-warm-muted hover:text-brand-800 hover:bg-warm-bg transition-all"
                        title="Mark as read"
                      >
                        <CheckCircle2 className="w-4 h-4" />
                      </button>
                    )}
                    <button
                      onClick={() => handleDelete(n.id)}
                      className="p-1.5 rounded-lg text-warm-muted hover:text-red-600 hover:bg-red-50 transition-all"
                      title="Delete"
                    >
                      <Trash2 className="w-4 h-4" />
                    </button>
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>
      </main>
    </div>
  );
}
