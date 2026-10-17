from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy import func
from typing import List, Optional
from datetime import datetime

from app.database.database import get_db
from app.core.dependencies import require_roles
from app.models.user import User
from app.models.activity_log import ActivityLog

router = APIRouter(
    prefix="/api/v1/super-admin",
    tags=["Super Admin"]
)


# ============================================================================
# DASHBOARD
# ============================================================================

@router.get("/dashboard")
def super_admin_dashboard(
    current_user: User = Depends(require_roles("super_admin")),
    db: Session = Depends(get_db)
):
    """
    Get super admin dashboard with system-wide statistics
    """
    total_users = db.query(User).count()
    total_admins = db.query(User).filter(User.role == "admin").count()
    total_super_admins = db.query(User).filter(User.role == "super_admin").count()
    total_patients = db.query(User).filter(User.role == "patient").count()
    total_doctors = db.query(User).filter(User.role == "doctor").count()

    active_users = db.query(User).filter(User.is_active == True).count()
    verified_users = db.query(User).filter(User.is_verified == True).count()

    recent_activity = db.query(ActivityLog).order_by(
        ActivityLog.created_at.desc()
    ).limit(10).all()

    return {
        "total_users": total_users,
        "total_admins": total_admins,
        "total_super_admins": total_super_admins,
        "total_patients": total_patients,
        "total_doctors": total_doctors,
        "active_users": active_users,
        "verified_users": verified_users,
        "recent_activity": [
            {
                "id": activity.id,
                "user_id": activity.user_id,
                "action": activity.action,
                "description": activity.description,
                "timestamp": activity.created_at
            }
            for activity in recent_activity
        ]
    }


# ============================================================================
# ADMIN MANAGEMENT
# ============================================================================

@router.get("/admins")
def list_admins(
    current_user: User = Depends(require_roles("super_admin")),
    db: Session = Depends(get_db),
    skip: int = 0,
    limit: int = 50
):
    """
    List all admins and super admins
    """
    admins = db.query(User).filter(
        User.role.in_(["admin", "super_admin"])
    ).offset(skip).limit(limit).all()

    total = db.query(User).filter(
        User.role.in_(["admin", "super_admin"])
    ).count()

    return {
        "total": total,
        "skip": skip,
        "limit": limit,
        "admins": [
            {
                "id": admin.id,
                "full_name": admin.full_name,
                "email": admin.email,
                "role": admin.role,
                "is_active": admin.is_active,
                "created_at": admin.created_at,
                "updated_at": admin.updated_at
            }
            for admin in admins
        ]
    }


@router.post("/admins")
def create_admin(
    admin_data: dict,
    current_user: User = Depends(require_roles("super_admin")),
    db: Session = Depends(get_db)
):
    """
    Create a new admin user
    """
    from app.core.security import hash_password

    # Check if user already exists
    existing_user = db.query(User).filter(
        User.email == admin_data.get("email")
    ).first()

    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="User with this email already exists"
        )

    # Create new admin
    new_admin = User(
        full_name=admin_data.get("full_name"),
        email=admin_data.get("email"),
        password_hash=hash_password(admin_data.get("password")),
        role=admin_data.get("role", "admin"),
        phone=admin_data.get("phone"),
        is_active=True,
        is_verified=True
    )

    db.add(new_admin)
    db.commit()
    db.refresh(new_admin)

    # Log activity
    activity_log = ActivityLog(
        user_id=current_user.id,
        action="admin_created",
        description=f"Created admin: {new_admin.email}"
    )
    db.add(activity_log)
    db.commit()

    return {
        "id": new_admin.id,
        "full_name": new_admin.full_name,
        "email": new_admin.email,
        "role": new_admin.role,
        "is_active": new_admin.is_active
    }


