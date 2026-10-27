import React from 'react';
import { Routes, Route, Navigate } from 'react-router-dom';
import ProtectedRoute from './components/ProtectedRoute';

// Public Pages (Screens 1 - 10)
import LandingPage from './pages/LandingPage';
import AboutUsPage from './pages/AboutUsPage';
import FeaturesPage from './pages/FeaturesPage';
import HowItWorksPage from './pages/HowItWorksPage';
import FaqPage from './pages/FaqPage';
import ContactPage from './pages/ContactPage';
import LoginPage from './pages/LoginPage';
import RegisterPage from './pages/RegisterPage';
import OtpVerificationPage from './pages/OtpVerificationPage';
import ForgotPasswordPage from './pages/ForgotPasswordPage';
import DoctorForgotPasswordPage from './pages/DoctorForgotPasswordPage';

// Patient Pages (Screens 11 - 15, Chatbot, Reports, Notifications, Feedback, Settings)
import PatientDashboardPage from './pages/PatientDashboardPage';
import PatientDoctorsPage from './pages/PatientDoctorsPage';
import RiskAssessmentPage from './pages/RiskAssessmentPage';
import PredictionResultPage from './pages/PredictionResultPage';
import PatientReportPage from './pages/PatientReportPage';
import PredictionHistoryPage from './pages/PredictionHistoryPage';
import MedicalReportsPage from './pages/MedicalReportsPage';
import ChatbotPage from './pages/ChatbotPage';
import ChatPage from './pages/ChatPage';
import NotificationsPage from './pages/NotificationsPage';
import FeedbackPage from './pages/FeedbackPage';
import SettingsPage from './pages/SettingsPage';

// Doctor Pages (Screens 16 & 17 + Consultation Management)
import DoctorDashboardPage from './pages/DoctorDashboardPage';
import DoctorPatientReviewPage from './pages/DoctorPatientReviewPage';
import DoctorRequestsPage from './pages/DoctorRequestsPage';
import DoctorAssessmentsPage from './pages/DoctorAssessmentsPage';

// Admin Pages (Screens 18 & 23)
import AdminDashboardPage from './pages/AdminDashboardPage';
import DoctorApprovalsPage from './pages/DoctorApprovalsPage';

export default function App() {
  return (
    <Routes>
      {/* Public Routes */}
      <Route path="/" element={<LandingPage />} />
      <Route path="/about" element={<AboutUsPage />} />
      <Route path="/features" element={<FeaturesPage />} />
      <Route path="/how-it-works" element={<HowItWorksPage />} />
      <Route path="/faq" element={<FaqPage />} />
      <Route path="/contact" element={<ContactPage />} />
      <Route path="/login" element={<LoginPage />} />
      <Route path="/register" element={<RegisterPage />} />
      <Route path="/verify-otp" element={<OtpVerificationPage />} />
      <Route path="/forgot-password" element={<ForgotPasswordPage />} />
      <Route path="/doctor/forgot-password" element={<DoctorForgotPasswordPage />} />

      {/* Patient Protected Routes */}
      <Route element={<ProtectedRoute allowedRoles={['patient', 'doctor', 'admin']} />}>
        <Route path="/patient/dashboard" element={<PatientDashboardPage />} />
        <Route path="/patient/doctors" element={<PatientDoctorsPage />} />
        <Route path="/patient/doctor-chat" element={<ChatPage />} />
        <Route path="/patient/assessment" element={<RiskAssessmentPage />} />
        <Route path="/patient/prediction-result/:id" element={<PredictionResultPage />} />
        <Route path="/patient/report/:id" element={<PatientReportPage />} />
        <Route path="/patient/history" element={<PredictionHistoryPage />} />
        <Route path="/patient/medical-reports" element={<MedicalReportsPage />} />
        <Route path="/patient/chat" element={<ChatbotPage />} />
        <Route path="/patient/notifications" element={<NotificationsPage />} />
        <Route path="/patient/feedback" element={<FeedbackPage />} />
        <Route path="/patient/settings" element={<SettingsPage />} />
      </Route>

      {/* Doctor Protected Routes */}
      <Route element={<ProtectedRoute allowedRoles={['doctor', 'admin']} />}>
        <Route path="/doctor/dashboard" element={<DoctorDashboardPage />} />
        <Route path="/doctor/requests" element={<DoctorRequestsPage />} />
        <Route path="/doctor/chat" element={<ChatPage />} />
        <Route path="/doctor/assessments" element={<DoctorAssessmentsPage />} />
        <Route path="/doctor/patient/:id" element={<DoctorPatientReviewPage />} />
      </Route>

      {/* Admin Protected Routes */}
      <Route element={<ProtectedRoute allowedRoles={['admin']} />}>
        <Route path="/admin/dashboard" element={<AdminDashboardPage />} />
        <Route path="/admin/approvals" element={<DoctorApprovalsPage />} />
      </Route>

      {/* Catch-all Fallback */}
      <Route path="*" element={<Navigate to="/" replace />} />
    </Routes>
  );
}
