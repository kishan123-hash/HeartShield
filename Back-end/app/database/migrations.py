import logging
from sqlalchemy import text, inspect
from app.database.database import engine, Base
import app.models  # Ensures all models are registered

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("migrations")


def run_migrations():
    """
    Safely creates new tables (doctor_patient_conversations, doctor_patient_messages, doctor_patient_attachments)
    and validates existing schema without dropping or destroying existing data.
    """
    logger.info("Running safe, non-destructive schema migrations...")
    try:
        # Create any missing tables registered in Base
        Base.metadata.create_all(bind=engine)
        logger.info("Base.metadata.create_all completed successfully.")

        inspector = inspect(engine)
        tables = inspector.get_table_names()
        logger.info(f"Verified live database tables: {tables}")

        # Check and update doctor_patient_relationships columns if needed
        if "doctor_patient_relationships" in tables:
            cols = [c["name"] for c in inspector.get_columns("doctor_patient_relationships")]
            with engine.connect() as conn:
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
            "doctor_patient_relationships",
            "doctor_patient_conversations",
            "doctor_patient_messages",
            "doctor_patient_attachments"
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