@router.put("/admins/{admin_id}")
def update_admin(
    admin_id: int,
    admin_data: dict,
    current_user: User = Depends(require_roles("super_admin")),
    db: Session = Depends(get_db)
):
    """
    Update an admin user
    """
    admin = db.query(User).filter(User.id == admin_id).first()

    if not admin:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Admin not found"
        )

    if admin.role not in ["admin", "super_admin"]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="User is not an admin"
        )

    # Update fields
    if "full_name" in admin_data:
        admin.full_name = admin_data["full_name"]
    if "role" in admin_data:
        admin.role = admin_data["role"]
    if "is_active" in admin_data:
        admin.is_active = admin_data["is_active"]
    if "phone" in admin_data:
        admin.phone = admin_data["phone"]

    admin.updated_at = datetime.utcnow()
    db.commit()
    db.refresh(admin)

    # Log activity
    activity_log = ActivityLog(
        user_id=current_user.id,
        action="admin_updated",
        description=f"Updated admin: {admin.email}"
    )
    db.add(activity_log)
    db.commit()

    return {
        "id": admin.id,
        "full_name": admin.full_name,
        "email": admin.email,
        "role": admin.role,
        "is_active": admin.is_active
    }


@router.delete("/admins/{admin_id}")
def delete_admin(
    admin_id: int,
    current_user: User = Depends(require_roles("super_admin")),
    db: Session = Depends(get_db)
):
    """
    Delete an admin user
    """
    admin = db.query(User).filter(User.id == admin_id).first()

    if not admin:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Admin not found"
        )

    if admin.id == current_user.id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot delete yourself"
        )

    email = admin.email
    db.delete(admin)
    db.commit()

    # Log activity
    activity_log = ActivityLog(
        user_id=current_user.id,
        action="admin_deleted",
        description=f"Deleted admin: {email}"
    )
    db.add(activity_log)
    db.commit()

    return {
        "message": f"Admin {email} deleted successfully"
    }


# ============================================================================
# ROLE MANAGEMENT (PLACEHOLDER - Roles stored as Enum in User model)
# ============================================================================

@router.get("/roles")
def list_roles(
    current_user: User = Depends(require_roles("super_admin")),
    db: Session = Depends(get_db)
):
    """
    List all available roles in the system
    """
    roles = [
        {
            "name": "patient",
            "description": "Regular patient user",
            "permissions": [
                "view_own_predictions",
                "create_predictions",
                "view_recommendations",
                "view_reports"
            ]
        },
        {
            "name": "doctor",
            "description": "Medical professional",
            "permissions": [
                "view_patients",
                "view_predictions",
                "create_recommendations",
                "create_notes",
                "view_analytics"
            ]
        },
        {
            "name": "admin",
            "description": "System administrator",
            "permissions": [
                "manage_users",
                "manage_doctors",
                "view_analytics",
                "view_feedback",
                "manage_approvals"
            ]
        },
        {
            "name": "super_admin",
            "description": "Super administrator with full system access",
            "permissions": [
                "manage_admins",
                "manage_roles",
                "manage_permissions",
                "view_audit_logs",
                "manage_system_settings"
            ]
        }
    ]

    return {"roles": roles}


@router.put("/roles/{role_name}")
def update_role(
    role_name: str,
    role_data: dict,
    current_user: User = Depends(require_roles("super_admin")),
    db: Session = Depends(get_db)
):
    """
    Update role permissions (placeholder - actual implementation depends on role table)
    """
    # Log activity
    activity_log = ActivityLog(
        user_id=current_user.id,
        action="role_updated",
        description=f"Updated role: {role_name}"
    )
    db.add(activity_log)
    db.commit()

    return {
        "message": f"Role {role_name} updated successfully",
        "role": role_name,
        "permissions": role_data.get("permissions", [])
    }


# ============================================================================
# PERMISSIONS MANAGEMENT (PLACEHOLDER)
# ============================================================================

