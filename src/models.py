# src/models.py

from sqlalchemy import (
    Column, Integer, String, Text, ForeignKey, DateTime, func
)
from sqlalchemy.orm import relationship
from .db import Base

from datetime import datetime


class University(Base):
    __tablename__ = "universities"

    id = Column(Integer, primary_key=True)
    key = Column(String, unique=True, nullable=False)
    name = Column(String, unique=True, nullable=False)
    base_url = Column(String, nullable=False)
    city = Column(String, nullable=True)

    masters = relationship("MasterProgram", back_populates="university")
    events = relationship("Event", back_populates="university")


class MasterProgram(Base):
    __tablename__ = "masters"

    id = Column(Integer, primary_key=True)
    university_id = Column(Integer, ForeignKey("universities.id"), nullable=False)
    name = Column(String, nullable=False)
    official_url = Column(String, nullable=False, unique=True)
    summary = Column(Text, nullable=False)
    city = Column(String, nullable=True)

    last_fetched_at = Column(
        DateTime, server_default=func.now(), onupdate=func.now(), nullable=False
    )

    university = relationship("University", back_populates="masters")


class Event(Base):
    __tablename__ = "events"

    id = Column(Integer, primary_key=True)
    university_id = Column(Integer, ForeignKey("universities.id"), nullable=False)
    title = Column(String, nullable=False)
    url = Column(String, nullable=False)
    summary = Column(Text, nullable=False)
    city = Column(String, nullable=True)

    last_fetched_at = Column(
        DateTime, server_default=func.now(), onupdate=func.now(), nullable=False
    )

    university = relationship("University", back_populates="events")




class UserProfile(Base):
    __tablename__ = "user_profiles"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(String, unique=True, index=True, nullable=False)
    cv_text = Column(Text, nullable=False)
    quiz_scores_json = Column(Text, nullable=True)  # store quiz answers/scores as JSON string
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow)


class UniversityOverview(Base):
    __tablename__ = "university_overviews"

    id = Column(Integer, primary_key=True)
    university_id = Column(Integer, ForeignKey("universities.id"), index=True, nullable=False)
    source_url = Column(String, nullable=False)
    raw_text = Column(Text, nullable=False)
    summary = Column(Text, nullable=True)


class UniversityLife(Base):
    __tablename__ = "university_life"

    id = Column(Integer, primary_key=True)
    university_id = Column(Integer, ForeignKey("universities.id"), index=True, nullable=False)
    source_url = Column(String, nullable=False)
    raw_text = Column(Text, nullable=False)
    summary = Column(Text, nullable=True)