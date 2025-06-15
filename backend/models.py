from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Text
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from datetime import datetime

Base = declarative_base()

class Talent(Base):
    __tablename__ = 'talents'

    id = Column(Integer, primary_key=True)
    name = Column(String(255), nullable=False)
    email = Column(String(255), unique=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

class Resume(Base):
    __tablename__ = 'resumes'

    id = Column(Integer, primary_key=True)
    talent_id = Column(Integer, ForeignKey('talents.id'))
    content = Column(Text)
    parsed_data = Column(Text)  # JSON field for parsed resume data
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationship
    talent = relationship("Talent", back_populates="resumes")

# Add the relationship to the Talent class
Talent.resumes = relationship("Resume", back_populates="talent") 