from app.models.user import User
from app.models.patient import Patient
from app.models.doctor import Doctor
from app.models.assessment import Assessment
from app.models.prediction import ModelPrediction
from app.models.otp_verification import OTPVerification
from app.models.report import Report
from app.models.patient_lifestyle import PatientLifestyle
from app.models.patient_health_information import PatientHealthInformation
from app.models.feedback import Feedback
from app.models.notification import Notification
from app.models.activity_log import ActivityLog
from app.models.user_settings import UserSettings
from app.models.doctor_note import DoctorNote
from app.models.chat import ChatConversation, ChatMessage
from app.models.medical_report import PatientMedicalReport
from app.models.doctor_patient_relationship import DoctorPatientRelationship
from app.models.consultation_chat import (
    DoctorPatientConversation,
    DoctorPatientMessage,
    DoctorPatientAttachment
)
from app.models.doctor_password_reset import DoctorPasswordResetRequest