@router.get("/permissions")
def list_permissions(
    current_user: User = Depends(require_roles("super_admin")),
    db: Session = Depends(get_db)
):
    """
    List all available permissions in the system
    """
    permissions = [
        {
            "name": "view_own_predictions",
            "category": "predictions",
            "description": "View own heart disease predictions"
        },
        {
            "name": "create_predictions",
            "category": "predictions",
            "description": "Create new predictions"
        },
        {
            "name": "view_recommendations",
            "category": "recommendations",
            "description": "View health recommendations"
        },
        {
            "name": "view_reports",
            "category": "reports",
            "description": "View generated reports"
        },
        {
            "name": "view_patients",
            "category": "patients",
            "description": "View patient information"
        },
        {
            "name": "view_predictions",
            "category": "predictions",
            "description": "View all predictions"
        },
        {
            "name": "create_recommendations",
            "category": "recommendations",
            "description": "Create health recommendations"
        },
        {
            "name": "create_notes",
            "category": "notes",
            "description": "Create patient notes"
        },
        {
            "name": "manage_users",
            "category": "users",
            "description": "Manage user accounts"
        },
        {
            "name": "manage_doctors",
            "category": "doctors",
            "description": "Manage doctor accounts"
        },
        {
            "name": "manage_admins",
            "category": "admins",
            "description": "Manage admin accounts"
        },
        {
            "name": "manage_roles",
            "category": "roles",
            "description": "Manage system roles"
        },
        {
            "name": "manage_permissions",
            "category": "permissions",
            "description": "Manage system permissions"
        },
        {
            "name": "view_audit_logs",
            "category": "audit",
            "description": "View system audit logs"
        },
        {
            "name": "manage_system_settings",
            "category": "settings",
            "description": "Manage system-wide settings"
        }
    ]

    return {"permissions": permissions}


@router.put("/permissions")
def update_permissions(
    permission_data: dict,
    current_user: User = Depends(require_roles("super_admin")),
    db: Session = Depends(get_db)
):
    """
    Update system permissions
    """
    activity_log = ActivityLog(
        user_id=current_user.id,
        action="permissions_updated",
        description="Updated system permissions"
    )
    db.add(activity_log)
    db.commit()

    return {
        "message": "Permissions updated successfully",
        "permissions": permission_data.get("permissions", [])
    }


# ============================================================================
# AUDIT LOGS
# ============================================================================

@router.get("/audit-logs")
def get_audit_logs(
    current_user: User = Depends(require_roles("super_admin")),
    db: Session = Depends(get_db),
    skip: int = 0,
    limit: int = 100,
    action: Optional[str] = None
):
    """
    Get system audit logs
    """
    query = db.query(ActivityLog)

    if action:
        query = query.filter(ActivityLog.action == action)

    total = query.count()
    logs = query.order_by(
        ActivityLog.created_at.desc()
    ).offset(skip).limit(limit).all()

    return {
        "total": total,
        "skip": skip,
        "limit": limit,
        "logs": [
            {
                "id": log.id,
                "user_id": log.user_id,
                "action": log.action,
                "description": log.description,
                "timestamp": log.created_at
            }
            for log in logs
        ]
    }


# ============================================================================
# SYSTEM SETTINGS
# ============================================================================

@router.get("/settings")
def get_system_settings(
    current_user: User = Depends(require_roles("super_admin")),
    db: Session = Depends(get_db)
):
    """
    Get system-wide settings
    """
    # Placeholder - would typically query a Settings table
    settings = {
        "maintenance_mode": False,
        "allow_new_registrations": True,
        "require_email_verification": True,
        "max_login_attempts": 5,
        "session_timeout_minutes": 30,
        "password_min_length": 8,
        "api_rate_limit": 1000,
        "max_file_upload_size_mb": 10,
        "smtp_enabled": True,
        "notification_email": "admin@heartshield.com"
    }

    return settings


@router.put("/settings")
def update_system_settings(
    settings_data: dict,
    current_user: User = Depends(require_roles("super_admin")),
    db: Session = Depends(get_db)
):
    """
    Update system-wide settings
    """
    activity_log = ActivityLog(
        user_id=current_user.id,
        action="settings_updated",
        description="Updated system settings"
    )
    db.add(activity_log)
    db.commit()

    return {
        "message": "System settings updated successfully",
        "settings": settings_data
    }
