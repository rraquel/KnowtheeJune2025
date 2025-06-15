from datetime import datetime
from sqlalchemy import Column, Integer, String, Float, ForeignKey, DateTime, Text, Enum, UniqueConstraint, Boolean, Date, func
from sqlalchemy.orm import relationship, declarative_base
from sqlalchemy.ext.declarative import declared_attr
import uuid
from sqlalchemy import (
    Column, String, Integer, Date, Text, JSON, TIMESTAMP, ForeignKey, Float
)
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import relationship, declarative_base
from pgvector.sqlalchemy import Vector

Base = declarative_base()

class TimestampMixin:
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

class Employee(Base, TimestampMixin):
    """Model for employee personal information."""
    __tablename__ = 'employees'

    id = Column(PG_UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    full_name = Column(String(200), nullable=False)
    email = Column(String(200))
    location = Column(String(100))
    current_position = Column(String(100))
    department = Column(String(100))
    
    # Relationships
    contacts = relationship("EmployeeContact", back_populates="employee", cascade="all, delete-orphan")
    education = relationship("EmployeeEducation", back_populates="employee", cascade="all, delete-orphan")
    experiences = relationship("EmployeeExperience", back_populates="employee", cascade="all, delete-orphan")
    skills = relationship("EmployeeSkill", back_populates="employee", cascade="all, delete-orphan")
    assessments = relationship("EmployeeAssessment", back_populates="employee", cascade="all, delete-orphan")
    embeddings = relationship('DocumentEmbedding', back_populates='employee', cascade='all, delete-orphan')

class EmployeeContact(Base, TimestampMixin):
    """Model for employee contact information."""
    __tablename__ = 'employee_contacts'

    id = Column(PG_UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    employee_id = Column(PG_UUID(as_uuid=True), ForeignKey('employees.id', ondelete='CASCADE'), nullable=False)
    type = Column(String(20), nullable=False)
    value = Column(Text, nullable=False)
    is_primary = Column(Boolean, default=False)

    # Relationship
    employee = relationship("Employee", back_populates="contacts")

class EmployeeEducation(Base, TimestampMixin):
    """Model for employee education history."""
    __tablename__ = 'employee_education'

    id = Column(PG_UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    employee_id = Column(PG_UUID(as_uuid=True), ForeignKey('employees.id', ondelete='CASCADE'), nullable=False)
    institution = Column(String(255), nullable=False)
    degree = Column(String(255))
    field = Column(String(255))
    start_date = Column(Date)
    end_date = Column(Date)
    
    # Relationship
    employee = relationship("Employee", back_populates="education")

class EmployeeExperience(Base, TimestampMixin):
    """Model for employee work experience."""
    __tablename__ = 'employee_experiences'

    id = Column(PG_UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    employee_id = Column(PG_UUID(as_uuid=True), ForeignKey('employees.id', ondelete='CASCADE'), nullable=False)
    company = Column(String(255), nullable=False)
    title = Column(String(255), nullable=False)
    start_date = Column(Date)
    end_date = Column(Date)
    description = Column(Text)
    
    # Relationship
    employee = relationship("Employee", back_populates="experiences")

class EmployeeSkill(Base, TimestampMixin):
    """Model for employee skills."""
    __tablename__ = 'employee_skills'

    id = Column(PG_UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    employee_id = Column(PG_UUID(as_uuid=True), ForeignKey('employees.id', ondelete='CASCADE'), nullable=False)
    skill = Column(String(255), nullable=False)
    type = Column(String(50), nullable=False, default='technical')  # technical, soft, language, etc.
    
    # Relationship
    employee = relationship("Employee", back_populates="skills")

class EmployeeAssessment(Base, TimestampMixin):
    """Model for employee assessment records."""
    __tablename__ = 'employee_assessments'

    id = Column(PG_UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    employee_id = Column(PG_UUID(as_uuid=True), ForeignKey('employees.id', ondelete='CASCADE'), nullable=False)
    assessment_type = Column(String(50), nullable=False)  # IDI, HPI, HDS, MVPI
    assessment_date = Column(Date, nullable=False)
    source_filename = Column(String(255), nullable=False)
    status = Column(String(20), default='active')
    notes = Column(Text)
    
    # Relationships
    employee = relationship("Employee", back_populates="assessments")
    idi_scores = relationship("IDIScore", back_populates="assessment", cascade="all, delete-orphan")
    hogan_scores = relationship("HoganScore", back_populates="assessment", cascade="all, delete-orphan")

class IDIScore(Base, TimestampMixin):
    """Model for IDI assessment scores."""
    __tablename__ = 'idi_scores'

    id = Column(PG_UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    assessment_id = Column(PG_UUID(as_uuid=True), ForeignKey('employee_assessments.id', ondelete='CASCADE'), nullable=False)
    category = Column(String(50), nullable=False)
    dimension = Column(String(50), nullable=False)
    score = Column(Float, nullable=False)
    
    # Relationship
    assessment = relationship("EmployeeAssessment", back_populates="idi_scores")

class HoganScore(Base, TimestampMixin):
    """Model for Hogan assessment scores."""
    __tablename__ = 'hogan_scores'

    id = Column(PG_UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    assessment_id = Column(PG_UUID(as_uuid=True), ForeignKey('employee_assessments.id', ondelete='CASCADE'), nullable=False)
    trait = Column(String(50), nullable=False)
    score = Column(Float, nullable=False)
    
    # Relationship
    assessment = relationship("EmployeeAssessment", back_populates="hogan_scores")

class DocumentEmbedding(Base, TimestampMixin):
    """Model for storing document embeddings."""
    __tablename__ = 'document_embeddings'

    id = Column(PG_UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    employee_id = Column(PG_UUID(as_uuid=True), ForeignKey('employees.id', ondelete='CASCADE'), nullable=False)
    source = Column(String(50), nullable=False)  # e.g. 'CV', 'Assessment'
    embedding = Column(Vector(1536), nullable=False)  # pgvector type
    
    # Relationships
    employee = relationship('Employee', back_populates='embeddings')