from sqlalchemy.dialects.mysql import BIGINT
from sqlalchemy import (
    Column,
    String,
    Text,
    DateTime,
    Boolean,
    func
)

from app.database.database import Base


class ContactMessage(Base):
    """
    Database model for Contact Us form submissions
    """
    __tablename__ = "contact_messages"

    id = Column(
        BIGINT(unsigned=True),
        primary_key=True,
        autoincrement=True
    )

    name = Column(
        String(150),
        nullable=False
    )

    email = Column(
        String(255),
        nullable=False,
        index=True
    )

    subject = Column(
        String(255),
        nullable=False
    )

    message = Column(
        Text,
        nullable=False
    )

    # Status: 'new', 'in_progress', 'resolved'
    status = Column(
        String(50),
        default="new",
        nullable=False
    )

    is_read = Column(
        Boolean,
        default=False,
        nullable=False
    )

    created_at = Column(
        DateTime,
        server_default=func.now(),
        nullable=False
    )

    updated_at = Column(
        DateTime,
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False
    )
