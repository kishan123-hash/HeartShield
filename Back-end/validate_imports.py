"""
Direct import validation - Test all module imports without starting server
"""
import sys
import traceback

print("🔍 Validating HeartShield Backend Imports\n")
print("=" * 70)

modules_to_test = [
    ("FastAPI", "from fastapi import FastAPI"),
    ("SQLAlchemy", "from sqlalchemy.orm import Session"),
    ("Pydantic", "from pydantic import BaseModel"),
    ("Auth Router", "from app.api.auth import router"),
    ("Predictions Router", "from app.api.predictions import router"),
    ("XAI Router", "from app.api.xai import router"),
    ("Reports Router", "from app.api.reports import router"),
    ("Recommendations Router", "from app.api.recommendations import router"),
    ("Admin Router", "from app.api.admin import router"),
    ("Super Admin Router", "from app.api.super_admin import router"),
    ("Analytics Router", "from app.api.analytics import router"),
    ("Doctors Router", "from app.api.doctors import router, doctor_router"),
    ("Notifications Module", "from app.api import notifications"),
    ("Feedback Module", "from app.api import feedback"),
    ("Settings Module", "from app.api import settings"),
    ("Users Module", "from app.api import users"),
]

passed = 0
failed = 0

for name, import_stmt in modules_to_test:
    try:
        exec(import_stmt)
        print(f"✅ {name:30} OK")
        passed += 1
    except Exception as e:
        print(f"❌ {name:30} FAILED")
        print(f"   Error: {str(e)[:80]}")
        failed += 1

print("\n" + "=" * 70)
print(f"\n📊 Import Validation Results:")
print(f"   ✅ Passed: {passed}/{len(modules_to_test)}")
print(f"   ❌ Failed: {failed}/{len(modules_to_test)}")

if failed == 0:
    print("\n✨ All imports successful! Server should start correctly.")
else:
    print(f"\n⚠️  Fix {failed} import error(s) before starting server.")

sys.exit(0 if failed == 0 else 1)
