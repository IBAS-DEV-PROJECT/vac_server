from sqlalchemy import ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.common.constants import ConcernStatus
from app.db.base import Base, TimestampMixin, UUIDMixin


class Concern(UUIDMixin, TimestampMixin, Base):
    __tablename__ = "concerns"

    user_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    concern: Mapped[str] = mapped_column(String(255), nullable=False)
    topic: Mapped[str] = mapped_column(String(20), nullable=False, index=True)
    # topic이 "기타"일 때 사용자가 직접 입력한 주제명 (그 외 주제에서는 NULL)
    topic_other: Mapped[str | None] = mapped_column(String(50), nullable=True)
    status: Mapped[str] = mapped_column(
        String(20), default=ConcernStatus.PENDING, nullable=False, index=True
    )

    records: Mapped[list["Record"]] = relationship(
        back_populates="concern", cascade="all, delete-orphan", passive_deletes=True
    )


class Record(UUIDMixin, TimestampMixin, Base):
    __tablename__ = "records"

    concern_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("concerns.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    user_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    decision: Mapped[str] = mapped_column(String(255), nullable=False)
    reason: Mapped[str] = mapped_column(Text, nullable=False)
    value: Mapped[str] = mapped_column(String(20), nullable=False, index=True)

    concern: Mapped["Concern"] = relationship(back_populates="records")
