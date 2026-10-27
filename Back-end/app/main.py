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
from app.api.consultations import router as consultations_router
from app.api.consultation_chat import router as consultation_chat_router
from app.api.doctor_assessments import router as doctor_assessments_router
from app.core.security_headers import SecurityHeadersMiddleware
from app.core.rate_limiter import rate_limiter
from app.core.security_logger import security_logger
import uuid
from fastapi.responses import JSONResponse
from fastapi import Request
from starlette.exceptions import HTTPException as StarletteHTTPException
from fastapi.exceptions import RequestValidationError
import logging

logger = logging.getLogger("heartshield_app")

app = FastAPI(
    title="HeartShield API",
    version="1.0.0"
)

# Layer 1: Security Headers
app.add_middleware(SecurityHeadersMiddleware)

# Layer 2: Auth Rate Limiter Middleware
@app.middleware("http")
async def rate_limit_auth_middleware(request: Request, call_next):
    path = request.url.path
    if request.method != "OPTIONS" and any(route in path for route in [
        "/api/v1/auth/login",
        "/api/v1/auth/register",
        "/api/v1/auth/send-otp",
        "/api/v1/auth/verify-otp"
    ]):
        client_ip = request.client.host if request.client else "127.0.0.1"
        key = f"auth:{path}:{client_ip}"
        allowed, retry_after = rate_limiter.is_allowed(key, max_requests=25, window_seconds=60)
        if not allowed:
            security_logger.log_rate_limit(client_ip, path)
            return JSONResponse(
                status_code=429,
                content={"detail": f"Rate limit exceeded. Please wait {retry_after} seconds before retrying."}
            )
    return await call_next(request)

# Layer 5: Centralized Error Sanitization Handler
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    if isinstance(exc, (StarletteHTTPException, RequestValidationError)):
        raise exc
    tracking_id = uuid.uuid4().hex[:12]
    logger.error(f"Unhandled server error [{tracking_id}] on {request.method} {request.url.path}: {exc}", exc_info=True)
    return JSONResponse(
        status_code=500,
        content={
            "detail": "An internal server error occurred. Please contact support.",
            "tracking_id": tracking_id
        }
    )




app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "http://localhost:5173",
        "http://127.0.0.1:3000",
        "http://127.0.0.1:5173",
        "https://heartshield-frontend.onrender.com",
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
app.include_router(consultations_router)
app.include_router(consultation_chat_router)
app.include_router(doctor_assessments_router)

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
