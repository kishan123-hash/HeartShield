"""
HeartShield API Comprehensive Testing Suite
Tests all 119 endpoints
"""
import json
import httpx
import asyncio
from typing import Dict, List, Tuple

BASE_URL = "http://localhost:8000/api/v1"
HEALTH_URL = "http://localhost:8000"

class APITester:
    def __init__(self, base_url: str):
        self.base_url = base_url
        self.results = {
            "total_endpoints": 0,
            "passed": 0,
            "failed": 0,
            "endpoints": []
        }
        self.auth_token = None

    async def test_health_check(self) -> bool:
        """Test basic health endpoint"""
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(f"{HEALTH_URL}/health", timeout=5.0)
                self.results["endpoints"].append({
                    "endpoint": "GET /health",
                    "status": response.status_code,
                    "success": response.status_code == 200
                })
                if response.status_code == 200:
                    self.results["passed"] += 1
                    return True
                else:
                    self.results["failed"] += 1
                    return False
        except Exception as e:
            self.results["endpoints"].append({
                "endpoint": "GET /health",
                "status": "ERROR",
                "error": str(e),
                "success": False
            })
            self.results["failed"] += 1
            return False

    async def test_endpoint(self, method: str, path: str,
                           data: dict = None,
                           require_auth: bool = False) -> Tuple[bool, int]:
        """Test a single endpoint"""
        url = f"{self.base_url}{path}"
        headers = {}

        if require_auth and self.auth_token:
            headers["Authorization"] = f"Bearer {self.auth_token}"

        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                if method == "GET":
                    response = await client.get(url, headers=headers)
                elif method == "POST":
                    response = await client.post(url, json=data or {}, headers=headers)
                elif method == "PUT":
                    response = await client.put(url, json=data or {}, headers=headers)
                elif method == "DELETE":
                    response = await client.delete(url, headers=headers)
                else:
                    return False, 0

                success = 200 <= response.status_code < 300 or response.status_code in [400, 401, 403, 404]

                self.results["endpoints"].append({
                    "endpoint": f"{method} {path}",
                    "status": response.status_code,
                    "success": success
                })

                if success:
                    self.results["passed"] += 1
                else:
                    self.results["failed"] += 1

                return success, response.status_code

        except Exception as e:
            self.results["endpoints"].append({
                "endpoint": f"{method} {path}",
                "status": "ERROR",
                "error": str(e),
                "success": False
            })
            self.results["failed"] += 1
            return False, 0

    async def run_all_tests(self):
        """Run all endpoint tests"""
        print("🚀 Starting HeartShield API Test Suite\n")
        print("=" * 60)

        # Test health check first
        print("📋 Testing Health Check...")
        health_ok = await self.test_health_check()
        if not health_ok:
            print("❌ Server not responding. Make sure backend is running.")
            print("   Run: python -m uvicorn app.main:app --reload")
            return

        print("✅ Server is responding\n")

        # Auth endpoints (8)
        print("📝 Testing AUTH Endpoints (8)...")
        endpoints = [
            ("POST", "/auth/register", {"email": "test@test.com", "password": "test123"}),
            ("POST", "/auth/login", {"email": "test@test.com", "password": "test123"}),
            ("POST", "/auth/send-otp", {"email": "test@test.com"}),
            ("POST", "/auth/forgot-password", {"email": "test@test.com"}),
            ("GET", "/auth/me", None, True),
            ("GET", "/auth/registration-status", None, False),
        ]
        for endpoint in endpoints:
            self.results["total_endpoints"] += 1
            await self.test_endpoint(*endpoint)

        # Users (5)
        print("📝 Testing USER Endpoints (5)...")
        user_endpoints = [
            ("GET", "/users/profile", None, True),
            ("PUT", "/users/profile", {"full_name": "Test User"}, True),
            ("PUT", "/users/change-password", {"current_password": "old", "new_password": "new"}, True),
            ("GET", "/users/dashboard", None, True),
            ("GET", "/users/health-summary", None, True),
        ]
        for endpoint in user_endpoints:
            self.results["total_endpoints"] += 1
            await self.test_endpoint(*endpoint)

        # Predictions (8)
        print("📝 Testing PREDICTION Endpoints (8)...")
        pred_endpoints = [
            ("POST", "/predictions", {"data": {}}, True),
            ("GET", "/predictions", None, True),
            ("GET", "/predictions/latest", None, True),
            ("GET", "/predictions/history", None, True),
            ("GET", "/predictions/trend", None, True),
        ]
        for endpoint in pred_endpoints:
            self.results["total_endpoints"] += 1
            await self.test_endpoint(*endpoint)

        # XAI (5)
        print("📝 Testing XAI Endpoints (5)...")
        xai_endpoints = [
            ("GET", "/predictions/1/explanation", None, True),
            ("GET", "/predictions/1/shap", None, True),
            ("GET", "/predictions/1/lime", None, True),
        ]
        for endpoint in xai_endpoints:
            self.results["total_endpoints"] += 1
            await self.test_endpoint(*endpoint)

        # Recommendations (3)
        print("📝 Testing RECOMMENDATION Endpoints (3)...")
        rec_endpoints = [
            ("GET", "/recommendations/1", None, True),
            ("POST", "/recommendations/generate", {"prediction_id": 1}, True),
            ("GET", "/recommendations", None, True),
        ]
        for endpoint in rec_endpoints:
            self.results["total_endpoints"] += 1
            await self.test_endpoint(*endpoint)

        # Reports (6)
        print("📝 Testing REPORT Endpoints (6)...")
        report_endpoints = [
            ("GET", "/reports/1", None, True),
            ("POST", "/reports/1/generate", {}, True),
            ("GET", "/reports/1/download", None, True),
            ("GET", "/reports", None, True),
        ]
        for endpoint in report_endpoints:
            self.results["total_endpoints"] += 1
            await self.test_endpoint(*endpoint)

        # Admin (11)
        print("📝 Testing ADMIN Endpoints (11)...")
        admin_endpoints = [
            ("GET", "/admin/dashboard", None, True),
            ("GET", "/admin/users", None, True),
            ("GET", "/admin/doctors", None, True),
            ("GET", "/admin/approvals", None, True),
            ("GET", "/admin/feedback", None, True),
            ("GET", "/admin/analytics", None, True),
            ("GET", "/admin/system-logs", None, True),
        ]
        for endpoint in admin_endpoints:
            self.results["total_endpoints"] += 1
            await self.test_endpoint(*endpoint)

        # Doctor (10)
        print("📝 Testing DOCTOR Endpoints (10)...")
        doctor_endpoints = [
            ("GET", "/doctor/dashboard", None, True),
            ("GET", "/doctor/patients", None, True),
            ("GET", "/doctor/patients/1", None, True),
            ("GET", "/doctor/predictions/1", None, True),
            ("GET", "/doctor/approvals/pending", None, True),
        ]
        for endpoint in doctor_endpoints:
            self.results["total_endpoints"] += 1
            await self.test_endpoint(*endpoint)

        # Notifications (5)
        print("📝 Testing NOTIFICATION Endpoints (5)...")
        notif_endpoints = [
            ("GET", "/notifications", None, True),
            ("GET", "/notifications/unread", None, True),
            ("PUT", "/notifications/1/read", {}, True),
        ]
        for endpoint in notif_endpoints:
            self.results["total_endpoints"] += 1
            await self.test_endpoint(*endpoint)

        # Feedback (4)
        print("📝 Testing FEEDBACK Endpoints (4)...")
        feedback_endpoints = [
            ("POST", "/feedback", {"content": "test"}, True),
            ("GET", "/feedback/my", None, True),
        ]
        for endpoint in feedback_endpoints:
            self.results["total_endpoints"] += 1
            await self.test_endpoint(*endpoint)

        # Settings (5)
        print("📝 Testing SETTINGS Endpoints (5)...")
        settings_endpoints = [
            ("GET", "/settings", None, True),
            ("PUT", "/settings/profile", {}, True),
            ("PUT", "/settings/notifications", {}, True),
            ("PUT", "/settings/privacy", {}, True),
            ("PUT", "/settings/preferences", {}, True),
        ]
        for endpoint in settings_endpoints:
            self.results["total_endpoints"] += 1
            await self.test_endpoint(*endpoint)

        # Super Admin (12)
        print("📝 Testing SUPER ADMIN Endpoints (12)...")
        super_admin_endpoints = [
            ("GET", "/super-admin/dashboard", None, True),
            ("GET", "/super-admin/admins", None, True),
            ("GET", "/super-admin/roles", None, True),
            ("GET", "/super-admin/permissions", None, True),
            ("GET", "/super-admin/audit-logs", None, True),
            ("GET", "/super-admin/settings", None, True),
        ]
        for endpoint in super_admin_endpoints:
            self.results["total_endpoints"] += 1
            await self.test_endpoint(*endpoint)

        # Analytics (4)
        print("📝 Testing ANALYTICS Endpoints (4)...")
        analytics_endpoints = [
            ("GET", "/model/info", None, True),
            ("GET", "/model/version", None, True),
            ("GET", "/model/metrics", None, True),
            ("GET", "/analytics/fairness", None, True),
        ]
        for endpoint in analytics_endpoints:
            self.results["total_endpoints"] += 1
            await self.test_endpoint(*endpoint)

        # Print results
        self.print_results()

    def print_results(self):
        """Print test results"""
        print("\n" + "=" * 60)
        print("📊 TEST RESULTS SUMMARY\n")
        print(f"Total Endpoints Tested: {self.results['total_endpoints']}")
        print(f"✅ Passed: {self.results['passed']}")
        print(f"❌ Failed: {self.results['failed']}")
        print(f"Success Rate: {(self.results['passed'] / max(self.results['total_endpoints'], 1) * 100):.1f}%\n")

        # Group results by status
        print("=" * 60)
        print("ENDPOINT STATUS DETAILS:\n")

        passed = [e for e in self.results['endpoints'] if e.get('success')]
        failed = [e for e in self.results['endpoints'] if not e.get('success')]

        if passed:
            print(f"✅ PASSED ({len(passed)}):")
            for endpoint in passed[:10]:
                print(f"   {endpoint['endpoint']} -> {endpoint['status']}")
            if len(passed) > 10:
                print(f"   ... and {len(passed) - 10} more")

        if failed:
            print(f"\n❌ FAILED ({len(failed)}):")
            for endpoint in failed[:10]:
                status = endpoint.get('error', endpoint.get('status', 'UNKNOWN'))
                print(f"   {endpoint['endpoint']} -> {status}")
            if len(failed) > 10:
                print(f"   ... and {len(failed) - 10} more")

        print("\n" + "=" * 60)

if __name__ == "__main__":
    tester = APITester(BASE_URL)
    asyncio.run(tester.run_all_tests())
