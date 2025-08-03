from sqlalchemy import (
    Column,
    Integer,
    String,
    Boolean,
    DateTime,
    ForeignKey,
    UniqueConstraint,
)
from sqlalchemy.orm import relationship
from datetime import datetime, timezone
from app.db import Base


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True)
    username = Column(String, nullable=False, unique=True)
    email = Column(String, nullable=False, unique=True)
    password_hash = Column(String, nullable=False)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    points = Column(Integer, default=0)

    # relationships
    watchlist = relationship(
        "WatchlistItem", back_populates="user", cascade="all, delete-orphan"
    )
    application_logs = relationship(
        "ApplicationLog", back_populates="user", cascade="all, delete-orphan"
    )
    checkins = relationship(
        "CheckIn", back_populates="user", cascade="all, delete-orphan"
    )
    reminders = relationship(
        "Reminder", back_populates="user", cascade="all, delete-orphan"
    )
    badges = relationship("Badge", back_populates="user", cascade="all, delete-orphan")


class Internship(Base):
    __tablename__ = "internships"
    id = Column(String, primary_key=True)
    company = Column(String, nullable=False)
    role = Column(String, nullable=False)
    location = Column(String)
    remote = Column(Boolean, default=False)
    link = Column(String)
    date_posted = Column(String)
    source = Column(String)
    is_visible = Column(Boolean)
    active = Column(Boolean)
    season = Column(String)


class WatchlistItem(Base):
    __tablename__ = "watchlist_items"
    __table_args__ = (
        UniqueConstraint("user_id", "company_name", name="uix_user_company"),
    )

    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    company_name = Column(String, nullable=False)
    added_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

    user = relationship("User", back_populates="watchlist")


class ApplicationLog(Base):
    __tablename__ = "application_logs"

    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    company = Column(String, nullable=False)
    role = Column(String, nullable=False)
    status = Column(String, nullable=False)
    date_applied = Column(DateTime, default=lambda: datetime.now(timezone.utc))

    user = relationship("User", back_populates="application_logs")


class CheckIn(Base):
    __tablename__ = "checkins"

    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    note = Column(String, nullable=True)
    date = Column(DateTime, default=lambda: datetime.now(timezone.utc))

    user = relationship("User", back_populates="checkins")


class Reminder(Base):
    __tablename__ = "reminders"

    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    text = Column(String, nullable=False)
    due_date = Column(DateTime, nullable=False)
    company = Column(String, nullable=False)
    role = Column(String, nullable=False)

    user = relationship("User", back_populates="reminders")


class Badge(Base):
    __tablename__ = "badges"

    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    badge_name = Column(String, nullable=False)
    badge_description = Column(String, nullable=False)
    points_required = Column(Integer, nullable=False)
    earned_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

    user = relationship("User", back_populates="badges")
