import logging
from sqlalchemy import text, inspect
from app.database.database import engine, Base
import app.models  # Ensures all models are registered

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("migrations")


def run_migrations():
    """
    Safely creates new tables (account_unlock_tokens, etc.)
    and validates existing schema, adding required security columns without dropping or destroying existing data.
    """
    logger.info("Running safe, non-destructive schema migrations...")
    try:
        # Create any missing tables registered in Base
        Base.metadata.create_all(bind=engine)
        logger.info("Base.metadata.create_all completed successfully.")

        inspector = inspect(engine)
        tables = inspector.get_table_names()
        logger.info(f"Verified live database tables: {tables}")

        with engine.connect() as conn:
            # Check and update users table for security fields
            if "users" in tables:
                user_cols = [c["name"] for c in inspector.get_columns("users")]

                columns_to_add = [
                    ("failed_login_attempts", "INT NOT NULL DEFAULT 0"),
                    ("is_locked", "TINYINT(1) NOT NULL DEFAULT 0"),
                    ("locked_at", "DATETIME NULL"),
                    ("token_version", "INT NOT NULL DEFAULT 1"),
                    ("mfa_enabled", "TINYINT(1) NOT NULL DEFAULT 0"),
                    ("mfa_secret", "VARCHAR(255) NULL"),
                    ("mfa_recovery_codes", "TEXT NULL")
                ]

                for col_name, col_def in columns_to_add:
                    if col_name not in user_cols:
                        logger.info(f"Adding '{col_name}' column to users table...")
                        try:
                            conn.execute(text(f"ALTER TABLE users ADD COLUMN {col_name} {col_def};"))
                            conn.commit()
                            logger.info(f"Column '{col_name}' added successfully.")
                        except Exception as col_err:
                            logger.error(f"Error adding column '{col_name}': {col_err}")

            # Check and update doctor_patient_relationships columns if needed
            if "doctor_patient_relationships" in tables:
                cols = [c["name"] for c in inspector.get_columns("doctor_patient_relationships")]
                if "notes" not in cols:
                    logger.info("Adding 'notes' column to doctor_patient_relationships...")
                    conn.execute(text("ALTER TABLE doctor_patient_relationships ADD COLUMN notes TEXT NULL;"))
                    conn.commit()

                # Ensure enum supports pending, requested, active, approved, inactive, rejected
                try:
                    conn.execute(text(
                        "ALTER TABLE doctor_patient_relationships MODIFY COLUMN relationship_status "
                        "ENUM('pending','requested','active','approved','inactive','rejected') DEFAULT 'pending';"
                    ))
                    conn.commit()
                    logger.info("Updated relationship_status ENUM successfully.")
                except Exception as enum_err:
                    logger.warning(f"Note on ENUM update: {enum_err}")

        # Check required tables
        required_tables = [
            "users",
            "patients",
            "doctors",
            "assessments",
            "model_predictions",
            "account_unlock_tokens",
            "activity_logs",
            "otp_verifications"
        ]
        for req in required_tables:
            if req in tables:
                logger.info(f"  [OK] Table '{req}' exists.")
            else:
                logger.warning(f"  [MISSING] Table '{req}' was not found.")

        logger.info("Migration check complete.")
        return True
    except Exception as e:
        logger.error(f"Migration error: {e}", exc_info=True)
        return False


if __name__ == "__main__":
    success = run_migrations()
    if not success:
        exit(1)
