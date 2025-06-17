from typing import Dict, List, Optional, Any
import os
import logging
import json
from datetime import datetime
from pathlib import Path
import uuid
import re

from sqlalchemy.orm import Session
from sqlalchemy import func
from sqlalchemy.exc import SQLAlchemyError

from backend.db.models import (
    EmbeddingRun, 
    EmbeddingDocument, 
    EmbeddingChunk, 
    Employee,
    EmployeeCV,
    EmployeeAssessment
)
from backend.db.session import get_db
from .chunker import TextChunker
from .embedder import OpenAIEmbedder
from .chunking_registry import registry

logger = logging.getLogger(__name__)

class EmbeddingPipeline:
    """Orchestrates the document processing pipeline: chunk → embed → store."""
    
    def __init__(self, db: Session, embedding_model: str = "text-embedding-3-small"):
        """Initialize the embedding pipeline.
        
        Args:
            db: Database session
            embedding_model: OpenAI embedding model to use
        """
        self.db = db
        self.chunker = TextChunker()
        self.embedder = OpenAIEmbedder(model=embedding_model)
        # Register bound methods
        registry._methods["cv"] = self.chunker._chunk_cv
        registry._methods["assessment"] = self.chunker._chunk_assessment
        registry._methods["generic"] = self.chunker._chunk_generic
        logger.info(f"Initialized pipeline with model: {embedding_model}")
        
    def _check_document_exists(self, filename: str, employee_id: str) -> bool:
        """Check if document has already been processed.
        
        Args:
            filename: Name of the file
            employee_id: UUID of the employee
            
        Returns:
            True if document exists, False otherwise
        """
        existing = self.db.query(EmbeddingDocument).filter(
            EmbeddingDocument.source_filename == filename,
            EmbeddingDocument.employee_id == employee_id
        ).first()
        
        if existing:
            logger.info(f"Document {filename} already processed for employee {employee_id}")
            return True
        return False
        
    def _extract_metadata_from_filename(self, filename: str) -> Optional[Dict]:
        """Extract metadata from filename.
        
        Args:
            filename: Name of the file to extract metadata from
            
        Returns:
            Dict containing metadata or None if file should be skipped
        """
        metadata = {
            "employee_name": None,
            "doc_type": None,
            "assessment_type": None
        }
        
        # Skip .done files and hidden files
        if filename.endswith('.done') or filename.startswith('.'):
            logger.debug(f"Skipping file {filename}: done file or hidden file")
            return None
            
        # Extract name and type from filename patterns
        patterns = {
            r'IDI_([A-Za-z]+)_([A-Za-z\-]+)\.txt$': ('IDI', 'IDI'),
            r'Hogan_([A-Za-z]+)_([A-Za-z\-]+)\.txt$': ('Hogan', 'Hogan'),
            r'CV_([A-Za-z]+)_([A-Za-z\-]+)\.txt$': ('CV', None),
            r'CV_([A-Za-z]+)_([A-Za-z\-]+)\.json$': ('CV', None)
        }
        
        for pattern, (doc_type, assessment_type) in patterns.items():
            match = re.match(pattern, filename)
            if match:
                metadata["doc_type"] = doc_type
                metadata["assessment_type"] = assessment_type
                metadata["employee_name"] = f"{match.group(1)} {match.group(2)}"
                logger.info(f"Extracted metadata from {filename}: {metadata}")
                return metadata
                
        # Try to extract from JSON metadata if it's a JSON file
        if filename.endswith('.json'):
            try:
                with open(os.path.join('backend/data/processed', filename), 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    meta = data.get('metadata', {})
                    if 'employee_id' in meta:
                        metadata["employee_name"] = meta['employee_id']
                        metadata["doc_type"] = meta.get('doc_type', 'CV')
                        logger.info(f"Extracted metadata from JSON {filename}: {metadata}")
                        return metadata
            except Exception as e:
                logger.warning(f"Failed to parse JSON metadata for {filename}: {str(e)}")
                
        logger.warning(f"Could not extract metadata from filename: {filename}")
        return None
        
    def _get_or_create_employee(self, employee_name: str) -> Employee:
        """Get existing employee or create new one.
        
        Args:
            employee_name: Full name of the employee
            
        Returns:
            Employee object
            
        Raises:
            ValueError: If employee_name is None or empty
        """
        if not employee_name or not employee_name.strip():
            raise ValueError("Employee name cannot be empty")
            
        # Try to find employee by name (case-insensitive)
        employee = self.db.query(Employee).filter(
            func.lower(Employee.full_name) == func.lower(employee_name.strip())
        ).first()
        
        if not employee:
            # Create new employee
            employee = Employee(
                full_name=employee_name.strip(),
                created_at=datetime.utcnow(),
                updated_at=datetime.utcnow()
            )
            self.db.add(employee)
            self.db.flush()
            logger.info(f"Created new employee: {employee_name}")
            
        return employee
        
    def process_directory(self, input_dir: str) -> None:
        """Process all documents in a directory.
        
        Args:
            input_dir: Path to directory containing documents to process
        """
        input_path = Path(input_dir)
        if not input_path.exists():
            raise ValueError(f"Input directory does not exist: {input_dir}")
            
        logger.info(f"Processing directory: {input_dir}")
            
        # Create embedding run with registered chunking method
        chunking_method = "generic"  # Default method
        try:
            if registry.get_method("cv") and registry.get_method("assessment"):
                chunking_method = "cv"  # Use CV method if available
        except ValueError as e:
            logger.warning(f"Using default chunking method: {str(e)}")
            
        run = EmbeddingRun(
            name=f"Run_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}",
            chunking_method=chunking_method,
            embedding_model=self.embedder.model,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow()
        )
        self.db.add(run)
        self.db.flush()
        self.db.commit()
        logger.info(f"Created embedding run: {run.id}")
        
        # Process each file
        processed_count = 0
        skipped_count = 0
        error_count = 0
        
        for file_path in input_path.glob('*'):
            if file_path.is_file() and not file_path.name.endswith('.done'):
                try:
                    logger.info(f"Processing file: {file_path.name}")
                    
                    metadata = self._extract_metadata_from_filename(file_path.name)
                    if not metadata or not metadata["employee_name"]:
                        logger.warning(f"Skipping file {file_path.name}: could not extract employee name")
                        skipped_count += 1
                        continue
                        
                    employee = self._get_or_create_employee(metadata["employee_name"])
                    
                    # Check if already processed
                    if self._check_document_exists(file_path.name, employee.id):
                        logger.info(f"Skipping already processed file: {file_path.name}")
                        skipped_count += 1
                        continue
                        
                    self.process_document(
                        file_path=file_path,
                        employee_id=employee.id,
                        doc_type=metadata["doc_type"],
                        embedding_run_id=run.id
                    )
                    processed_count += 1
                    
                except Exception as e:
                    logger.error(f"Error processing file {file_path}: {str(e)}")
                    self.db.rollback()
                    error_count += 1
                    continue
                    
        self.db.commit()
        logger.info(f"Pipeline completed. Processed: {processed_count}, Skipped: {skipped_count}, Errors: {error_count}")
        
    def _generate_assessment_summary(self, file_path: Path, doc_type: str, employee_name: str) -> Optional[Path]:
        """Generate a summary for an assessment file if it doesn't exist.
        
        Args:
            file_path: Path to the assessment file
            doc_type: Type of assessment (IDI, Hogan)
            employee_name: Name of the employee
            
        Returns:
            Path to the summary file if created, None otherwise
        """
        summary_filename = f"{doc_type}Summary_{employee_name.replace(' ', '_')}.txt"
        summary_path = file_path.parent / summary_filename
        
        if summary_path.exists():
            logger.info(f"Summary already exists: {summary_path}")
            return summary_path
            
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
                
            # Generate summary based on assessment type
            if doc_type == "IDI":
                summary = self._generate_idi_summary(content)
            elif doc_type == "Hogan":
                summary = self._generate_hogan_summary(content)
            else:
                logger.warning(f"Unknown assessment type for summary: {doc_type}")
                return None
                
            # Write summary to file
            with open(summary_path, 'w', encoding='utf-8') as f:
                f.write(summary)
                
            logger.info(f"Generated summary: {summary_path}")
            return summary_path
            
        except Exception as e:
            logger.error(f"Error generating summary for {file_path}: {str(e)}")
            return None
            
    def _generate_idi_summary(self, content: str) -> str:
        """Generate a summary for an IDI assessment.
        
        Args:
            content: Raw content of the IDI assessment
            
        Returns:
            Summary text
        """
        # Extract key sections and scores
        sections = []
        current_section = []
        
        for line in content.split('\n'):
            if line.strip().startswith('Section') or line.strip().startswith('Dimension'):
                if current_section:
                    sections.append('\n'.join(current_section))
                current_section = [line]
            else:
                current_section.append(line)
                
        if current_section:
            sections.append('\n'.join(current_section))
            
        # Format summary
        summary = "IDI Assessment Summary\n"
        summary += "=" * 50 + "\n\n"
        
        for section in sections:
            summary += section + "\n\n"
            
        return summary
        
    def _generate_hogan_summary(self, content: str) -> str:
        """Generate a summary for a Hogan assessment.
        
        Args:
            content: Raw content of the Hogan assessment
            
        Returns:
            Summary text
        """
        # Extract key sections and scores
        sections = []
        current_section = []
        
        for line in content.split('\n'):
            if line.strip().startswith('Scale') or line.strip().startswith('Trait'):
                if current_section:
                    sections.append('\n'.join(current_section))
                current_section = [line]
            else:
                current_section.append(line)
                
        if current_section:
            sections.append('\n'.join(current_section))
            
        # Format summary
        summary = "Hogan Assessment Summary\n"
        summary += "=" * 50 + "\n\n"
        
        for section in sections:
            summary += section + "\n\n"
            
        return summary

    def _map_document_type(self, doc_type: str) -> str:
        """Map document type to allowed database values.
        
        Args:
            doc_type: Original document type from filename
            
        Returns:
            Mapped document type that matches database constraints
        """
        mapping = {
            'CV': 'cv',
            'IDI': 'assessment',
            'Hogan': 'assessment',
            'IDISummary': 'summary',
            'HoganSummary': 'summary'
        }
        return mapping.get(doc_type, 'other')
        
    def _get_external_document_id(self, filename: str, employee_id: str, doc_type: str) -> Optional[str]:
        """Get the external document ID based on document type.
        
        Args:
            filename: Name of the file
            employee_id: UUID of the employee
            doc_type: Type of document (cv, assessment)
            
        Returns:
            UUID of the external document or None if not found
        """
        if doc_type == "CV":
            cv = self.db.query(EmployeeCV).filter(
                EmployeeCV.employee_id == employee_id,
                EmployeeCV.filename == filename
            ).first()
            return cv.id if cv else None
        elif doc_type in ["IDI", "Hogan"]:
            assessment = self.db.query(EmployeeAssessment).filter(
                EmployeeAssessment.employee_id == employee_id,
                EmployeeAssessment.source_filename == filename
            ).first()
            return assessment.id if assessment else None
        return None

    def process_document(self, file_path: Path, employee_id: str, doc_type: str, embedding_run_id: str) -> None:
        """Process a single document: chunk → embed → store.
        
        Args:
            file_path: Path to the document
            employee_id: UUID of the employee
            doc_type: Type of document (CV, IDI, Hogan)
            embedding_run_id: UUID of the embedding run
        """
        try:
            # Get external document ID
            external_document_id = self._get_external_document_id(file_path.name, employee_id, doc_type)
            if not external_document_id:
                logger.error(f"Could not find external document ID for {file_path.name}")
                return

            # Map document type to allowed DB value
            mapped_doc_type = self._map_document_type(doc_type)
            logger.info(f"Processing document {file_path.name} as type {mapped_doc_type}")

            # Create embedding document
            doc = EmbeddingDocument(
                employee_id=employee_id,
                embedding_run_id=embedding_run_id,
                document_type=mapped_doc_type,
                source_filename=file_path.name,
                external_document_id=external_document_id,
                source_type=mapped_doc_type,
                created_at=datetime.utcnow(),
                updated_at=datetime.utcnow()
            )
            self.db.add(doc)
            self.db.flush()
            logger.info(f"Created embedding document with ID: {doc.id}")

            # Read and chunk content
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            logger.info(f"Read {len(content)} characters from {file_path.name}")

            # Get appropriate chunking method
            chunking_method = registry.get_method(mapped_doc_type)
            if not chunking_method:
                chunking_method = registry.get_method("generic")
                logger.warning(f"No specific chunking method found for {mapped_doc_type}, using generic")

            # For CVs, chunker may require 'text' argument
            import inspect
            if mapped_doc_type == "cv" and 'text' in inspect.signature(chunking_method).parameters:
                chunks = chunking_method(text=content)
            else:
                chunks = chunking_method(content)
            # Wrap string chunks as dicts if needed
            if chunks and isinstance(chunks[0], str):
                chunks = [{"content": c} for c in chunks]
            logger.info(f"Generated {len(chunks)} chunks for {file_path.name}")

            # Process each chunk
            chunk_count = 0
            for i, chunk in enumerate(chunks):
                try:
                    # Generate embedding
                    embedding = self.embedder.embed(chunk["content"])
                    
                    # Create chunk record
                    chunk_record = EmbeddingChunk(
                        external_document_id=external_document_id,
                        chunk_index=i,
                        content=chunk["content"],
                        embedding=embedding,
                        token_count=chunk.get("token_count"),
                        char_count=chunk.get("char_count"),
                        chunk_label=chunk.get("label")
                    )
                    self.db.add(chunk_record)
                    chunk_count += 1
                except Exception as e:
                    logger.error(f"Error processing chunk {i} for {file_path.name}: {str(e)}")
                    continue

            self.db.commit()
            logger.info(f"Successfully processed {file_path.name}: created {chunk_count} chunks")

        except Exception as e:
            self.db.rollback()
            logger.error(f"Error processing document {file_path}: {str(e)}")
            raise 