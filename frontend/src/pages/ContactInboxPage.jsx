import React, { useState, useEffect } from 'react';
import {
  Inbox,
  Search,
  Filter,
  Mail,
  MailOpen,
  Clock,
  CheckCircle2,
  AlertCircle,
  Trash2,
  Eye,
  RefreshCw,
  X,
  User,
  Calendar,
  MessageSquare,
  ArrowUpDown
} from 'lucide-react';
import Sidebar from '../components/Sidebar';
import api from '../api/client';

export default function ContactInboxPage() {
  const [messages, setMessages] = useState([]);
  const [statistics, setStatistics] = useState({
    total_messages: 0,
    unread_messages: 0,
    in_progress: 0,
    resolved: 0,
  });
  const [loading, setLoading] = useState(true);
  const [searchTerm, setSearchTerm] = useState('');
  const [statusFilter, setStatusFilter] = useState('ALL');
  const [selectedMessage, setSelectedMessage] = useState(null);
  const [deleteConfirmId, setDeleteConfirmId] = useState(null);
  const [actionLoading, setActionLoading] = useState(false);
  const [feedback, setFeedback] = useState({ type: '', text: '' });

  const fetchMessages = async () => {
    setLoading(true);
    try {
      const res = await api.get('/admin/contact-messages');
      setMessages(res.data?.messages || []);
      if (res.data?.statistics) {
        setStatistics(res.data.statistics);
      }
    } catch (err) {
      console.error('Failed to load contact messages:', err);
      setFeedback({ type: 'error', text: 'Failed to load contact messages. Please try again.' });
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchMessages();
  }, []);

  const handleUpdateStatus = async (messageId, newStatus) => {
    setActionLoading(true);
    setFeedback({ type: '', text: '' });
    try {
      const res = await api.patch(`/admin/contact-messages/${messageId}`, {
        status: newStatus,
      });
      setMessages((prev) =>
        prev.map((m) => (m.id === messageId ? { ...m, status: res.data.status } : m))
      );
      if (selectedMessage && selectedMessage.id === messageId) {
        setSelectedMessage((prev) => ({ ...prev, status: res.data.status }));
      }
      setFeedback({ type: 'success', text: `Message status updated to "${newStatus.replace('_', ' ')}".` });
      // Refresh stats
      const statsRes = await api.get('/admin/contact-messages');
      if (statsRes.data?.statistics) setStatistics(statsRes.data.statistics);
    } catch (err) {
      console.error('Failed to update status:', err);
      setFeedback({ type: 'error', text: 'Failed to update message status.' });
    } finally {
      setActionLoading(false);
    }
  };

  const handleToggleRead = async (messageId, currentIsRead) => {
    setActionLoading(true);
    setFeedback({ type: '', text: '' });
    try {
      const newReadState = !currentIsRead;
      const res = await api.patch(`/admin/contact-messages/${messageId}`, {
        is_read: newReadState,
      });
      setMessages((prev) =>
        prev.map((m) => (m.id === messageId ? { ...m, is_read: res.data.is_read } : m))
      );
      if (selectedMessage && selectedMessage.id === messageId) {
        setSelectedMessage((prev) => ({ ...prev, is_read: res.data.is_read }));
      }
      setFeedback({
        type: 'success',
        text: newReadState ? 'Message marked as read.' : 'Message marked as unread.',
      });
      // Refresh stats
      const statsRes = await api.get('/admin/contact-messages');
      if (statsRes.data?.statistics) setStatistics(statsRes.data.statistics);
    } catch (err) {
      console.error('Failed to toggle read state:', err);
      setFeedback({ type: 'error', text: 'Failed to update read status.' });
    } finally {
      setActionLoading(false);
    }
  };

  const handleOpenMessage = async (msg) => {
    setSelectedMessage(msg);
    // If not read, auto-mark as read
    if (!msg.is_read) {
      try {
        await api.patch(`/admin/contact-messages/${msg.id}`, { is_read: true });
        setMessages((prev) =>
          prev.map((m) => (m.id === msg.id ? { ...m, is_read: true } : m))
        );
        setSelectedMessage((prev) => (prev ? { ...prev, is_read: true } : null));
        const statsRes = await api.get('/admin/contact-messages');
        if (statsRes.data?.statistics) setStatistics(statsRes.data.statistics);
      } catch (e) {
        console.warn('Auto mark as read error:', e);
      }
    }
  };

  const handleDeleteMessage = async (messageId) => {
    setActionLoading(true);
    setFeedback({ type: '', text: '' });
    try {
      await api.delete(`/admin/contact-messages/${messageId}`);
      setMessages((prev) => prev.filter((m) => m.id !== messageId));
      if (selectedMessage && selectedMessage.id === messageId) {
        setSelectedMessage(null);
      }
      setDeleteConfirmId(null);
      setFeedback({ type: 'success', text: `Message #${messageId} permanently deleted.` });
      // Refresh stats
      const statsRes = await api.get('/admin/contact-messages');
      if (statsRes.data?.statistics) setStatistics(statsRes.data.statistics);
    } catch (err) {
      console.error('Failed to delete message:', err);
      setFeedback({ type: 'error', text: 'Failed to delete message.' });
    } finally {
      setActionLoading(false);
    }
  };

  // Filter & search logic
  const filteredMessages = messages.filter((m) => {
    // Status filter
    if (statusFilter === 'UNREAD' && m.is_read) return false;
    if (statusFilter === 'NEW' && m.status !== 'new') return false;
    if (statusFilter === 'IN_PROGRESS' && m.status !== 'in_progress') return false;
    if (statusFilter === 'RESOLVED' && m.status !== 'resolved') return false;

    // Search term filter (name, email, subject)
    if (!searchTerm) return true;
    const term = searchTerm.toLowerCase();
    return (
      (m.name && m.name.toLowerCase().includes(term)) ||
      (m.email && m.email.toLowerCase().includes(term)) ||
      (m.subject && m.subject.toLowerCase().includes(term))
    );
  });

  const getStatusBadge = (status) => {
    switch (status) {
      case 'resolved':
        return (
          <span className="inline-flex items-center px-2 py-0.5 rounded-full text-[10px] font-bold bg-emerald-100 text-emerald-800">
            Resolved
          </span>
        );
      case 'in_progress':
        return (
          <span className="inline-flex items-center px-2 py-0.5 rounded-full text-[10px] font-bold bg-blue-100 text-blue-800">
            In Progress
          </span>
        );
      case 'new':
      default:
        return (
          <span className="inline-flex items-center px-2 py-0.5 rounded-full text-[10px] font-bold bg-amber-100 text-amber-800">
            New
          </span>
        );
    }
  };

  return (
    <div className="min-h-screen flex flex-col lg:flex-row bg-warm-bg w-full min-w-0 overflow-x-hidden">
      <Sidebar />

      <main className="flex-1 p-4 sm:p-6 lg:p-10 max-w-6xl w-full mx-auto space-y-8 min-w-0">
        {/* Header */}
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
          <div>
            <div className="flex items-center space-x-2">
              <span className="text-[11px] font-bold uppercase tracking-wider text-brand-800 bg-brand-50 px-2.5 py-0.5 rounded-full border border-brand-200">
                Administration Portal
              </span>
              <span className="text-xs text-warm-muted">Inquiries & Communications</span>
            </div>
            <h1 className="text-2xl font-black text-gray-900 tracking-tight mt-1 flex items-center space-x-2">
              <Inbox className="w-6 h-6 text-brand-800" />
              <span>Contact Inbox</span>
            </h1>
            <p className="text-xs text-warm-muted mt-1">
              Review, manage, and respond to incoming inquiries submitted via the public Contact Us form.
            </p>
          </div>

          <button
            onClick={fetchMessages}
            disabled={loading}
            className="inline-flex items-center space-x-2 px-4 py-2 rounded-full text-xs font-bold text-gray-700 bg-white border border-warm-border hover:bg-rose-50 transition-all shadow-xs shrink-0 self-start sm:self-auto"
          >
            <RefreshCw className={`w-3.5 h-3.5 ${loading ? 'animate-spin' : ''}`} />
            <span>Refresh</span>
          </button>
        </div>

        {/* Feedback Alert */}
        {feedback.text && (
          <div
            className={`p-4 rounded-2xl border text-xs flex items-center justify-between ${
              feedback.type === 'error'
                ? 'bg-red-50 border-red-200 text-red-700'
                : 'bg-emerald-50 border-emerald-200 text-emerald-800'
            }`}
          >
            <div className="flex items-center space-x-2">
              {feedback.type === 'error' ? (
                <AlertCircle className="w-4 h-4 shrink-0" />
              ) : (
                <CheckCircle2 className="w-4 h-4 shrink-0" />
              )}
              <span>{feedback.text}</span>
            </div>
            <button
              onClick={() => setFeedback({ type: '', text: '' })}
              className="text-gray-400 hover:text-gray-700"
            >
              <X className="w-4 h-4" />
            </button>
          </div>
        )}

        {/* Metric Cards Grid */}
        <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
          <div className="bg-white p-5 rounded-3xl border border-warm-border shadow-xs space-y-2">
            <div className="flex items-center justify-between">
              <span className="text-[10px] font-bold uppercase tracking-wider text-warm-muted">
                Total Messages
              </span>
              <div className="w-8 h-8 rounded-xl bg-rose-50 text-brand-800 flex items-center justify-center">
                <Inbox className="w-4 h-4" />
              </div>
            </div>
            <div className="text-2xl font-black text-gray-900">{statistics.total_messages}</div>
            <p className="text-[11px] text-warm-muted">All-time form submissions</p>
          </div>

          <div className="bg-white p-5 rounded-3xl border border-warm-border shadow-xs space-y-2">
            <div className="flex items-center justify-between">
              <span className="text-[10px] font-bold uppercase tracking-wider text-warm-muted">
                Unread Messages
              </span>
              <div className="w-8 h-8 rounded-xl bg-amber-50 text-amber-700 flex items-center justify-center">
                <Mail className="w-4 h-4" />
              </div>
            </div>
            <div className="text-2xl font-black text-amber-700">{statistics.unread_messages}</div>
            <p className="text-[11px] text-warm-muted">Requires review</p>
          </div>

          <div className="bg-white p-5 rounded-3xl border border-warm-border shadow-xs space-y-2">
            <div className="flex items-center justify-between">
              <span className="text-[10px] font-bold uppercase tracking-wider text-warm-muted">
                In Progress
              </span>
              <div className="w-8 h-8 rounded-xl bg-blue-50 text-blue-700 flex items-center justify-center">
                <Clock className="w-4 h-4" />
              </div>
            </div>
            <div className="text-2xl font-black text-blue-700">{statistics.in_progress}</div>
            <p className="text-[11px] text-warm-muted">Under active handling</p>
          </div>

          <div className="bg-white p-5 rounded-3xl border border-warm-border shadow-xs space-y-2">
            <div className="flex items-center justify-between">
              <span className="text-[10px] font-bold uppercase tracking-wider text-warm-muted">
                Resolved
              </span>
              <div className="w-8 h-8 rounded-xl bg-emerald-50 text-emerald-700 flex items-center justify-center">
                <CheckCircle2 className="w-4 h-4" />
              </div>
            </div>
            <div className="text-2xl font-black text-emerald-700">{statistics.resolved}</div>
            <p className="text-[11px] text-warm-muted">Successfully closed</p>
          </div>
        </div>

        {/* Search & Filter Toolbar */}
        <div className="bg-white p-4 sm:p-5 rounded-3xl border border-warm-border shadow-xs space-y-3">
          <div className="flex flex-col sm:flex-row gap-3 items-center justify-between">
            {/* Search Input */}
            <div className="relative w-full sm:w-80">
              <Search className="w-4 h-4 text-warm-muted absolute left-3.5 top-1/2 -translate-y-1/2" />
              <input
                type="text"
                placeholder="Search by name, email, or subject..."
                value={searchTerm}
                onChange={(e) => setSearchTerm(e.target.value)}
                className="w-full pl-9 pr-3 py-2 bg-warm-bg border border-warm-border rounded-xl text-xs text-gray-900 focus:outline-none focus:border-brand-800 transition-all placeholder:text-warm-muted"
              />
            </div>

            {/* Filter Tabs */}
            <div className="flex items-center space-x-1.5 w-full sm:w-auto overflow-x-auto pb-1 sm:pb-0">
              {[
                { id: 'ALL', label: 'All' },
                { id: 'UNREAD', label: `Unread (${statistics.unread_messages})` },
                { id: 'NEW', label: 'New' },
                { id: 'IN_PROGRESS', label: 'In Progress' },
                { id: 'RESOLVED', label: 'Resolved' },
              ].map((tab) => (
                <button
                  key={tab.id}
                  onClick={() => setStatusFilter(tab.id)}
                  className={`px-3 py-1.5 rounded-lg text-xs font-bold transition-all whitespace-nowrap ${
                    statusFilter === tab.id
                      ? 'bg-brand-800 text-white shadow-xs'
                      : 'text-gray-600 hover:text-brand-800 hover:bg-rose-50'
                  }`}
                >
                  {tab.label}
                </button>
              ))}
            </div>
          </div>
        </div>

        {/* Messages List / Table */}
        <div className="bg-white rounded-3xl border border-warm-border shadow-xs overflow-hidden">
          {loading ? (
            <div className="p-12 text-center space-y-3">
              <div className="w-8 h-8 border-3 border-brand-800 border-t-transparent rounded-full animate-spin mx-auto" />
              <p className="text-xs text-warm-muted">Loading contact inquiries...</p>
            </div>
          ) : filteredMessages.length === 0 ? (
            <div className="p-12 text-center space-y-3">
              <div className="w-12 h-12 rounded-2xl bg-warm-bg text-warm-muted flex items-center justify-center mx-auto">
                <Inbox className="w-6 h-6" />
              </div>
              <h3 className="text-sm font-bold text-gray-900">No contact messages found</h3>
              <p className="text-xs text-warm-muted max-w-sm mx-auto">
                {searchTerm || statusFilter !== 'ALL'
                  ? 'No messages match your selected search criteria or filter.'
                  : 'Form submissions from public visitors will automatically appear in this inbox.'}
              </p>
            </div>
          ) : (
            <div className="overflow-x-auto">
              <table className="w-full text-left text-xs border-collapse">
                <thead className="bg-warm-bg text-warm-muted uppercase tracking-wider text-[10px] font-bold border-b border-warm-border">
                  <tr>
                    <th className="p-4 w-12 text-center">Status</th>
                    <th className="p-4">Sender & Email</th>
                    <th className="p-4">Subject & Preview</th>
                    <th className="p-4">Date & Time</th>
                    <th className="p-4 text-center">Lifecycle</th>
                    <th className="p-4 text-right">Actions</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-warm-border">
                  {filteredMessages.map((msg) => {
                    const createdDate = new Date(msg.created_at);
                    const formattedDate = createdDate.toLocaleDateString('en-US', {
                      month: 'short',
                      day: 'numeric',
                      year: 'numeric',
                    });
                    const formattedTime = createdDate.toLocaleTimeString('en-US', {
                      hour: '2-digit',
                      minute: '2-digit',
                    });

                    return (
                      <tr
                        key={msg.id}
                        className={`hover:bg-rose-50/40 transition-colors ${
                          !msg.is_read ? 'bg-amber-50/30 font-semibold' : ''
                        }`}
                      >
                        {/* Read/Unread Icon */}
                        <td className="p-4 text-center">
                          <button
                            title={msg.is_read ? 'Mark as Unread' : 'Mark as Read'}
                            onClick={() => handleToggleRead(msg.id, msg.is_read)}
                            className="p-1 text-warm-muted hover:text-brand-800 transition-colors"
                          >
                            {msg.is_read ? (
                              <MailOpen className="w-4 h-4 text-gray-400" />
                            ) : (
                              <Mail className="w-4 h-4 text-amber-600 fill-amber-600/20" />
                            )}
                          </button>
                        </td>

                        {/* Sender Name & Email */}
                        <td className="p-4">
                          <div className="font-bold text-gray-900">{msg.name}</div>
                          <div className="text-[11px] text-warm-muted font-normal">{msg.email}</div>
                        </td>

                        {/* Subject & Preview */}
                        <td className="p-4 max-w-xs">
                          <div className="text-gray-900 truncate font-semibold">{msg.subject}</div>
                          <div className="text-[11px] text-warm-muted font-normal truncate">
                            {msg.message}
                          </div>
                        </td>

                        {/* Date & Time */}
                        <td className="p-4 whitespace-nowrap">
                          <div className="text-gray-900">{formattedDate}</div>
                          <div className="text-[10px] text-warm-muted">{formattedTime}</div>
                        </td>

                        {/* Lifecycle Status Badge */}
                        <td className="p-4 text-center whitespace-nowrap">
                          {getStatusBadge(msg.status)}
                        </td>

                        {/* Actions */}
                        <td className="p-4 text-right whitespace-nowrap space-x-1.5">
                          <button
                            onClick={() => handleOpenMessage(msg)}
                            className="p-1.5 rounded-lg bg-warm-bg border border-warm-border text-gray-700 hover:text-brand-800 hover:bg-white transition-all shadow-2xs"
                            title="View Complete Message"
                          >
                            <Eye className="w-3.5 h-3.5" />
                          </button>

                          <button
                            onClick={() => setDeleteConfirmId(msg.id)}
                            className="p-1.5 rounded-lg bg-warm-bg border border-warm-border text-red-600 hover:bg-red-50 hover:border-red-200 transition-all shadow-2xs"
                            title="Delete Message"
                          >
                            <Trash2 className="w-3.5 h-3.5" />
                          </button>
                        </td>
                      </tr>
                    );
                  })}
                </tbody>
              </table>
            </div>
          )}
        </div>

        {/* Message Detail Modal */}
        {selectedMessage && (
          <div className="fixed inset-0 z-50 bg-black/40 backdrop-blur-xs flex items-center justify-center p-4">
            <div className="bg-white rounded-3xl border border-warm-border shadow-2xl max-w-2xl w-full p-6 sm:p-8 space-y-6 max-h-[90vh] overflow-y-auto animate-in fade-in zoom-in-95 duration-150">
              {/* Modal Header */}
              <div className="flex items-start justify-between border-b border-warm-border pb-4">
                <div className="space-y-1">
                  <div className="flex items-center space-x-2">
                    <span className="text-[10px] font-bold uppercase tracking-wider text-brand-800 bg-brand-50 px-2 py-0.5 rounded-full border border-brand-200">
                      Message #{selectedMessage.id}
                    </span>
                    {getStatusBadge(selectedMessage.status)}
                    <span className="text-[11px] text-warm-muted">
                      {selectedMessage.is_read ? 'Read' : 'Unread'}
                    </span>
                  </div>
                  <h3 className="text-lg font-black text-gray-900 tracking-tight">
                    {selectedMessage.subject}
                  </h3>
                </div>
                <button
                  onClick={() => setSelectedMessage(null)}
                  className="p-2 rounded-xl text-gray-400 hover:text-gray-700 hover:bg-warm-bg transition-colors"
                >
                  <X className="w-5 h-5" />
                </button>
              </div>

              {/* Sender Details Card */}
              <div className="p-4 bg-warm-bg rounded-2xl border border-warm-border grid grid-cols-1 sm:grid-cols-2 gap-3 text-xs">
                <div>
                  <span className="text-[10px] font-bold text-warm-muted uppercase block">Sender Name</span>
                  <span className="font-bold text-gray-900">{selectedMessage.name}</span>
                </div>
                <div>
                  <span className="text-[10px] font-bold text-warm-muted uppercase block">Email Address</span>
                  <a
                    href={`mailto:${selectedMessage.email}`}
                    className="font-bold text-brand-800 hover:underline"
                  >
                    {selectedMessage.email}
                  </a>
                </div>
                <div>
                  <span className="text-[10px] font-bold text-warm-muted uppercase block">Submitted Date</span>
                  <span className="font-semibold text-gray-800">
                    {new Date(selectedMessage.created_at).toLocaleDateString('en-US', {
                      weekday: 'short',
                      year: 'numeric',
                      month: 'short',
                      day: 'numeric',
                    })}
                  </span>
                </div>
                <div>
                  <span className="text-[10px] font-bold text-warm-muted uppercase block">Submitted Time</span>
                  <span className="font-semibold text-gray-800">
                    {new Date(selectedMessage.created_at).toLocaleTimeString('en-US', {
                      hour: '2-digit',
                      minute: '2-digit',
                      second: '2-digit',
                    })}
                  </span>
                </div>
              </div>

              {/* Message Content */}
              <div className="space-y-2">
                <span className="text-[10px] font-bold text-warm-muted uppercase tracking-wider block">
                  Complete Message
                </span>
                <div className="p-5 bg-warm-bg/50 border border-warm-border rounded-2xl text-xs text-gray-900 whitespace-pre-wrap leading-relaxed">
                  {selectedMessage.message}
                </div>
              </div>

              {/* Status and Action Buttons */}
              <div className="border-t border-warm-border pt-4 flex flex-col sm:flex-row items-center justify-between gap-3">
                <div className="flex flex-wrap items-center gap-2">
                  <span className="text-xs font-bold text-gray-700">Set Status:</span>
                  <button
                    disabled={actionLoading || selectedMessage.status === 'in_progress'}
                    onClick={() => handleUpdateStatus(selectedMessage.id, 'in_progress')}
                    className="px-3 py-1.5 rounded-full text-xs font-bold bg-blue-50 text-blue-800 border border-blue-200 hover:bg-blue-100 transition-colors disabled:opacity-50"
                  >
                    In Progress
                  </button>
                  <button
                    disabled={actionLoading || selectedMessage.status === 'resolved'}
                    onClick={() => handleUpdateStatus(selectedMessage.id, 'resolved')}
                    className="px-3 py-1.5 rounded-full text-xs font-bold bg-emerald-50 text-emerald-800 border border-emerald-200 hover:bg-emerald-100 transition-colors disabled:opacity-50"
                  >
                    Mark Resolved
                  </button>
                  <button
                    disabled={actionLoading}
                    onClick={() => handleToggleRead(selectedMessage.id, selectedMessage.is_read)}
                    className="px-3 py-1.5 rounded-full text-xs font-bold bg-warm-bg text-gray-700 border border-warm-border hover:bg-gray-100 transition-colors"
                  >
                    {selectedMessage.is_read ? 'Mark as Unread' : 'Mark as Read'}
                  </button>
                </div>

                <div className="flex items-center space-x-2">
                  <button
                    onClick={() => setDeleteConfirmId(selectedMessage.id)}
                    className="px-3.5 py-1.5 rounded-full text-xs font-bold text-red-600 bg-red-50 border border-red-200 hover:bg-red-100 transition-colors flex items-center space-x-1.5"
                  >
                    <Trash2 className="w-3.5 h-3.5" />
                    <span>Delete</span>
                  </button>
                </div>
              </div>
            </div>
          </div>
        )}

        {/* Delete Confirmation Dialog */}
        {deleteConfirmId && (
          <div className="fixed inset-0 z-60 bg-black/40 backdrop-blur-xs flex items-center justify-center p-4">
            <div className="bg-white rounded-3xl border border-warm-border shadow-2xl max-w-sm w-full p-6 space-y-4 text-center">
              <div className="w-12 h-12 rounded-full bg-red-100 text-red-600 flex items-center justify-center mx-auto">
                <Trash2 className="w-6 h-6" />
              </div>
              <div className="space-y-1">
                <h3 className="text-base font-bold text-gray-900">Delete Contact Message?</h3>
                <p className="text-xs text-warm-muted">
                  Are you sure you want to permanently delete message #{deleteConfirmId}? This action cannot be undone.
                </p>
              </div>
              <div className="flex items-center justify-center space-x-3 pt-2">
                <button
                  onClick={() => setDeleteConfirmId(null)}
                  disabled={actionLoading}
                  className="px-4 py-2 rounded-full text-xs font-bold text-gray-700 bg-warm-bg border border-warm-border hover:bg-gray-100 transition-colors"
                >
                  Cancel
                </button>
                <button
                  onClick={() => handleDeleteMessage(deleteConfirmId)}
                  disabled={actionLoading}
                  className="px-5 py-2 rounded-full text-xs font-bold text-white bg-red-600 hover:bg-red-700 transition-colors shadow-xs"
                >
                  {actionLoading ? 'Deleting...' : 'Yes, Delete'}
                </button>
              </div>
            </div>
          </div>
        )}
      </main>
    </div>
  );
}
