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
    created_at = Column(DateTime, default=datetime.now(timezone.utc))

    watchlist = relationship("WatchlistItem", back_populates="user")


# Internships obtained from scraping JSON
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


# Watchlist table for companies users want to track
class WatchlistItem(Base):
    __tablename__ = "watchlist_items"
    __table_args__ = (
        UniqueConstraint(
            "user_id", "company_name", name="uix_user_company"
        ),  # Database side checks to ensure user doesn't add a company more than once.
    )

    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    company_name = Column(String, nullable=False)
    added_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

    user = relationship("User", back_populates="watchlist")
