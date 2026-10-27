import React, { useState, useEffect } from 'react';
import {
  MessageSquare,
  Star,
  Send,
  CheckCircle2,
  AlertCircle,
  Clock,
  Sparkles,
  X
} from 'lucide-react';
import Sidebar from '../components/Sidebar';
import api from '../api/client';

export default function FeedbackPage() {
  const [rating, setRating] = useState(5);
  const [hoverRating, setHoverRating] = useState(0);
  const [category, setCategory] = useState('general');
  const [feedbackText, setFeedbackText] = useState('');
  const [submitting, setSubmitting] = useState(false);
  const [success, setSuccess] = useState('');
  const [error, setError] = useState('');
  const [myFeedback, setMyFeedback] = useState([]);
  const [loading, setLoading] = useState(true);

  const fetchMyFeedback = async () => {
    setLoading(true);
    try {
      const res = await api.get('/feedback/my');
      setMyFeedback(res.data?.feedback || []);
    } catch (err) {
      console.warn('Feedback fetch notice:', err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchMyFeedback();
  }, []);

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!feedbackText.trim()) {
      setError('Please provide your feedback comments.');
      return;
    }

    setSubmitting(true);
    setError('');
    setSuccess('');

    try {
      await api.post('/feedback', null, {
        params: {
          rating: rating,
          feedback_text: feedbackText.trim(),
          category: category,
        },
      });

      setSuccess('Thank you! Your feedback helps refine our clinical AI ensemble.');
      setFeedbackText('');
      setRating(5);
      fetchMyFeedback();
    } catch (err) {
      console.error('Feedback submit error:', err);
      setError(err.response?.data?.detail || 'Failed to submit feedback. Please try again.');
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <div className="min-h-screen flex flex-col lg:flex-row bg-warm-bg w-full min-w-0 overflow-x-hidden">
      <Sidebar />

      <main className="flex-1 p-4 sm:p-6 lg:p-10 max-w-4xl w-full mx-auto space-y-8 min-w-0">
        {/* Header */}
        <div>
          <span className="text-[11px] font-bold uppercase tracking-wider text-brand-800 bg-brand-50 px-2.5 py-0.5 rounded-full border border-brand-200">
            User Experience
          </span>
          <h1 className="text-2xl font-black text-gray-900 tracking-tight mt-1">
            Platform Feedback & Insights
          </h1>
          <p className="text-xs text-warm-muted mt-1">
            Share your experience with HeartShield's predictive models, explainability charts, and AI health chatbot.
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

        {/* Feedback Submission Card */}
        <div className="bg-white p-6 sm:p-8 rounded-3xl border border-warm-border shadow-xs">
          <form onSubmit={handleSubmit} className="space-y-6">
            {/* Star Rating */}
            <div className="space-y-2">
              <label className="block text-xs font-bold text-gray-800">
                Overall Experience Rating
              </label>
              <div className="flex items-center space-x-2">
                {[1, 2, 3, 4, 5].map((star) => (
                  <button
                    key={star}
                    type="button"
                    onClick={() => setRating(star)}
                    onMouseEnter={() => setHoverRating(star)}
                    onMouseLeave={() => setHoverRating(0)}
                    className="p-1 text-amber-400 hover:scale-110 transition-transform"
                  >
                    <Star
                      className={`w-7 h-7 ${
                        (hoverRating || rating) >= star ? 'fill-amber-400 text-amber-400' : 'text-gray-300'
                      }`}
                    />
                  </button>
                ))}
                <span className="text-xs font-bold text-brand-800 ml-2">
                  {rating === 5 ? 'Excellent' : rating === 4 ? 'Good' : rating === 3 ? 'Average' : 'Needs Improvement'}
                </span>
              </div>
            </div>

            {/* Category */}
            <div>
              <label className="block text-xs font-bold text-gray-800 mb-1.5">
                Feedback Category
              </label>
              <select
                value={category}
                onChange={(e) => setCategory(e.target.value)}
                className="w-full sm:w-80 px-3.5 py-2.5 bg-warm-bg border border-warm-border rounded-xl text-xs text-gray-900 focus:outline-none focus:border-brand-800"
              >
                <option value="general">General Feedback</option>
                <option value="model_accuracy">AI Prediction Accuracy & SHAP</option>
                <option value="chatbot">AI Health Chatbot & Guidance</option>
                <option value="ui_usability">Design & Navigation</option>
                <option value="bug_report">Bug Report / Technical Issue</option>
              </select>
            </div>

            {/* Message Area */}
            <div>
              <label className="block text-xs font-bold text-gray-800 mb-1.5">
                Your Comments & Suggestions
              </label>
              <textarea
                rows={4}
                value={feedbackText}
                onChange={(e) => setFeedbackText(e.target.value)}
                placeholder="What did you like? What can we improve in risk assessment or report generation?"
                className="w-full p-4 bg-warm-bg border border-warm-border rounded-2xl text-xs text-gray-900 focus:outline-none focus:border-brand-800 transition-all leading-relaxed"
              />
            </div>

            <button
              type="submit"
              disabled={submitting}
              className="inline-flex items-center space-x-2 px-8 py-3 rounded-full text-xs font-bold text-white bg-brand-800 hover:bg-brand-900 transition-all shadow-md shadow-brand-900/20 disabled:opacity-50"
            >
              <Send className="w-4 h-4" />
              <span>{submitting ? 'Submitting...' : 'Submit Feedback'}</span>
            </button>
          </form>
        </div>

        {/* Past Feedback History */}
        <div className="bg-white rounded-3xl border border-warm-border shadow-xs p-6 space-y-4">
          <h3 className="text-sm font-bold text-gray-900">Your Submitted Feedback</h3>
          {loading ? (
            <p className="text-xs text-warm-muted">Loading feedback history...</p>
          ) : myFeedback.length === 0 ? (
            <p className="text-xs text-warm-muted">You haven't submitted any feedback yet.</p>
          ) : (
            <div className="divide-y divide-warm-border">
              {myFeedback.map((fb) => (
                <div key={fb.id} className="py-4 space-y-1.5">
                  <div className="flex items-center justify-between text-xs">
                    <div className="flex items-center space-x-2">
                      <div className="flex text-amber-400">
                        {Array.from({ length: fb.rating || 5 }).map((_, i) => (
                          <Star key={i} className="w-3.5 h-3.5 fill-amber-400" />
                        ))}
                      </div>
                      <span className="capitalize px-2 py-0.5 rounded-full text-[10px] font-bold bg-warm-bg text-gray-700 border border-warm-border">
                        {fb.category}
                      </span>
                    </div>
                    <span className="text-[11px] text-warm-muted">
                      {fb.created_at ? new Date(fb.created_at).toLocaleDateString() : ''}
                    </span>
                  </div>
                  <p className="text-xs text-gray-800 leading-relaxed">{fb.feedback_text}</p>
                </div>
              ))}
            </div>
          )}
        </div>
      </main>
    </div>
  );
}
