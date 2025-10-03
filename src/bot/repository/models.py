"""Database models for the Olympiad bot."""

from __future__ import annotations

import enum
from datetime import date, datetime

from sqlalchemy import BigInteger, Boolean, Date, DateTime, Enum, ForeignKey, Integer, String, Text
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship
from sqlalchemy.sql import func


class Base(DeclarativeBase):
    """Base class for declarative SQLAlchemy models."""


class ReminderKind(str, enum.Enum):
    """Reminder event kinds supported by the bot."""

    REG_WEEK = "reg_week"
    DAY_BEFORE = "day_before"
    DAY_OF = "day_of"


class User(Base):
    """Telegram bot user."""

    __tablename__ = "users"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    tg_id: Mapped[int] = mapped_column(BigInteger, unique=True)
    username: Mapped[str | None] = mapped_column(String(255), nullable=True)
    is_subscribed: Mapped[bool] = mapped_column(
        Boolean, nullable=False, server_default="false", default=False
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now(), default=func.now
    )

    olympiads: Mapped[list["UserOlympiad"]] = relationship(back_populates="user")
    reminders: Mapped[list["Reminder"]] = relationship(back_populates="user")
    payments: Mapped[list["PaymentStub"]] = relationship(back_populates="user")


class Olympiad(Base):
    """Olympiad catalog entry."""

    __tablename__ = "olympiads"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    subject: Mapped[str] = mapped_column(String(100), nullable=False)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    reg_deadline: Mapped[date | None] = mapped_column(Date, nullable=True)
    round_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)

    participants: Mapped[list["UserOlympiad"]] = relationship(back_populates="olympiad")
    materials: Mapped[list["Material"]] = relationship(back_populates="olympiad")
    reminders: Mapped[list["Reminder"]] = relationship(back_populates="olympiad")
    universities: Mapped[list["OlympiadUniversity"]] = relationship(back_populates="olympiad")


class UserOlympiad(Base):
    """Association between users and olympiads."""

    __tablename__ = "user_olympiads"

    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), primary_key=True
    )
    olympiad_id: Mapped[int] = mapped_column(
        ForeignKey("olympiads.id", ondelete="CASCADE"), primary_key=True
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now(), default=func.now
    )

    user: Mapped[User] = relationship(back_populates="olympiads")
    olympiad: Mapped[Olympiad] = relationship(back_populates="participants")


class Material(Base):
    """Learning materials linked to an olympiad."""

    __tablename__ = "materials"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    olympiad_id: Mapped[int] = mapped_column(
        ForeignKey("olympiads.id", ondelete="CASCADE"), nullable=False, index=True
    )
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    url: Mapped[str] = mapped_column(String(1024), nullable=False)
    added_by_admin_id: Mapped[int | None] = mapped_column(BigInteger, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now(), default=func.now
    )

    olympiad: Mapped[Olympiad] = relationship(back_populates="materials")


class Reminder(Base):
    """Scheduled reminder for an olympiad event."""

    __tablename__ = "reminders"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )
    olympiad_id: Mapped[int] = mapped_column(
        ForeignKey("olympiads.id", ondelete="CASCADE"), nullable=False, index=True
    )
    kind: Mapped[ReminderKind] = mapped_column(
        Enum(ReminderKind, name="reminder_kind"), nullable=False
    )
    scheduled_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    sent_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    user: Mapped[User] = relationship(back_populates="reminders")
    olympiad: Mapped[Olympiad] = relationship(back_populates="reminders")


class University(Base):
    """University participating in olympiad benefits."""

    __tablename__ = "universities"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False, unique=True)

    olympiads: Mapped[list["OlympiadUniversity"]] = relationship(back_populates="university")


class OlympiadUniversity(Base):
    """Association between olympiads and universities."""

    __tablename__ = "olympiad_university"

    olympiad_id: Mapped[int] = mapped_column(
        ForeignKey("olympiads.id", ondelete="CASCADE"), primary_key=True
    )
    university_id: Mapped[int] = mapped_column(
        ForeignKey("universities.id", ondelete="CASCADE"), primary_key=True
    )

    olympiad: Mapped[Olympiad] = relationship(back_populates="universities")
    university: Mapped[University] = relationship(back_populates="olympiads")


class PaymentStub(Base):
    """Stub table for payment records."""

    __tablename__ = "payments_stub"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )
    status: Mapped[str] = mapped_column(String(50), nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now(), default=func.now
    )

    user: Mapped[User] = relationship(back_populates="payments")


__all__ = (
    "Base",
    "Material",
    "Olympiad",
    "OlympiadUniversity",
    "PaymentStub",
    "Reminder",
    "ReminderKind",
    "University",
    "User",
    "UserOlympiad",
)
