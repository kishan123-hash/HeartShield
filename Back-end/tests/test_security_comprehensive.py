import os
import sys
import pytest
from fastapi.testclient import TestClient

# Ensure Back-end is in path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from app.main import app
from app.models.user import User
from app.core.dependencies import get_current_user


@pytest.fixture
def client():
    return TestClient(app)


def test_unauthenticated_endpoints_return_401(client):
    """OWASP A01: Broken Access Control - Enforce Authentication"""
    protected_urls = [
        "/api/v1/predictions/latest",
        "/api/v1/predictions",
        "/api/v1/chat/conversations",
        "/api/v1/medical-reports",
        "/api/v1/settings",
        "/api/v1/doctors/me",
        "/api/v1/admin/dashboard",
    ]

    for url in protected_urls:
        res = client.get(url)
        assert res.status_code == 401, f"Expected 401 for {url}, got {res.status_code}"

    print("\n[PASS] Security Check: All protected endpoints strictly require authentication (401).")


def test_rbac_privilege_escalation_prevention(client):
    """OWASP A01: Broken Access Control - Enforce Role Separation"""
    # Create patient mock user
    patient_user = User(
        id=999,
        full_name="Test Patient",
        email="patient@test.com",
        role="patient",
        is_active=True,
        is_verified=True
    )

    app.dependency_overrides[get_current_user] = lambda: patient_user

    try:
        # Attempt to access doctor-only endpoints as patient -> 403
        res_doctor = client.get("/api/v1/doctors/me")
        assert res_doctor.status_code == 403, f"Expected 403 for doctor endpoint, got {res_doctor.status_code}"

        # Attempt to access admin-only endpoints as patient -> 403
        res_admin = client.get("/api/v1/admin/dashboard")
        assert res_admin.status_code == 403, f"Expected 403 for admin endpoint, got {res_admin.status_code}"
    finally:
        app.dependency_overrides.pop(get_current_user, None)

    print("\n[PASS] Security Check: Role-Based Access Control blocked patient privilege escalation (403).")


def test_upload_spoofed_file_rejection(client):
    """OWASP A04: Insecure Design & File Signature Tampering"""
    patient_user = User(
        id=999,
        full_name="Test Patient",
        email="patient@test.com",
        role="patient",
        is_active=True,
        is_verified=True
    )

    app.dependency_overrides[get_current_user] = lambda: patient_user

    try:
        # Malicious binary masquerading as PDF
        fake_exe_content = b"MZ\x90\x00\x03\x00\x00\x00MaliciousExecutableContent"
        files = {
            "file": ("malicious_payload.pdf", fake_exe_content, "application/pdf")
        }
        data = {"report_type": "Lipid Panel"}

        res = client.post("/api/v1/medical-reports/upload", files=files, data=data)
        assert res.status_code == 400
        assert "signature does not match" in res.json().get("detail", "")
    finally:
        app.dependency_overrides.pop(get_current_user, None)

    print("\n[PASS] Security Check: Spoofed executable file signature was rejected with 400 Bad Request.")
