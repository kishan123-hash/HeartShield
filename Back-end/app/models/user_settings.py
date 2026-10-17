from sqlalchemy import (
    Column,
    BigInteger,
    String,
    Boolean,
    DateTime,
    ForeignKey,
    func
)

from app.database.database import Base


class UserSettings(Base):
    __tablename__ = "user_settings"

    id = Column(
        BigInteger,
        primary_key=True,
        autoincrement=True
    )

    user_id = Column(
        BigInteger,
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        unique=True,
        index=True
    )

    # Notification settings
    email_notifications = Column(
        Boolean,
        default=True
    )

    assessment_notifications = Column(
        Boolean,
        default=True
    )

    doctor_notifications = Column(
        Boolean,
        default=True
    )

    system_notifications = Column(
        Boolean,
        default=True
    )

    # Privacy settings
    profile_visibility = Column(
        Boolean,
        default=True
    )

    data_sharing = Column(
        Boolean,
        default=False
    )

    # Preferences
    language = Column(
        String(20),
        default="en"
    )

    theme = Column(
        String(20),
        default="light"
    )

    timezone = Column(
        String(50),
        default="Asia/Kolkata"
    )

    created_at = Column(
        DateTime,
        server_default=func.now()
    )

    updated_at = Column(
        DateTime,
        server_default=func.now(),
        onupdate=func.now()
    )