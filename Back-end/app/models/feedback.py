from sqlalchemy import Column, BigInteger, Text, String, Integer, DateTime, ForeignKey, func
from app.database.database import Base


class Feedback(Base):
    __tablename__ = "feedback"

    id = Column(BigInteger, primary_key=True, autoincrement=True)

    user_id = Column(
        BigInteger,
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )

    rating = Column(Integer, nullable=False)

    feedback_text = Column(Text, nullable=False)

    category = Column(
        String(50),
        default="other",
        nullable=True
    )

    status = Column(
        String(20),
        default="new",
        nullable=True,
        index=True
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