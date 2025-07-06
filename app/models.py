from sqlalchemy import Column, Integer, String, Boolean, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from datetime import datetime, timezone
from app.db import Base


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True)
    username = Column(String, nullable=False, unique=True)
    email = Column(String, nullable=False, unique=True)
    password_hash = Column(String, nullable=False)  # storing hashed passwords only
    created_at = Column(DateTime, default=datetime.now(timezone.utc))

    # relationship to link users with their watchlist items
    watchlist = relationship("WatchlistItem", back_populates="user")


class Internship(Base):
    __tablename__ = "internships"

    id = Column(String, primary_key=True)  # using UUID from the JSON data
    company = Column(String, nullable=False)
    role = Column(String, nullable=False)  # changed from title to role
    location = Column(String)  # JSON has location as list but we'll store as string
    remote = Column(Boolean, default=False)  # can figure this out from location later
    link = Column(String)  # this comes from "url" field in JSON
    date_posted = Column(String)  # keeping as string for now, might change later
    source = Column(String)  # from JSON source field
    is_visible = Column(Boolean)
    active = Column(Boolean)
    season = Column(String)


#Watchlist table for companies users want to track
class WatchlistItem(Base):
    __tablename__ = "watchlist_items"
    
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    company_name = Column(String, nullable=False)
    added_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))  # when they added it

    # connects back to the user who added this item
    user = relationship("User", back_populates="watchlist")
