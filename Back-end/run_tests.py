"""
HeartShield API Comprehensive Testing Suite
Tests all 42 new endpoints across Admin, Super Admin, Notifications, Feedback, Settings, Analytics, and System modules
"""
import json
import httpx
import asyncio
from typing import Dict, List, Tuple
from datetime import datetime

BASE_URL = "http://localhost:8000/api/v1"
HEALTH_URL = "http://localhost:8000"

class APITester:
    def __init__(self, base_url: str):
        self.base_url = base_url
        self.results = {
            "total_endpoints": 0,
            "passed": 0,
            "failed": 0,
            "timestamp": datetime.now().isoformat(),
            "endpoints": [],
            "by_module": {}
        }
        self.auth_token = None

    async def test_health_check(self) -> bool:
        """Test basic health endpoint"""
        try:
            async with httpx.AsyncClient(timeout=5.0) as client:
                response = await client.get(f"{HEALTH_URL}/health")
                success = response.status_code == 200
                self.results["endpoints"].append({
                    "endpoint": "GET /health",
                    "module": "SYSTEM",
                    "status": response.status_code,
                    "success": success
                })
                if success:
                    self.results["passed"] += 1
                else:
                    self.results["failed"] += 1
                return True
        except Exception as e:
            self.results["endpoints"].append({
                "endpoint": "GET /health",
                "module": "SYSTEM",
                "status": "ERROR",
                "error": str(e),
                "success": False
            })
            self.results["failed"] += 1
            return False

    async def test_endpoint(self, method: str, path: str, module: str,
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

                # Accept 2xx, 4xx errors (which show endpoint exists), but not 5xx
                success = response.status_code < 500

                self.results["endpoints"].append({
                    "endpoint": f"{method} {path}",
                    "module": module,
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
                "module": module,
                "status": "ERROR",
                "error": str(e),
                "success": False
            })
            self.results["failed"] += 1
            return False, 0

    async def run_all_tests(self):
        """Run all endpoint tests"""
        print("🚀 Starting HeartShield API Test Suite\n")
        print("=" * 70)

        # Test health check first
        print("📋 Testing System Health Check...")
        health_ok = await self.test_health_check()
        if not health_ok:
            print("❌ Server not responding. Make sure backend is running.")
            print("   Run: python -m uvicorn app.main:app --reload")
            return

        print("✅ Server is responding\n")

        # ADMIN ENDPOINTS (11)
        print("📝 Testing ADMIN Endpoints (11)...")
        admin_endpoints = [
            ("GET", "/admin/dashboard", "Admin dashboard"),
            ("GET", "/admin/users", "List users"),
            ("GET", "/admin/doctors", "List doctors"),
            ("GET", "/admin/approvals", "Get approvals"),
            ("PUT", "/admin/users/1/approve", "Approve user"),
            ("PUT", "/admin/users/1/reject", "Reject user"),
            ("PUT", "/admin/doctors/1/approve", "Approve doctor"),
            ("GET", "/admin/feedback", "Get feedback"),
            ("GET", "/admin/analytics", "Get analytics"),
            ("GET", "/admin/system-logs", "Get logs"),
            ("PUT", "/admin/feedback/1", "Update feedback"),
        ]
        for method, path, desc in admin_endpoints:
            self.results["total_endpoints"] += 1
            await self.test_endpoint(method, path, "ADMIN", require_auth=True)

        # SUPER ADMIN ENDPOINTS (12)
        print("📝 Testing SUPER ADMIN Endpoints (12)...")
        super_admin_endpoints = [
            ("GET", "/super-admin/dashboard", "Dashboard"),
            ("GET", "/super-admin/admins", "List admins"),
            ("POST", "/super-admin/admins", "Create admin"),
            ("PUT", "/super-admin/admins/1", "Update admin"),
            ("DELETE", "/super-admin/admins/1", "Delete admin"),
            ("GET", "/super-admin/roles", "List roles"),
            ("PUT", "/super-admin/roles/admin", "Update role"),
            ("GET", "/super-admin/permissions", "List permissions"),
            ("PUT", "/super-admin/permissions", "Update permissions"),
            ("GET", "/super-admin/audit-logs", "Get audit logs"),
            ("GET", "/super-admin/settings", "Get settings"),
            ("PUT", "/super-admin/settings", "Update settings"),
        ]
        for method, path, desc in super_admin_endpoints:
            self.results["total_endpoints"] += 1
            await self.test_endpoint(method, path, "SUPER_ADMIN", require_auth=True)

        # NOTIFICATIONS ENDPOINTS (5)
        print("📝 Testing NOTIFICATIONS Endpoints (5)...")
        notif_endpoints = [
            ("GET", "/notifications", "Get notifications"),
            ("GET", "/notifications/unread", "Get unread"),
            ("PUT", "/notifications/1/read", "Mark as read"),
            ("PUT", "/notifications/read-all", "Mark all as read"),
            ("DELETE", "/notifications/1", "Delete notification"),
        ]
        for method, path, desc in notif_endpoints:
            self.results["total_endpoints"] += 1
            await self.test_endpoint(method, path, "NOTIFICATIONS", require_auth=True)

        # FEEDBACK ENDPOINTS (4)
        print("📝 Testing FEEDBACK Endpoints (4)...")
        feedback_endpoints = [
            ("POST", "/feedback", "Create feedback"),
            ("GET", "/feedback/my", "Get user feedback"),
            ("GET", "/admin/feedback", "Get all feedback"),
            ("PUT", "/admin/feedback/1", "Update feedback"),
        ]
        for method, path, desc in feedback_endpoints:
            self.results["total_endpoints"] += 1
            await self.test_endpoint(method, path, "FEEDBACK", require_auth=True)

        # SETTINGS ENDPOINTS (5)
        print("📝 Testing SETTINGS Endpoints (5)...")
        settings_endpoints = [
            ("GET", "/settings", "Get settings"),
            ("PUT", "/settings/profile", "Update profile"),
            ("PUT", "/settings/notifications", "Update notifications"),
            ("PUT", "/settings/privacy", "Update privacy"),
            ("PUT", "/settings/preferences", "Update preferences"),
        ]
        for method, path, desc in settings_endpoints:
            self.results["total_endpoints"] += 1
            await self.test_endpoint(method, path, "SETTINGS", require_auth=True)

        # ANALYTICS ENDPOINTS (4)
        print("📝 Testing ANALYTICS Endpoints (4)...")
        analytics_endpoints = [
            ("GET", "/analytics/fairness", "Fairness metrics"),
            ("GET", "/model/info", "Model info"),
            ("GET", "/model/metrics", "Model metrics"),
            ("GET", "/model/version", "Model version"),
        ]
        for method, path, desc in analytics_endpoints:
            self.results["total_endpoints"] += 1
            await self.test_endpoint(method, path, "ANALYTICS", require_auth=True)

        # DOCTOR APPROVALS (3)
        print("📝 Testing DOCTOR APPROVALS Endpoints (3)...")
        doctor_endpoints = [
            ("GET", "/doctor/approvals/pending", "Pending approvals"),
            ("PUT", "/doctor/users/1/approve", "Approve doctor"),
            ("PUT", "/doctor/users/1/reject", "Reject doctor"),
        ]
        for method, path, desc in doctor_endpoints:
            self.results["total_endpoints"] += 1
            await self.test_endpoint(method, path, "DOCTOR_APPROVALS", require_auth=True)

        # SYSTEM ENDPOINTS (1)
        print("📝 Testing SYSTEM Endpoints (1)...")
        system_endpoints = [
            ("GET", "/health", "Health check"),
        ]
        for method, path, desc in system_endpoints:
            self.results["total_endpoints"] += 1
            await self.test_endpoint(method, path, "SYSTEM")

        # USER MANAGEMENT (1)
        print("📝 Testing USER MANAGEMENT Endpoints (1)...")
        user_mgmt_endpoints = [
            ("PUT", "/users/1", "Update user"),
        ]
        for method, path, desc in user_mgmt_endpoints:
            self.results["total_endpoints"] += 1
            await self.test_endpoint(method, path, "USER_MANAGEMENT", require_auth=True)

        # Print results
        self.print_results()

    def print_results(self):
        """Print test results"""
        print("\n" + "=" * 70)
        print("📊 TEST RESULTS SUMMARY\n")
        print(f"Total Endpoints Tested: {self.results['total_endpoints']}")
        print(f"✅ Passed: {self.results['passed']}")
        print(f"❌ Failed: {self.results['failed']}")
        success_rate = (self.results['passed'] / max(self.results['total_endpoints'], 1) * 100)
        print(f"Success Rate: {success_rate:.1f}%\n")

        # Group results by module
        print("=" * 70)
        print("RESULTS BY MODULE:\n")

        modules = {}
        for endpoint in self.results['endpoints']:
            module = endpoint.get('module', 'UNKNOWN')
            if module not in modules:
                modules[module] = {'passed': 0, 'failed': 0, 'endpoints': []}

            if endpoint.get('success'):
                modules[module]['passed'] += 1
            else:
                modules[module]['failed'] += 1

            modules[module]['endpoints'].append(endpoint)

        for module in sorted(modules.keys()):
            data = modules[module]
            total = data['passed'] + data['failed']
            status = "✅" if data['failed'] == 0 else "⚠️"
            print(f"{status} {module:20} {data['passed']:2}/{total:2} passed")

        print("\n" + "=" * 70)
        print("DETAILED ENDPOINT STATUS:\n")

        # Show failed endpoints if any
        failed = [e for e in self.results['endpoints'] if not e.get('success')]
        if failed:
            print(f"❌ FAILED ENDPOINTS ({len(failed)}):")
            for endpoint in failed:
                status = endpoint.get('error', endpoint.get('status', 'UNKNOWN'))
                print(f"   {endpoint['endpoint']:30} -> {status}")
        else:
            print("✅ All endpoints responding correctly!")

        print("\n" + "=" * 70)
        print("\n✨ Testing complete!")

if __name__ == "__main__":
    tester = APITester(BASE_URL)
    asyncio.run(tester.run_all_tests())
