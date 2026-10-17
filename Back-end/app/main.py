from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

try:
    from app.api.doctors import router as doctor_router, doctor_router as new_doctor_router
except ImportError:
    try:
        from app.api.doctors import router as doctor_router
        new_doctor_router = None
    except ImportError:
        doctor_router = None
        new_doctor_router = None

try:
    from app.api.test_database import router as database_router
except ImportError:
    database_router = None

from app.api.auth import router as auth_router
from app.api.patients import router as patient_router
from app.api.assessments import router as assessment_router
from app.api.health_information import router as health_information_router
from app.api.predictions import router as predictions_router
from app.api.xai import router as xai_router
from app.api.reports import router as reports_router
from app.api.recommendations import router as recommendations_router
from app.api.admin import router as admin_router

try:
    from app.api import lifestyle
except ImportError:
    lifestyle = None

try:
    from app.api import notifications
except ImportError:
    notifications = None

try:
    from app.api import feedback
except ImportError:
    feedback = None

try:
    from app.api import settings
except ImportError:
    settings = None

try:
    from app.api import users
except ImportError:
    users = None

from app.api.super_admin import router as super_admin_router
from app.api.analytics import router as analytics_router
from app.api.chat import router as chat_router
from app.api.medical_reports import router as medical_reports_router

app = FastAPI(
    title="HeartShield API",
    version="1.0.0"
)


app.add_middleware(
    CORSMiddleware,

    allow_origins=[
        "http://localhost:3000",
        "http://localhost:5173",
        "http://127.0.0.1:3000",
        "http://127.0.0.1:5173",
        "https://heartshield-sandstone.vercel.app",
    ],

    allow_credentials=True,

    allow_methods=["*"],

    allow_headers=["*"],
)


# REGISTER DATABASE TEST ROUTER
if database_router:
    app.include_router(database_router)

app.include_router(auth_router)
app.include_router(patient_router)
app.include_router(assessment_router)

if doctor_router:
    app.include_router(doctor_router)

app.include_router(admin_router)

if new_doctor_router:
    app.include_router(new_doctor_router)

if users:
    app.include_router(users.router)

app.include_router(predictions_router)
app.include_router(xai_router)
app.include_router(reports_router)
app.include_router(recommendations_router)
app.include_router(
    health_information_router,
    prefix="/api/v1"
)

if lifestyle:
    app.include_router(
        lifestyle.router,
        prefix="/api/v1",
    )

if notifications:
    app.include_router(notifications.router)

if feedback:
    app.include_router(feedback.router)

if settings:
    app.include_router(settings.router)

app.include_router(super_admin_router)
app.include_router(analytics_router)
app.include_router(chat_router)
app.include_router(medical_reports_router)

@app.get("/")
def root():

    return {
        "message": "HeartShield Backend is Running"
    }


@app.get("/health")
def health_check():

    return {
        "status": "healthy"
    }