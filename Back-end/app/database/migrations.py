import logging
from sqlalchemy import text
from app.database.database import engine, Base
import app.models  # Ensures all models are registered

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("migrations")


def run_migrations():
    """
    Safely creates new tables (chat_conversations, chat_messages, patient_medical_reports, reports)
    if they do not already exist, preserving all existing tables and data.
    """
    logger.info("Running safe, non-destructive schema migrations...")
    try:
        # Create tables that are missing
        Base.metadata.create_all(bind=engine)
        logger.info("Base.metadata.create_all completed successfully.")

        # Verify tables exist
        with engine.connect() as conn:
            result = conn.execute(text("SHOW TABLES;"))
            tables = [row[0] for row in result.fetchall()]
            logger.info(f"Verified live database tables: {tables}")
            
            required_tables = ["users", "patients", "assessments", "model_predictions", "chat_conversations", "chat_messages", "patient_medical_reports"]
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
