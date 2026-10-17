from sqlalchemy import Column, BigInteger, String, DateTime, ForeignKey, func
from app.database.database import Base


class ActivityLog(Base):
    __tablename__ = "activity_logs"

    id = Column(
        BigInteger,
        primary_key=True,
        autoincrement=True
    )

    user_id = Column(
        BigInteger,
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
        index=True
    )

    action = Column(
        String(255),
        nullable=False
    )

    entity_type = Column(
        String(100),
        nullable=True
    )

    entity_id = Column(
        BigInteger,
        nullable=True
    )

    ip_address = Column(
        String(45),
        nullable=True
    )

    created_at = Column(
        DateTime,
        server_default=func.now(),
        index=True
    )