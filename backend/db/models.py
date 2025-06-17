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
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

class EmployeeCV(Base, TimestampMixin):
    """Model for employee CV documents."""
    __tablename__ = 'employee_cvs'

    id = Column(PG_UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    employee_id = Column(PG_UUID(as_uuid=True), ForeignKey('employees.id', ondelete='CASCADE'), nullable=False)
    filename = Column(Text, nullable=False)
    upload_date = Column(DateTime(timezone=True), server_default=func.now())
    source = Column(Text)

    # Relationships
    employee = relationship("Employee", back_populates="cvs")

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
    cvs = relationship("EmployeeCV", back_populates="employee", cascade="all, delete-orphan")
    embedding_documents = relationship("EmbeddingDocument", back_populates="employee", cascade="all, delete-orphan")

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

class EmbeddingRun(Base, TimestampMixin):
    """Model for tracking embedding generation runs."""
    __tablename__ = 'embedding_runs'

    id = Column(PG_UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(Text, nullable=False)
    chunking_method = Column(Text, nullable=False)
    embedding_model = Column(Text, nullable=False)

    # Relationships
    documents = relationship("EmbeddingDocument", back_populates="embedding_run", cascade="all, delete-orphan")

class EmbeddingDocument(Base):
    __tablename__ = "embedding_documents"
    id = Column(PG_UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    employee_id = Column(PG_UUID(as_uuid=True), ForeignKey("employees.id"), nullable=False)
    embedding_run_id = Column(PG_UUID(as_uuid=True), ForeignKey("embedding_runs.id"), nullable=False)
    document_type = Column(Text, nullable=False)
    source_filename = Column(Text, nullable=False)
    title = Column(Text)
    external_document_id = Column(PG_UUID(as_uuid=True), nullable=False, unique=True)  # Links to employee_cvs.id or employee_assessments.id
    parsed_source_id = Column(PG_UUID(as_uuid=True))  # For tracking the parsed source
    source_type = Column(Text)  # Type of the source document
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # Add unique constraint for source_filename and embedding_run_id
    __table_args__ = (
        UniqueConstraint('source_filename', 'embedding_run_id', name='uix_source_run'),
    )

    # Relationships
    employee = relationship("Employee", back_populates="embedding_documents")
    embedding_run = relationship("EmbeddingRun", back_populates="documents")
    chunks = relationship("EmbeddingChunk", back_populates="document", cascade="all, delete-orphan")

class EmbeddingChunk(Base, TimestampMixin):
    """Model for storing document chunks and their embeddings."""
    __tablename__ = 'embedding_chunks'

    id = Column(PG_UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    external_document_id = Column(PG_UUID(as_uuid=True), ForeignKey('embedding_documents.external_document_id', ondelete='CASCADE'), nullable=False)
    chunk_index = Column(Integer, nullable=False)
    content = Column(Text, nullable=False)
    embedding = Column(Vector(1536), nullable=False)
    token_count = Column(Integer, nullable=True)
    char_count = Column(Integer, nullable=True)
    chunk_label = Column(Text, nullable=True)
    
    # Relationships
    document = relationship("EmbeddingDocument", back_populates="chunks", foreign_keys=[external_document_id])