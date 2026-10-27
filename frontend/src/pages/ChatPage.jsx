import React, { useState, useEffect, useRef } from 'react';
import { useLocation, Link } from 'react-router-dom';
import {
  MessageCircle,
  Send,
  Paperclip,
  Search,
  Check,
  CheckCheck,
  FileText,
  Download,
  Eye,
  Image as ImageIcon,
  X,
  AlertCircle,
  User,
  Stethoscope,
  Clock,
  ShieldCheck,
  ArrowLeft
} from 'lucide-react';
import Sidebar from '../components/Sidebar';
import { useAuth } from '../context/AuthContext';
import api, { getMediaUrl as resolveMediaUrl } from '../api/client';

export default function ChatPage() {
  const { user, role } = useAuth();
  const location = useLocation();

  const [conversations, setConversations] = useState([]);
  const [activeConv, setActiveConv] = useState(null);
  const [messages, setMessages] = useState([]);
  const [messageText, setMessageText] = useState('');
  const [selectedFile, setSelectedFile] = useState(null);
  const [filePreview, setFilePreview] = useState(null);
  const [loadingConvs, setLoadingConvs] = useState(true);
  const [loadingMessages, setLoadingMessages] = useState(false);
  const [sending, setSending] = useState(false);
  const [searchTerm, setSearchTerm] = useState('');
  const [alert, setAlert] = useState(null);
  const [lightboxImage, setLightboxImage] = useState(null);

  const messagesEndRef = useRef(null);
  const fileInputRef = useRef(null);
  const pollTimerRef = useRef(null);
  const activeConvIdRef = useRef(null);

  const token = localStorage.getItem('token');

  // Synchronous selection updater so async closures/timers always read the current target
  const setActiveConversationSync = (conv) => {
    activeConvIdRef.current = conv ? conv.id : null;
    setActiveConv(conv);
  };

  // Load conversations
  const fetchConversations = async (autoSelect = false) => {
    try {
      const res = await api.get('/consultation-chat/conversations');
      const convs = res.data || [];
      setConversations(convs);

      // Auto-select conversation or update current active metadata
      if (convs.length > 0) {
        if (activeConvIdRef.current != null) {
          // A conversation is actively selected; only update its metadata, NEVER switch away
          const updatedActive = convs.find((c) => c.id === activeConvIdRef.current);
          if (updatedActive) {
            setActiveConv(updatedActive);
          }
        } else if (autoSelect) {
          // Check if URL specifies doctor query param
          const params = new URLSearchParams(location.search);
          const targetDoctorId = params.get('doctor');
          if (targetDoctorId) {
            const found = convs.find((c) => String(c.doctor_id) === String(targetDoctorId));
            if (found) {
              setActiveConversationSync(found);
              return;
            }
          }
          setActiveConversationSync(convs[0]);
        }
      }
    } catch (err) {
      console.error('Failed to load conversations:', err);
    } finally {
      setLoadingConvs(false);
    }
  };

  // Load messages for active conversation
  const fetchMessages = async (convId, isInitial = false) => {
    if (!convId) return;
    if (isInitial) setLoadingMessages(true);
    try {
      const res = await api.get(`/consultation-chat/conversations/${convId}/messages`);
      // Request-identity guard: Only update state if activeConvIdRef.current is STILL this convId
      if (activeConvIdRef.current === convId) {
        setMessages(res.data || []);
      }
    } catch (err) {
      if (activeConvIdRef.current === convId) {
        console.error('Failed to load messages:', err);
      }
    } finally {
      if (activeConvIdRef.current === convId && isInitial) {
        setLoadingMessages(false);
      }
    }
  };

  // Immediate single-click conversation selection handler
  const handleSelectConversation = (conv) => {
    if (!conv || activeConvIdRef.current === conv.id) return;

    // Immediately halt existing polling timer
    if (pollTimerRef.current) {
      clearInterval(pollTimerRef.current);
      pollTimerRef.current = null;
    }

    // Immediately update active ID synchronously and set active state
    setActiveConversationSync(conv);

    // Immediately clear stale message list from prior patient and start loading indicator
    setMessages([]);
    setLoadingMessages(true);
    setAlert(null);

    // Fetch messages immediately for the new patient
    fetchMessages(conv.id, true);
  };

  // On mount or URL query param change, load conversations and auto-select if nothing selected
  useEffect(() => {
    fetchConversations(true);
    return () => {
      if (pollTimerRef.current) {
        clearInterval(pollTimerRef.current);
        pollTimerRef.current = null;
      }
    };
  }, [location.search]);

  // Polling setup: every 3.5s refresh active conversation messages & conversation list
  useEffect(() => {
    const currentId = activeConv?.id;
    if (!currentId) return;

    // Start polling strictly scoped to currentId
    if (pollTimerRef.current) clearInterval(pollTimerRef.current);
    pollTimerRef.current = setInterval(() => {
      if (activeConvIdRef.current === currentId) {
        fetchMessages(currentId, false);
        fetchConversations(false);
      }
    }, 3500);

    return () => {
      if (pollTimerRef.current) {
        clearInterval(pollTimerRef.current);
        pollTimerRef.current = null;
      }
    };
  }, [activeConv?.id]);

  // Scroll to bottom on new messages
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages]);

  // Handle file selection
  const handleFileChange = (e) => {
    const file = e.target.files?.[0];
    if (!file) return;

    // Validate size (10 MB max)
    const MAX_SIZE = 10 * 1024 * 1024;
    if (file.size > MAX_SIZE) {
      setAlert({
        type: 'error',
        message: `File "${file.name}" exceeds the 10 MB limit (${(file.size / (1024 * 1024)).toFixed(1)} MB).`
      });
      if (fileInputRef.current) fileInputRef.current.value = '';
      return;
    }

    // Validate types: image or pdf
    const allowed = ['image/jpeg', 'image/jpg', 'image/png', 'image/webp', 'application/pdf'];
    if (!allowed.includes(file.type.toLowerCase()) && !file.name.match(/\.(jpg|jpeg|png|webp|pdf)$/i)) {
      setAlert({
        type: 'error',
        message: 'Unsupported format. Only JPG, PNG, WEBP, and PDF documents are supported.'
      });
      if (fileInputRef.current) fileInputRef.current.value = '';
      return;
    }

    setSelectedFile(file);
    setAlert(null);

    // Create thumbnail preview if image
    if (file.type.startsWith('image/')) {
      const reader = new FileReader();
      reader.onload = (ev) => setFilePreview(ev.target.result);
      reader.readAsDataURL(file);
    } else {
      setFilePreview(null);
    }
  };

  const handleClearSelectedFile = () => {
    setSelectedFile(null);
    setFilePreview(null);
    if (fileInputRef.current) fileInputRef.current.value = '';
  };

  // Send message or upload attachment
  const handleSendMessage = async (e) => {
    e?.preventDefault();
    const targetConvId = activeConvIdRef.current;
    if (!targetConvId || sending) return;

    const text = messageText.trim();
    if (!text && !selectedFile) return;

    try {
      setSending(true);
      setAlert(null);

      if (selectedFile) {
        // Upload attachment
        const formData = new FormData();
        formData.append('file', selectedFile);
        if (text) {
          formData.append('message_text', text);
        }

        const res = await api.post(
          `/consultation-chat/conversations/${targetConvId}/attachments`,
          formData,
          {
            headers: { 'Content-Type': 'multipart/form-data' }
          }
        );

        if (activeConvIdRef.current === targetConvId) {
          setMessages((prev) => [...prev, res.data]);
        }
        handleClearSelectedFile();
        setMessageText('');
      } else {
        // Send pure text
        const res = await api.post(
          `/consultation-chat/conversations/${targetConvId}/messages`,
          { content: text }
        );

        if (activeConvIdRef.current === targetConvId) {
          setMessages((prev) => [...prev, res.data]);
        }
        setMessageText('');
      }

      // Refresh list to update preview without changing active conversation
      fetchConversations(false);
    } catch (err) {
      console.error('Failed to send message:', err);
      setAlert({
        type: 'error',
        message: err.response?.data?.detail || 'Failed to deliver message.'
      });
    } finally {
      setSending(false);
    }
  };

  const handleKeyDown = (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSendMessage();
    }
  };

  const formatFileSize = (bytes) => {
    if (!bytes) return '0 B';
    const kb = bytes / 1024;
    if (kb < 1024) return `${kb.toFixed(1)} KB`;
    return `${(kb / 1024).toFixed(1)} MB`;
  };

  const formatTimestamp = (dateString) => {
    if (!dateString) return '';
    const d = new Date(dateString);
    const now = new Date();
    const isToday = d.toDateString() === now.toDateString();
    if (isToday) {
      return d.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
    }
    return d.toLocaleDateString([], { month: 'short', day: 'numeric', hour: '2-digit', minute: '2-digit' });
  };

  const getMediaUrl = (downloadUrl) => {
    return resolveMediaUrl(downloadUrl, token);
  };

  const filteredConversations = conversations.filter((c) =>
    c.partner_name.toLowerCase().includes(searchTerm.toLowerCase()) ||
    (c.partner_specialization && c.partner_specialization.toLowerCase().includes(searchTerm.toLowerCase()))
  );

  return (
    <div className="min-h-screen flex flex-col lg:flex-row bg-warm-bg w-full min-w-0 overflow-x-hidden">
      <Sidebar />

      <main className="flex-1 p-2 sm:p-4 lg:p-8 max-w-7xl w-full mx-auto flex flex-col h-[calc(100vh-56px)] lg:h-screen overflow-hidden min-w-0">
        {/* Top Header */}
        <div className="bg-white rounded-2xl px-6 py-4 border border-warm-border shadow-xs flex items-center justify-between shrink-0 mb-4">
          <div className="flex items-center space-x-3">
            <div className="w-10 h-10 rounded-xl bg-rose-50 text-brand-800 flex items-center justify-center font-bold">
              <MessageCircle className="w-5 h-5" />
            </div>
            <div>
              <h1 className="text-lg font-black text-gray-900 tracking-tight flex items-center space-x-2">
                <span>Clinical Messaging</span>
                <span className="text-[10px] uppercase font-bold text-emerald-700 bg-emerald-50 px-2 py-0.5 rounded-full border border-emerald-200">
                  End-to-End Encrypted & Authenticated
                </span>
              </h1>
              <p className="text-xs text-warm-muted">
                Direct communication between verified cardiologist and registered patient.
              </p>
            </div>
          </div>

          {role === 'patient' && (
            <Link
              to="/patient/doctors"
              className="hidden sm:inline-flex items-center space-x-1.5 px-3.5 py-1.5 rounded-xl text-xs font-bold text-gray-700 bg-warm-bg hover:bg-rose-50 border border-warm-border transition-all"
            >
              <Stethoscope className="w-3.5 h-3.5" />
              <span>Doctors Directory</span>
            </Link>
          )}

          {role === 'doctor' && (
            <Link
              to="/doctor/requests"
              className="hidden sm:inline-flex items-center space-x-1.5 px-3.5 py-1.5 rounded-xl text-xs font-bold text-gray-700 bg-warm-bg hover:bg-rose-50 border border-warm-border transition-all"
            >
              <User className="w-3.5 h-3.5" />
              <span>Patient Requests</span>
            </Link>
          )}
        </div>

        {/* Chat Container */}
        <div className="flex-1 bg-white rounded-3xl border border-warm-border shadow-sm flex overflow-hidden min-h-0">
          {/* Left Sidebar: Conversations List */}
          <div className={`${activeConv ? 'hidden sm:flex' : 'flex'} w-full sm:w-80 md:w-96 border-r border-warm-border flex-col shrink-0 bg-white`}>
            {/* Search */}
            <div className="p-4 border-b border-warm-border">
              <div className="relative">
                <Search className="w-4 h-4 text-warm-muted absolute left-3 top-1/2 -translate-y-1/2" />
                <input
                  type="text"
                  placeholder="Search conversations..."
                  value={searchTerm}
                  onChange={(e) => setSearchTerm(e.target.value)}
                  className="w-full pl-9 pr-3 py-2 bg-warm-bg border border-warm-border rounded-xl text-xs text-gray-900 focus:outline-none focus:border-brand-800"
                />
              </div>
            </div>

            {/* List */}
            <div className="flex-1 overflow-y-auto divide-y divide-warm-border/60">
              {loadingConvs ? (
                <div className="p-8 text-center">
                  <div className="w-6 h-6 border-2 border-brand-800 border-t-transparent rounded-full animate-spin mx-auto mb-2" />
                  <p className="text-xs text-warm-muted">Loading chats...</p>
                </div>
              ) : filteredConversations.length === 0 ? (
                <div className="p-8 text-center space-y-3">
                  <MessageCircle className="w-8 h-8 text-warm-muted mx-auto" />
                  <p className="text-xs font-bold text-gray-800">
                    {role === 'doctor' ? 'No Patient Chats' : 'No Active Consultations'}
                  </p>
                  <p className="text-[11px] text-warm-muted leading-relaxed">
                    {role === 'doctor'
                      ? 'Approved consultation requests with patients will activate real-time chats here.'
                      : 'Request a consultation with a verified cardiologist to begin direct messaging.'}
                  </p>
                  {role === 'patient' && (
                    <Link
                      to="/patient/doctors"
                      className="inline-block mt-2 px-4 py-2 rounded-xl text-xs font-bold text-white bg-brand-800 hover:bg-brand-900"
                    >
                      Find Cardiologist
                    </Link>
                  )}
                  {role === 'doctor' && (
                    <Link
                      to="/doctor/requests"
                      className="inline-block mt-2 px-4 py-2 rounded-xl text-xs font-bold text-white bg-brand-800 hover:bg-brand-900"
                    >
                      Review Requests
                    </Link>
                  )}
                </div>
              ) : (
                filteredConversations.map((conv) => {
                  const isSelected = activeConv?.id === conv.id;
                  return (
                    <button
                      key={conv.id}
                      onClick={() => handleSelectConversation(conv)}
                      className={`w-full p-4 flex items-start space-x-3 text-left transition-colors ${
                        isSelected
                          ? 'bg-rose-50/80 border-r-4 border-brand-800'
                          : 'hover:bg-warm-bg/60'
                      }`}
                    >
                      <div className="w-11 h-11 rounded-2xl bg-brand-50 border border-brand-100 text-brand-800 flex items-center justify-center font-bold text-sm shrink-0 overflow-hidden shadow-2xs">
                        {conv.partner_avatar ? (
                          <img
                            src={conv.partner_avatar}
                            alt={conv.partner_name}
                            className="w-full h-full object-cover"
                          />
                        ) : (
                          <span>{conv.partner_name.charAt(0)}</span>
                        )}
                      </div>

                      <div className="flex-1 min-w-0">
                        <div className="flex items-center justify-between">
                          <h4 className="text-xs font-bold text-gray-900 truncate">
                            {conv.partner_name}
                          </h4>
                          <span className="text-[10px] text-warm-muted font-mono shrink-0 ml-1">
                            {formatTimestamp(conv.last_message_time)}
                          </span>
                        </div>

                        {conv.partner_specialization && (
                          <span className="text-[10px] font-semibold text-brand-800 block truncate">
                            {conv.partner_specialization}
                          </span>
                        )}

                        <div className="flex items-center justify-between mt-1">
                          <p className="text-xs text-warm-muted truncate pr-2">
                            {conv.last_message || 'No messages yet'}
                          </p>
                          {conv.unread_count > 0 && (
                            <span className="px-1.5 py-0.5 rounded-full text-[10px] font-bold bg-brand-800 text-white shrink-0">
                              {conv.unread_count}
                            </span>
                          )}
                        </div>
                      </div>
                    </button>
                  );
                })
              )}
            </div>
          </div>

          {/* Right Main Chat Panel */}
          {activeConv ? (
            <div className="flex-1 flex flex-col bg-[#F9F7F5] overflow-hidden">
              {/* Active Conversation Top Bar */}
              <div className="h-16 px-4 sm:px-6 bg-white border-b border-warm-border flex items-center justify-between shrink-0 shadow-2xs">
                <div className="flex items-center space-x-2 sm:space-x-3 min-w-0">
                  <button
                    type="button"
                    onClick={() => setActiveConv(null)}
                    className="sm:hidden p-1.5 rounded-lg text-gray-500 hover:text-gray-800 hover:bg-gray-100 shrink-0"
                    aria-label="Back to conversations list"
                  >
                    <ArrowLeft className="w-5 h-5" />
                  </button>
                  <div className="w-10 h-10 rounded-2xl bg-brand-50 border border-brand-100 text-brand-800 flex items-center justify-center font-bold text-sm overflow-hidden shrink-0">
                    {activeConv.partner_avatar ? (
                      <img
                        src={activeConv.partner_avatar}
                        alt={activeConv.partner_name}
                        className="w-full h-full object-cover"
                      />
                    ) : (
                      <span>{activeConv.partner_name.charAt(0)}</span>
                    )}
                  </div>
                  <div>
                    <h3 className="text-sm font-bold text-gray-900 flex items-center space-x-1.5">
                      <span>{activeConv.partner_name}</span>
                      <ShieldCheck className="w-4 h-4 text-emerald-600" />
                    </h3>
                    <p className="text-[11px] text-warm-muted">
                      {activeConv.partner_specialization
                        ? `${activeConv.partner_specialization} • Active Consultation`
                        : `${activeConv.partner_role === 'doctor' ? 'Practitioner' : 'Patient'} • Active Consultation`}
                    </p>
                  </div>
                </div>

                {role === 'doctor' && (
                  <Link
                    to={`/doctor/patient/${activeConv.patient_id}`}
                    className="inline-flex items-center space-x-1.5 px-3 py-1.5 rounded-xl text-xs font-bold text-brand-800 bg-brand-50 hover:bg-brand-100 transition-colors"
                  >
                    <span>View Patient Records</span>
                  </Link>
                )}
              </div>

              {/* Alert Message Banner */}
              {alert && (
                <div
                  className={`px-4 py-2.5 text-xs font-semibold flex items-center justify-between border-b ${
                    alert.type === 'error'
                      ? 'bg-red-50 text-red-800 border-red-200'
                      : 'bg-emerald-50 text-emerald-800 border-emerald-200'
                  }`}
                >
                  <div className="flex items-center space-x-2">
                    <AlertCircle className="w-4 h-4 shrink-0" />
                    <span>{alert.message}</span>
                  </div>
                  <button onClick={() => setAlert(null)} className="text-gray-500 hover:text-gray-800">
                    ✕
                  </button>
                </div>
              )}

              {/* Messages Area */}
              <div className="flex-1 overflow-y-auto p-4 sm:p-6 space-y-3.5">
                {loadingMessages ? (
                  <div className="p-12 text-center">
                    <div className="w-7 h-7 border-2 border-brand-800 border-t-transparent rounded-full animate-spin mx-auto mb-2" />
                    <p className="text-xs text-warm-muted">Loading message history...</p>
                  </div>
                ) : messages.length === 0 ? (
                  <div className="py-16 text-center space-y-2">
                    <div className="w-12 h-12 rounded-full bg-white border border-warm-border flex items-center justify-center mx-auto shadow-xs text-brand-800">
                      <MessageCircle className="w-6 h-6" />
                    </div>
                    <p className="text-xs font-bold text-gray-800">Begin Consultation</p>
                    <p className="text-[11px] text-warm-muted max-w-xs mx-auto">
                      Send a message, report, or clinical inquiry below. Attachments up to 10 MB are supported.
                    </p>
                  </div>
                ) : (
                  messages.map((msg) => {
                    const isMe =
                      (user?.id != null && Number(msg.sender_id) === Number(user.id)) ||
                      (activeConv?.partner_id != null && Number(msg.sender_id) !== Number(activeConv.partner_id)) ||
                      (role && msg.sender_role === role);

                    return (
                      <div
                        key={msg.id}
                        className={`w-full flex ${isMe ? 'justify-end' : 'justify-start'}`}
                      >
                        <div
                          className={`max-w-md sm:max-w-lg rounded-2xl p-3.5 shadow-2xs text-xs space-y-2 transition-all ${
                            isMe
                              ? 'bg-brand-800 text-white rounded-tr-xs'
                              : 'bg-white border border-warm-border text-gray-900 rounded-tl-xs'
                          }`}
                        >
                          {/* Attachments Section */}
                          {msg.attachments && msg.attachments.length > 0 && (
                            <div className="space-y-2">
                              {msg.attachments.map((att) => {
                                const isImg = att.file_type.startsWith('image/');
                                const isPdf = att.file_type === 'application/pdf';
                                const mediaUrl = getMediaUrl(att.download_url);

                                if (isImg) {
                                  return (
                                    <div
                                      key={att.id}
                                      className="rounded-xl overflow-hidden border border-black/10 bg-black/5 cursor-pointer group relative"
                                      onClick={() => setLightboxImage(mediaUrl)}
                                    >
                                      <img
                                        src={mediaUrl}
                                        alt={att.original_filename}
                                        className="w-full max-h-64 object-cover group-hover:opacity-95 transition-opacity"
                                        loading="lazy"
                                      />
                                      <div className="absolute inset-0 bg-black/30 opacity-0 group-hover:opacity-100 transition-opacity flex items-center justify-center text-white">
                                        <Eye className="w-6 h-6" />
                                      </div>
                                    </div>
                                  );
                                }

                                return (
                                  <div
                                    key={att.id}
                                    className={`p-3 rounded-xl border flex items-center justify-between gap-3 ${
                                      isMe
                                        ? 'bg-white/10 border-white/20 text-white'
                                        : 'bg-warm-bg border-warm-border text-gray-900'
                                    }`}
                                  >
                                    <div className="flex items-center space-x-2.5 min-w-0">
                                      <div className="w-8 h-8 rounded-lg bg-red-100 text-red-700 flex items-center justify-center shrink-0">
                                        <FileText className="w-4 h-4" />
                                      </div>
                                      <div className="min-w-0">
                                        <p className="text-xs font-bold truncate">
                                          {att.original_filename}
                                        </p>
                                        <span className={`text-[10px] block ${isMe ? 'text-white/70' : 'text-warm-muted'}`}>
                                          PDF Document • {formatFileSize(att.file_size)}
                                        </span>
                                      </div>
                                    </div>

                                    <a
                                      href={mediaUrl}
                                      target="_blank"
                                      rel="noopener noreferrer"
                                      className={`p-2 rounded-lg text-xs font-bold transition-all shrink-0 flex items-center space-x-1 ${
                                        isMe
                                          ? 'bg-white text-brand-900 hover:bg-gray-100'
                                          : 'bg-brand-800 text-white hover:bg-brand-900'
                                      }`}
                                    >
                                      <Download className="w-3.5 h-3.5" />
                                      <span>View</span>
                                    </a>
                                  </div>
                                );
                              })}
                            </div>
                          )}

                          {/* Message Body Content */}
                          {msg.content && (
                            <p className="whitespace-pre-wrap leading-relaxed break-words">
                              {msg.content}
                            </p>
                          )}

                          {/* Timestamp and Read Status */}
                          <div
                            className={`flex items-center justify-end space-x-1 text-[10px] pt-1 ${
                              isMe ? 'text-white/75' : 'text-warm-muted'
                            }`}
                          >
                            <span>{formatTimestamp(msg.created_at)}</span>
                            {isMe && (
                              <span>
                                {msg.is_read ? (
                                  <CheckCheck className="w-3.5 h-3.5 text-emerald-300 inline" />
                                ) : (
                                  <Check className="w-3.5 h-3.5 inline" />
                                )}
                              </span>
                            )}
                          </div>
                        </div>
                      </div>
                    );
                  })
                )}
                <div ref={messagesEndRef} />
              </div>

              {/* Bottom Input Area */}
              <div className="p-3 sm:p-4 bg-white border-t border-warm-border shrink-0">
                {/* Selected File Preview Chip */}
                {selectedFile && (
                  <div className="mb-2.5 p-2 rounded-xl bg-warm-bg border border-warm-border flex items-center justify-between">
                    <div className="flex items-center space-x-2 min-w-0">
                      {filePreview ? (
                        <img
                          src={filePreview}
                          alt="preview"
                          className="w-10 h-10 object-cover rounded-lg border border-warm-border"
                        />
                      ) : (
                        <div className="w-10 h-10 rounded-lg bg-red-100 text-red-700 flex items-center justify-center shrink-0">
                          <FileText className="w-5 h-5" />
                        </div>
                      )}
                      <div className="min-w-0 text-xs">
                        <p className="font-bold text-gray-900 truncate">
                          {selectedFile.name}
                        </p>
                        <span className="text-[10px] text-warm-muted">
                          {formatFileSize(selectedFile.size)} • Ready to send
                        </span>
                      </div>
                    </div>
                    <button
                      onClick={handleClearSelectedFile}
                      className="p-1 rounded-lg text-gray-400 hover:text-gray-700 hover:bg-gray-200"
                    >
                      <X className="w-4 h-4" />
                    </button>
                  </div>
                )}

                <form onSubmit={handleSendMessage} className="flex items-center space-x-2">
                  {/* File upload button */}
                  <input
                    type="file"
                    ref={fileInputRef}
                    onChange={handleFileChange}
                    accept=".jpg,.jpeg,.png,.webp,.pdf,image/jpeg,image/png,image/webp,application/pdf"
                    className="hidden"
                  />
                  <button
                    type="button"
                    onClick={() => fileInputRef.current?.click()}
                    title="Attach image or PDF (Max 10 MB)"
                    className="p-2.5 rounded-xl text-gray-500 hover:text-brand-800 hover:bg-rose-50 border border-warm-border transition-colors shrink-0"
                  >
                    <Paperclip className="w-4 h-4" />
                  </button>

                  {/* Text input */}
                  <input
                    type="text"
                    value={messageText}
                    onChange={(e) => setMessageText(e.target.value)}
                    onKeyDown={handleKeyDown}
                    placeholder={selectedFile ? 'Add an optional note with attachment...' : 'Type a consultation message (Enter to send)...'}
                    className="flex-1 px-4 py-2.5 bg-warm-bg border border-warm-border rounded-xl text-xs text-gray-900 focus:outline-none focus:border-brand-800"
                  />

                  {/* Send Button */}
                  <button
                    type="submit"
                    disabled={sending || (!messageText.trim() && !selectedFile)}
                    className="p-2.5 rounded-xl bg-brand-800 text-white hover:bg-brand-900 transition-all shadow-xs disabled:opacity-40 shrink-0"
                  >
                    {sending ? (
                      <div className="w-4 h-4 border-2 border-white border-t-transparent rounded-full animate-spin" />
                    ) : (
                      <Send className="w-4 h-4" />
                    )}
                  </button>
                </form>
              </div>
            </div>
          ) : (
            <div className="hidden sm:flex flex-1 flex-col items-center justify-center p-8 bg-[#F9F7F5] text-center space-y-3">
              <div className="w-14 h-14 rounded-2xl bg-white border border-warm-border flex items-center justify-center text-brand-800 shadow-xs">
                <MessageCircle className="w-7 h-7" />
              </div>
              <h3 className="text-sm font-bold text-gray-800">No Conversation Selected</h3>
              <p className="text-xs text-warm-muted max-w-xs">
                Select an approved patient or doctor from the left list to begin messaging.
              </p>
            </div>
          )}
        </div>

        {/* Image Lightbox Modal */}
        {lightboxImage && (
          <div
            className="fixed inset-0 z-50 bg-black/80 backdrop-blur-xs flex items-center justify-center p-4"
            onClick={() => setLightboxImage(null)}
          >
            <div className="relative max-w-4xl max-h-[90vh] overflow-hidden rounded-2xl">
              <button
                onClick={() => setLightboxImage(null)}
                className="absolute top-3 right-3 p-2 rounded-full bg-black/60 text-white hover:bg-black"
              >
                <X className="w-5 h-5" />
              </button>
              <img
                src={lightboxImage}
                alt="Enlarged attachment"
                className="max-w-full max-h-[85vh] object-contain rounded-2xl"
              />
            </div>
          </div>
        )}
      </main>
    </div>
  );
}
