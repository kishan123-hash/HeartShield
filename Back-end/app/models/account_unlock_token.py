from sqlalchemy import (
    Column,
    String,
    Boolean,
    DateTime,
    ForeignKey,
    func
)
from sqlalchemy.dialects.mysql import BIGINT

from app.database.database import Base


class AccountUnlockToken(Base):
    __tablename__ = "account_unlock_tokens"

    id = Column(
        BIGINT(unsigned=True),
        primary_key=True,
        index=True,
        autoincrement=True
    )

    user_id = Column(
        BIGINT(unsigned=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )

    token_hash = Column(
        String(64),
        nullable=False,
        unique=True,
        index=True
    )

    expires_at = Column(
        DateTime,
        nullable=False
    )

    is_used = Column(
        Boolean,
        default=False,
        nullable=False
    )

    created_at = Column(
        DateTime,
        server_default=func.now()
    )
