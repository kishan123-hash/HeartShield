import React, { useState, useEffect, useRef } from 'react';
import { useSearchParams } from 'react-router-dom';
import {
  Bot,
  User,
  Send,
  Plus,
  Trash2,
  FileText,
  AlertTriangle,
  Sparkles,
  ShieldAlert,
  Info,
  Clock,
  ExternalLink,
  Paperclip,
  CheckCircle2,
  X
} from 'lucide-react';
import Sidebar from '../components/Sidebar';
import EmergencyBanner from '../components/EmergencyBanner';
import api from '../api/client';

export default function ChatbotPage() {
  const [searchParams] = useSearchParams();
  const initialReportId = searchParams.get('report_id');

  const [conversations, setConversations] = useState([]);
  const [activeConvId, setActiveConvId] = useState(null);
  const [messages, setMessages] = useState([]);
  const [inputMessage, setInputMessage] = useState('');
  const [sending, setSending] = useState(false);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [emergencyDetected, setEmergencyDetected] = useState(false);

  // Attached report selection
  const [reports, setReports] = useState([]);
  const [selectedReportId, setSelectedReportId] = useState(
    initialReportId ? Number(initialReportId) : null
  );

  const messagesEndRef = useRef(null);

  // Auto scroll to bottom
  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages, sending]);

  // Load conversations and medical reports list
  useEffect(() => {
    const initChat = async () => {
      setLoading(true);
      try {
        // Fetch conversations
        const convRes = await api.get('/chat/conversations');
        const convList = convRes.data || [];
        setConversations(convList);

        if (convList.length > 0) {
          setActiveConvId(convList[0].id);
        } else {
          // Auto create first consultation
          const newConv = await api.post('/chat/conversations', {
            title: 'Cardiovascular Consultation',
          });
          setConversations([newConv.data]);
          setActiveConvId(newConv.data.id);
        }

        // Fetch reports for attachment dropdown
        try {
          const repRes = await api.get('/medical-reports');
          setReports(repRes.data?.reports || []);
        } catch (rErr) {
          console.warn('Reports not loaded:', rErr);
        }
      } catch (err) {
        console.error('Chat init error:', err);
        setError('Failed to initialize AI consultation sessions.');
      } finally {
        setLoading(false);
      }
    };

    initChat();
  }, []);

  // Fetch messages when active conversation changes
  useEffect(() => {
    const fetchMessages = async () => {
      if (!activeConvId) return;
      try {
        const res = await api.get(`/chat/conversations/${activeConvId}/messages`);
        setMessages(res.data?.messages || []);
      } catch (err) {
        console.error('Error fetching messages:', err);
      }
    };

    fetchMessages();
  }, [activeConvId]);

  const handleCreateConversation = async () => {
    try {
      const res = await api.post('/chat/conversations', {
        title: `Consultation ${conversations.length + 1}`,
      });
      setConversations([res.data, ...conversations]);
      setActiveConvId(res.data.id);
      setSelectedReportId(null);
    } catch (err) {
      console.error('Error creating conversation:', err);
      setError('Failed to create new consultation session.');
    }
  };

  const handleDeleteConversation = async (convId, e) => {
    e.stopPropagation();
    if (!window.confirm('Delete this conversation?')) return;
    try {
      await api.delete(`/chat/conversations/${convId}`);
      const remaining = conversations.filter((c) => c.id !== convId);
      setConversations(remaining);
      if (activeConvId === convId) {
        setActiveConvId(remaining.length > 0 ? remaining[0].id : null);
      }
    } catch (err) {
      console.error('Error deleting conversation:', err);
    }
  };

  // Client-side quick symptom check for acute cardiovascular warnings
  const checkAcuteSymptoms = (text) => {
    const acuteRegex = /\b(crushing chest pain|chest pressure|radiating (arm|jaw)|sudden syncope|loss of consciousness|shortness of breath at rest)\b/i;
    return acuteRegex.test(text);
  };

  const handleSendMessage = async (e) => {
    e?.preventDefault();
    if (!inputMessage.trim() || sending || !activeConvId) return;

    const userText = inputMessage.trim();
    setInputMessage('');

    // Check emergency keywords immediately
    if (checkAcuteSymptoms(userText)) {
      setEmergencyDetected(true);
    }

    // Optimistically append user message
    const optimisticUserMsg = {
      id: Date.now(),
      conversation_id: activeConvId,
      role: 'user',
      content: userText,
      created_at: new Date().toISOString(),
    };
    setMessages((prev) => [...prev, optimisticUserMsg]);
    setSending(true);

    try {
      const payload = {
        content: userText,
        report_id: selectedReportId || undefined,
      };

      const res = await api.post(`/chat/conversations/${activeConvId}/messages`, payload);

      // Append assistant response
      setMessages((prev) => [...prev, res.data]);

      // If response mentions emergency advice
      if (
        res.data.content?.toLowerCase().includes('emergency') &&
        (res.data.content?.includes('911') || res.data.content?.includes('112') || res.data.content?.includes('emergency room'))
      ) {
        setEmergencyDetected(true);
      }
    } catch (err) {
      console.error('Error sending message:', err);
      setMessages((prev) => [
        ...prev,
        {
          id: Date.now() + 1,
          conversation_id: activeConvId,
          role: 'assistant',
          content: 'I apologize, but I encountered an error communicating with the medical reasoning service. Please check your network connection and try again.',
          created_at: new Date().toISOString(),
        },
      ]);
    } finally {
      setSending(false);
    }
  };

  const handleQuickPrompt = (prompt) => {
    setInputMessage(prompt);
  };

  return (
    <div className="min-h-screen flex bg-warm-bg">
      <Sidebar />

      <main className="flex-1 flex flex-col h-screen overflow-hidden">
        {/* Top Header */}
        <header className="bg-white border-b border-warm-border px-6 py-4 flex items-center justify-between shrink-0 shadow-xs">
          <div className="flex items-center space-x-3">
            <div className="w-10 h-10 rounded-xl bg-gradient-to-br from-brand-800 to-brand-900 flex items-center justify-center text-white shadow-md shadow-brand-900/20">
              <Bot className="w-5 h-5" />
            </div>
            <div>
              <div className="flex items-center space-x-2">
                <h1 className="text-base font-black text-gray-900">HeartShield AI Health Assistant</h1>
                <span className="text-[10px] bg-brand-50 text-brand-800 font-bold px-2 py-0.5 rounded-full border border-brand-200">
                  Gemini 3.5 Flash
                </span>
                <span className="text-[10px] bg-emerald-50 text-emerald-700 font-bold px-2 py-0.5 rounded-full border border-emerald-200">
                  RAG Guidelines Active
                </span>
              </div>
              <p className="text-[11px] text-warm-muted">
                Evidence-based cardiovascular AI assistant grounded on AHA/ACC & WHO clinical protocols.
              </p>
            </div>
          </div>
        </header>

        {/* Emergency Triage Banner */}
        {emergencyDetected && (
          <div className="px-6 pt-3 shrink-0">
            <EmergencyBanner onDismiss={() => setEmergencyDetected(false)} />
          </div>
        )}

        {/* Workspace Split Layout: Conversations Sidebar + Chat Messages */}
        <div className="flex-1 flex overflow-hidden">
          {/* Left Session Column */}
          <div className="w-72 bg-warm-bg border-r border-warm-border p-4 flex flex-col justify-between shrink-0 hidden md:flex">
            <div className="space-y-3">
              <button
                onClick={handleCreateConversation}
                className="w-full flex items-center justify-center space-x-2 py-2.5 px-4 rounded-xl bg-brand-800 text-white text-xs font-bold hover:bg-brand-900 transition-all shadow-md shadow-brand-900/20"
              >
                <Plus className="w-4 h-4" />
                <span>New Consultation</span>
              </button>

              <div className="text-[10px] font-bold text-warm-muted uppercase tracking-wider px-2 pt-2">
                Past Sessions
              </div>

              <div className="space-y-1.5 overflow-y-auto max-h-[calc(100vh-250px)] pr-1">
                {conversations.map((c) => (
                  <div
                    key={c.id}
                    onClick={() => setActiveConvId(c.id)}
                    className={`flex items-center justify-between p-3 rounded-xl cursor-pointer text-xs transition-all ${
                      activeConvId === c.id
                        ? 'bg-white text-brand-800 font-bold border border-warm-border shadow-xs'
                        : 'text-gray-700 hover:bg-white/60'
                    }`}
                  >
                    <div className="flex items-center space-x-2 truncate">
                      <Bot className="w-3.5 h-3.5 shrink-0" />
                      <span className="truncate">{c.title}</span>
                    </div>
                    <button
                      onClick={(e) => handleDeleteConversation(c.id, e)}
                      className="p-1 rounded text-warm-muted hover:text-red-600 transition-colors"
                      title="Delete"
                    >
                      <Trash2 className="w-3.5 h-3.5" />
                    </button>
                  </div>
                ))}
              </div>
            </div>

            {/* Disclaimer pill */}
            <div className="p-3 bg-white rounded-xl border border-warm-border text-[10px] text-warm-muted space-y-1">
              <div className="flex items-center space-x-1 font-bold text-gray-700">
                <Info className="w-3 h-3 text-brand-800" />
                <span>Medical Notice</span>
              </div>
              <p>For educational & risk awareness. Never substitute for in-person cardiology triage.</p>
            </div>
          </div>

          {/* Main Chat Conversation View */}
          <div className="flex-1 flex flex-col bg-white overflow-hidden">
            {/* Messages Scroll Container */}
            <div className="flex-1 overflow-y-auto p-6 space-y-5">
              {/* Medical safety notice message */}
              <div className="p-3.5 bg-rose-50/60 rounded-2xl border border-brand-200/50 flex items-start space-x-3 text-xs text-brand-900 max-w-2xl mx-auto">
                <ShieldAlert className="w-4 h-4 text-brand-800 shrink-0 mt-0.5" />
                <p className="leading-relaxed">
                  <strong>Clinical Notice:</strong> HeartShield AI uses the Gemini 3.5 model with retrieval-augmented generation (RAG) over verified cardiovascular guidelines. If you experience acute chest tightness, radiating pain, or severe shortness of breath, please dial emergency medical services (911 / 112) immediately.
                </p>
              </div>

              {messages.map((msg, index) => {
                const isAssistant = msg.role === 'assistant';
                let parsedSources = [];
                if (msg.sources) {
                  try {
                    parsedSources = typeof msg.sources === 'string' ? JSON.parse(msg.sources) : msg.sources;
                  } catch (e) {
                    parsedSources = [];
                  }
                }

                return (
                  <div
                    key={msg.id || index}
                    className={`flex items-start space-x-3 ${isAssistant ? '' : 'flex-row-reverse space-x-reverse'}`}
                  >
                    <div
                      className={`w-8 h-8 rounded-full flex items-center justify-center shrink-0 text-xs font-bold ${
                        isAssistant
                          ? 'bg-brand-800 text-white shadow-xs'
                          : 'bg-warm-bg text-brand-900 border border-warm-border'
                      }`}
                    >
                      {isAssistant ? <Bot className="w-4 h-4" /> : <User className="w-4 h-4" />}
                    </div>

                    <div className={`max-w-2xl space-y-2 ${isAssistant ? 'text-left' : 'text-right'}`}>
                      <div
                        className={`p-4 rounded-3xl text-xs leading-relaxed inline-block text-left ${
                          isAssistant
                            ? 'bg-warm-bg text-gray-800 border border-warm-border shadow-xs'
                            : 'bg-brand-800 text-white font-medium shadow-md shadow-brand-900/10'
                        }`}
                      >
                        <div className="whitespace-pre-wrap">{msg.content}</div>
                      </div>

                      {/* RAG Grounding Citations */}
                      {isAssistant && parsedSources.length > 0 && (
                        <div className="flex flex-wrap gap-1.5 pt-1">
                          <span className="text-[10px] font-bold text-warm-muted uppercase tracking-wider block w-full">
                            Clinical Guideline Sources:
                          </span>
                          {parsedSources.map((src, idx) => (
                            <span
                              key={idx}
                              className="text-[10px] bg-brand-50 text-brand-800 px-2 py-0.5 rounded-full border border-brand-200 font-semibold"
                            >
                              📚 {src.title || src.source || 'AHA/ACC Guideline'}
                            </span>
                          ))}
                        </div>
                      )}

                      <span className="text-[10px] text-warm-muted block">
                        {new Date(msg.created_at || Date.now()).toLocaleTimeString([], {
                          hour: '2-digit',
                          minute: '2-digit',
                        })}
                      </span>
                    </div>
                  </div>
                );
              })}

              {/* Waiting indicator */}
              {sending && (
                <div className="flex items-start space-x-3">
                  <div className="w-8 h-8 rounded-full bg-brand-800 text-white flex items-center justify-center text-xs">
                    <Bot className="w-4 h-4" />
                  </div>
                  <div className="p-4 rounded-3xl bg-warm-bg border border-warm-border text-xs text-warm-muted flex items-center space-x-2">
                    <div className="w-2 h-2 rounded-full bg-brand-800 animate-pulse" />
                    <div className="w-2 h-2 rounded-full bg-brand-800 animate-pulse delay-75" />
                    <div className="w-2 h-2 rounded-full bg-brand-800 animate-pulse delay-150" />
                    <span className="text-xs font-semibold">HeartShield AI analyzing clinical parameters...</span>
                  </div>
                </div>
              )}

              <div ref={messagesEndRef} />
            </div>

            {/* Quick Prompt Recommendation Chips */}
            <div className="px-6 py-2 border-t border-warm-border/60 bg-warm-bg/50 flex items-center space-x-2 overflow-x-auto shrink-0">
              <span className="text-[10px] font-bold text-warm-muted uppercase tracking-wider shrink-0">
                Suggested:
              </span>
              {[
                'Explain my recent heart risk assessment',
                'What is a healthy LDL / HDL cholesterol level?',
                'Which physical exercises are safest for the heart?',
                'How does chronic stress elevate cardiac workload?',
              ].map((chip) => (
                <button
                  key={chip}
                  onClick={() => handleQuickPrompt(chip)}
                  className="px-3 py-1 rounded-full text-[11px] font-semibold bg-white border border-warm-border text-gray-700 hover:border-brand-800 hover:text-brand-800 transition-all shrink-0 shadow-xs"
                >
                  {chip}
                </button>
              ))}
            </div>

            {/* Bottom Message Input Box */}
            <div className="p-4 bg-white border-t border-warm-border shrink-0">
              {/* Attached Report Pill */}
              {selectedReportId && (
                <div className="mb-2 flex items-center justify-between bg-brand-50 border border-brand-200 px-3 py-1.5 rounded-xl text-xs text-brand-900 max-w-xl">
                  <div className="flex items-center space-x-2 truncate">
                    <Paperclip className="w-3.5 h-3.5 text-brand-800 shrink-0" />
                    <span className="font-semibold truncate">
                      Attached Report:{' '}
                      {reports.find((r) => r.id === selectedReportId)?.original_filename || `Report #${selectedReportId}`}
                    </span>
                  </div>
                  <button
                    onClick={() => setSelectedReportId(null)}
                    className="text-brand-800 hover:text-brand-900 font-bold p-1"
                  >
                    <X className="w-3.5 h-3.5" />
                  </button>
                </div>
              )}

              <form onSubmit={handleSendMessage} className="flex items-center space-x-3">
                {/* Report Attachment Dropdown */}
                {reports.length > 0 && (
                  <div className="relative">
                    <select
                      value={selectedReportId || ''}
                      onChange={(e) => setSelectedReportId(e.target.value ? Number(e.target.value) : null)}
                      className="text-xs bg-warm-bg border border-warm-border rounded-2xl py-3 px-3 text-gray-700 focus:outline-none focus:border-brand-800"
                      title="Attach Medical Report"
                    >
                      <option value="">Attach Lab Report (Optional)</option>
                      {reports.map((r) => (
                        <option key={r.id} value={r.id}>
                          {r.original_filename || r.file_name} ({r.report_type})
                        </option>
                      ))}
                    </select>
                  </div>
                )}

                {/* Input Text Box */}
                <div className="flex-1 relative">
                  <input
                    type="text"
                    value={inputMessage}
                    onChange={(e) => setInputMessage(e.target.value)}
                    placeholder="Ask HeartShield AI about your heart health, biomarkers, or lifestyle habits..."
                    className="w-full pl-4 pr-12 py-3 bg-warm-bg border border-warm-border rounded-2xl text-xs text-gray-900 focus:outline-none focus:border-brand-800 transition-all"
                  />
                  <button
                    type="submit"
                    disabled={!inputMessage.trim() || sending}
                    className="absolute right-2 top-1/2 -translate-y-1/2 p-2 rounded-xl bg-brand-800 text-white hover:bg-brand-900 transition-all shadow-md shadow-brand-900/20 disabled:opacity-40"
                  >
                    <Send className="w-3.5 h-3.5" />
                  </button>
                </div>
              </form>
            </div>
          </div>
        </div>
      </main>
    </div>
  );
}
