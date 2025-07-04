from sqlalchemy import Column, Integer, String, Boolean, DateTime, ForeignKey
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


#     watchlist = relationship("WatchlistItem", back_populates="user")


class Internship(Base):
    __tablename__ = "internships"

    id = Column(String, primary_key=True)  # UUID from JSON
    company = Column(String, nullable=False)
    role = Column(String, nullable=False)  # rename from title → role
    location = Column(String)  # JSON has a list — join into string
    remote = Column(
        Boolean, default=False
    )  # You can infer this from location if needed
    link = Column(String)  # from "url"
    date_posted = Column(String)  # keep as string for now
    source = Column(String)  # from JSON
    is_visible = Column(Boolean)
    active = Column(Boolean)
    season = Column(String)


#     watchlisted_by = relationship("WatchlistItem", back_populates="internship")


# class WatchlistItem(Base):
#     __tablename__ = "watchlist_items"
#     id = Column(Integer, primary_key=True)
#     user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
#     internship_id = Column(Integer, ForeignKey("internships.id"), nullable=False)
#     added_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

#     user = relationship("User", back_populates="watchlist")
#     internship = relationship("Internship", back_populates="watchlisted_by")
