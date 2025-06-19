"""
PostgreSQL pgvector-based vector store
Production-ready vector storage and retrieval using PostgreSQL + pgvector
"""
import os
import traceback
from dotenv import load_dotenv

# Load environment variables at the very top
load_dotenv()

import json
import logging
from typing import List, Dict, Any, Optional
from sqlalchemy.orm import sessionmaker
from sqlalchemy import func, text, and_, or_
from pgvector.sqlalchemy import Vector
import openai

from backend.db.session import engine, SessionLocal
from backend.db.models import (
    EmbeddingDocument,
    EmbeddingChunk,
    Base
)

logger = logging.getLogger(__name__)

class VectorStore:
    """
    PostgreSQL + pgvector based vector store
    Production-ready vector storage and semantic search capabilities
    """
    
    # Default tenant for single-tenant setup
    DEFAULT_TENANT_ID = "default_tenant"
    
    def __init__(self):
        """Initialize PostgreSQL + pgvector vector store"""
        try:
            print("🔧 Initializing PostgreSQL + pgvector VectorStore...")
            
            # Initialize OpenAI client for embeddings
            openai_api_key = os.getenv('OPENAI_API_KEY')
            if not openai_api_key:
                logger.warning(f"❌ OPENAI_API_KEY not set in {__file__}")
                print("Stack trace:")
                traceback.print_stack()
                print(f"Current working directory: {os.getcwd()}")
                print(f"Environment variables containing 'OPENAI': {[k for k in os.environ.keys() if 'OPENAI' in k.upper()]}")
                self.openai_client = None
            else:
                self.openai_client = openai.OpenAI(api_key=openai_api_key)
                print(f"✅ OpenAI client initialized successfully from {__file__}")
            
            # Test database connection and pgvector
            self._test_connection()
            
            # Create tables if they don't exist
            self._ensure_tables_exist()
            
            print("✅ PostgreSQL + pgvector VectorStore initialized successfully")
            
        except Exception as e:
            logger.error(f"Failed to initialize VectorStore: {e}")
            raise Exception(f"VectorStore initialization failed: {e}")
    
    def _test_connection(self):
        """Test PostgreSQL connection and pgvector extension"""
        try:
            with SessionLocal() as session:
                # Test basic connection
                session.execute(text("SELECT 1"))
                
                # Test pgvector extension
                result = session.execute(text("SELECT * FROM pg_extension WHERE extname = 'vector'"))
                if not result.fetchone():
                    logger.error("pgvector extension not installed!")
                    raise Exception("pgvector extension required but not found")
                
                logger.info("✅ PostgreSQL and pgvector extension available")
                
        except Exception as e:
            logger.error(f"Database connection test failed: {e}")
            raise Exception(f"PostgreSQL with pgvector is required. Please ensure Docker is running with: docker-compose up -d")
    
    def _ensure_tables_exist(self):
        """Ensure vector tables exist"""
        try:
            from backend.db.models import Base
            Base.metadata.create_all(bind=engine)
            logger.info("✅ Vector tables created/verified")
        except Exception as e:
            logger.error(f"Failed to create tables: {e}")
            raise
    
    def _generate_embedding(self, text: str) -> List[float]:
        """Generate embedding using OpenAI API"""
        if not self.openai_client:
            logger.warning("OpenAI client not available - returning zero vector")
            return [0.0] * 1536
        
        try:
            response = self.openai_client.embeddings.create(
                model="text-embedding-ada-002",
                input=text
            )
            return response.data[0].embedding
        except Exception as e:
            logger.error(f"Failed to generate embedding: {e}")
            return [0.0] * 1536
    
    # =============================================================================
    # LEADERSHIP DOCUMENTS METHODS (single profile collection)
    # =============================================================================
    
    def store_documents(self, documents: List[str], metadata_list: List[dict] = None):
        """Store documents in the leadership documents vector database."""
        try:
            with SessionLocal() as session:
                # Clear existing documents
                session.query(EmbeddingDocument).delete()
                
                # Store new documents
                for i, document in enumerate(documents):
                    embedding = self._generate_embedding(document)
                    metadata = metadata_list[i] if metadata_list and i < len(metadata_list) else {}
                    
                    doc = EmbeddingDocument(
                        document_id=str(i),
                        content=document,
                        embedding=embedding,
                        doc_metadata=metadata,
                        tenant_id=self.DEFAULT_TENANT_ID
                    )
                    session.add(doc)
                
                session.commit()
                logger.info(f"Stored {len(documents)} leadership documents")
                
        except Exception as e:
            logger.error(f"Failed to store documents: {e}")
            raise
    
    def clear(self):
        """Clear all documents from the leadership documents vector store."""
        try:
            with SessionLocal() as session:
                session.query(EmbeddingDocument).delete()
                session.commit()
                logger.info("Cleared all leadership documents")
        except Exception as e:
            logger.error(f"Failed to clear documents: {e}")
            raise
    
    # =============================================================================
    # EMPLOYEE PROFILE METHODS
    # =============================================================================
    
    def store_employee_profile(self, employee_id: str, profile_sections: List[Dict[str, Any]], 
                              metadata: Dict[str, Any] = None):
        """
        Store an employee's profile sections as separate chunks with metadata.
        
        Args:
            employee_id: Unique identifier for the employee
            profile_sections: List of profile section dictionaries
            metadata: Additional metadata about the employee
        """
        try:
            with SessionLocal() as session:
                # Delete existing entries for this employee
                session.query(EmbeddingChunk).join(EmbeddingDocument).filter(
                    EmbeddingDocument.employee_id == employee_id
                ).delete(synchronize_session=False)
                
                # Store each section as a separate chunk
                for i, section in enumerate(profile_sections):
                    # Convert section to JSON string if it's not already
                    if isinstance(section, dict):
                        section_text = json.dumps(section)
                    else:
                        section_text = section
                    
                    # Generate embedding
                    embedding = self._generate_embedding(section_text)
                    
                    # Create metadata for this section
                    section_metadata = {
                        "employee_id": employee_id,
                        "section_id": i
                    }
                    
                    # Add employee metadata if provided
                    if metadata:
                        for key, value in metadata.items():
                            # Handle list values by concatenating them
                            if isinstance(value, list):
                                section_metadata[key] = ", ".join(str(item) for item in value)
                            else:
                                section_metadata[key] = str(value)
                    
                    # Create embedding document first
                    doc = EmbeddingDocument(
                        employee_id=employee_id,
                        embedding_run_id=employee_id,  # Use employee_id as run_id for profiles
                        document_type="profile",
                        source_filename=f"profile_{employee_id}_{i}",
                        external_document_id=employee_id,
                        source_type="profile"
                    )
                    session.add(doc)
                    session.flush()
                    
                    # Create chunk
                    chunk = EmbeddingChunk(
                        external_document_id=doc.external_document_id,
                        chunk_index=i,
                        content=section_text,
                        embedding=embedding,
                        token_count=len(section_text.split()),
                        char_count=len(section_text),
                        chunk_label=f"profile_section_{i}"
                    )
                    session.add(chunk)
                
                session.commit()
                logger.info(f"Stored profile for employee {employee_id} with {len(profile_sections)} sections")
                
        except Exception as e:
            logger.error(f"Failed to store employee profile {employee_id}: {e}")
            raise
    
    def store_employee_documents(self, employee_id: str, documents: List[str], 
                                metadata: Dict[str, Any] = None):
        """
        Store an employee's raw document chunks for detailed citations.
        
        Args:
            employee_id: Unique identifier for the employee
            documents: List of raw document chunks
            metadata: Additional metadata about the employee
        """
        try:
            with SessionLocal() as session:
                # Delete existing document entries for this employee
                session.query(EmbeddingChunk).join(EmbeddingDocument).filter(
                    EmbeddingDocument.employee_id == employee_id
                ).delete(synchronize_session=False)
                
                if not documents:
                    session.commit()
                    return
                
                # Store each document chunk
                for i, doc_content in enumerate(documents):
                    embedding = self._generate_embedding(doc_content)
                    
                    # Create embedding document
                    doc = EmbeddingDocument(
                        employee_id=employee_id,
                        embedding_run_id=employee_id,  # Use employee_id as run_id for documents
                        document_type="document",
                        source_filename=f"document_{employee_id}_{i}",
                        external_document_id=employee_id,
                        source_type="document"
                    )
                    session.add(doc)
                    session.flush()
                    
                    # Create chunk
                    chunk = EmbeddingChunk(
                        external_document_id=doc.external_document_id,
                        chunk_index=i,
                        content=doc_content,
                        embedding=embedding,
                        token_count=len(doc_content.split()),
                        char_count=len(doc_content),
                        chunk_label=f"document_chunk_{i}"
                    )
                    session.add(chunk)
                
                session.commit()
                logger.info(f"Stored {len(documents)} document chunks for employee {employee_id}")
                
        except Exception as e:
            logger.error(f"Failed to store employee documents {employee_id}: {e}")
            raise
    
    def delete_employee_profile(self, employee_id: str):
        """Delete all vector entries for an employee."""
        try:
            with SessionLocal() as session:
                # Delete from profiles and documents
                session.query(EmbeddingChunk).join(EmbeddingDocument).filter(
                    EmbeddingDocument.employee_id == employee_id
                ).delete(synchronize_session=False)
                
                # Delete embedding documents
                session.query(EmbeddingDocument).filter(
                    EmbeddingDocument.employee_id == employee_id
                ).delete()
                
                session.commit()
                logger.info(f"Deleted all vector data for employee {employee_id}")
                
        except Exception as e:
            logger.error(f"Failed to delete employee profile {employee_id}: {e}")
            raise
    
    def batch_store_employee_profiles(self, employee_data_list: List[Dict[str, Any]]):
        """
        Store multiple employee profiles in batch for better performance.
        
        Args:
            employee_data_list: List of dictionaries containing employee data
                Each dict should have: id, profile, metadata
        """
        if not employee_data_list:
            return
        
        try:
            with SessionLocal() as session:
                # Get all employee IDs to delete existing data
                employee_ids = [data.get('id') for data in employee_data_list if data.get('id')]
                
                # Delete existing entries for all employees
                session.query(EmbeddingChunk).join(EmbeddingDocument).filter(
                    EmbeddingDocument.employee_id.in_(employee_ids)
                ).delete(synchronize_session=False)
                
                session.query(EmbeddingDocument).filter(
                    EmbeddingDocument.employee_id.in_(employee_ids)
                ).delete(synchronize_session=False)
                
                # Process all employees
                docs_to_add = []
                chunks_to_add = []
                
                for employee_data in employee_data_list:
                    employee_id = employee_data.get('id')
                    if not employee_id:
                        continue
                    
                    try:
                        # Parse profile data
                        profile_data = json.loads(employee_data.get('profile', '[]'))
                        metadata = employee_data.get('metadata', {})
                        
                        # Process each profile section
                        for section_idx, section in enumerate(profile_data):
                            # Convert section to JSON string if it's not already
                            if isinstance(section, dict):
                                section_text = json.dumps(section)
                            else:
                                section_text = section
                            
                            # Generate embedding
                            embedding = self._generate_embedding(section_text)
                            
                            # Create embedding document
                            doc = EmbeddingDocument(
                                employee_id=employee_id,
                                embedding_run_id=employee_id,
                                document_type="profile",
                                source_filename=f"profile_{employee_id}_{section_idx}",
                                external_document_id=employee_id,
                                source_type="profile"
                            )
                            docs_to_add.append(doc)
                            
                            # Create chunk
                            chunk = EmbeddingChunk(
                                external_document_id=employee_id,  # Will be updated after doc is created
                                chunk_index=section_idx,
                                content=section_text,
                                embedding=embedding,
                                token_count=len(section_text.split()),
                                char_count=len(section_text),
                                chunk_label=f"profile_section_{section_idx}"
                            )
                            chunks_to_add.append(chunk)
                            
                    except Exception as e:
                        logger.error(f"Error processing employee {employee_id}: {e}")
                        continue
                
                # Batch insert all documents first
                session.add_all(docs_to_add)
                session.flush()
                
                # Update external_document_id references in chunks
                for chunk in chunks_to_add:
                    chunk.external_document_id = chunk.external_document_id
                
                # Batch insert all chunks
                session.add_all(chunks_to_add)
                session.commit()
                
                logger.info(f"Batch stored {len(chunks_to_add)} profile sections for {len(employee_ids)} employees")
                
        except Exception as e:
            logger.error(f"Failed to batch store employee profiles: {e}")
            raise
    
    # =============================================================================
    # SEARCH METHODS
    # =============================================================================
    
    def get_relevant_chunks(self, query: str = None, n_results: int = 5, 
                          employee_id: str = None) -> List[str]:
        """
        Retrieve relevant document chunks based on a query.
        
        Args:
            query: The search query
            n_results: Maximum number of results to return
            employee_id: Optional employee ID to filter results
            
        Returns:
            List of relevant document chunks
        """
        try:
            with SessionLocal() as session:
                if employee_id:
                    # Search in employee-specific data
                    
                    # First try raw documents for detailed citations
                    if query:
                        query_embedding = self._generate_embedding(query)
                        
                        docs_query = session.query(EmbeddingChunk).join(EmbeddingDocument).filter(
                            EmbeddingDocument.employee_id == employee_id
                        ).order_by(
                            EmbeddingChunk.embedding.op('<->')(query_embedding)
                        ).limit(n_results)
                        
                        docs_results = docs_query.all()
                        if docs_results:
                            return [doc.content for doc in docs_results]
                    
                    # Fall back to profile sections
                    if query:
                        query_embedding = self._generate_embedding(query)
                        
                        profile_query = session.query(EmbeddingChunk).join(EmbeddingDocument).filter(
                            EmbeddingDocument.employee_id == employee_id
                        ).order_by(
                            EmbeddingChunk.embedding.op('<->')(query_embedding)
                        ).limit(n_results)
                        
                        profile_results = profile_query.all()
                        return [profile.content for profile in profile_results]
                    else:
                        # No query - return all for this employee
                        all_docs = session.query(EmbeddingChunk).join(EmbeddingDocument).filter(
                            EmbeddingDocument.employee_id == employee_id
                        ).all()
                        
                        if all_docs:
                            return [doc.content for doc in all_docs]
                        
                        return []
                
                else:
                    # Search across all employees
                    if query:
                        query_embedding = self._generate_embedding(query)
                        
                        results = session.query(EmbeddingChunk).join(EmbeddingDocument).order_by(
                            EmbeddingChunk.embedding.op('<->')(query_embedding)
                        ).limit(n_results).all()
                        
                        return [doc.content for doc in results]
                    else:
                        # Return all chunks
                        all_docs = session.query(EmbeddingChunk).join(EmbeddingDocument).limit(n_results).all()
                        return [doc.content for doc in all_docs]
                
        except Exception as e:
            logger.error(f"Error retrieving chunks: {e}")
            return []
    
    def search_employees(self, query: str, filters: Dict[str, Any] = None, 
                         n_results: int = 10) -> List[Dict[str, Any]]:
        """Search for employees based on a natural language query and optional filters."""
        try:
            with SessionLocal() as session:
                query_embedding = self._generate_embedding(query)
                
                # VALIDATION: Log the query being executed
                logger.info(f"Executing search_employees query: '{query}' with {n_results} max results")
                
                # Build base query with proper joins
                base_query = session.query(EmbeddingChunk, EmbeddingDocument).join(
                    EmbeddingDocument, 
                    EmbeddingChunk.external_document_id == EmbeddingDocument.external_document_id
                ).order_by(
                    EmbeddingChunk.embedding.op('<->')(query_embedding)
                )
                
                # Apply filters if provided
                if filters:
                    filter_conditions = []
                    for key, value in filters.items():
                        if isinstance(value, dict) and '$regex' in value:
                            pattern = value['$regex'].replace('.*', '')
                            filter_conditions.append(
                                func.lower(func.cast(EmbeddingChunk.chunk_label, text())).like(f'%{pattern.lower()}%')
                            )
                        else:
                            filter_conditions.append(
                                EmbeddingChunk.chunk_label == str(value)
                            )
                    
                    if filter_conditions:
                        base_query = base_query.filter(and_(*filter_conditions))
                
                # Execute query
                results = base_query.limit(n_results * 2).all()
                
                # VALIDATION: Log how many chunks were returned
                logger.info(f"search_employees: Retrieved {len(results)} chunks from database")
                
                # Group results by employee
                employee_results = {}
                for chunk, doc in results:
                    employee_id = doc.employee_id
                    if employee_id not in employee_results:
                        employee_results[employee_id] = {
                            'employee_id': str(employee_id),
                            'match_count': 0,
                            'matches': [],
                            'doc_metadata': {
                                'document_type': doc.document_type,
                                'source_filename': doc.source_filename
                            }
                        }
                    
                    employee_results[employee_id]['matches'].append(chunk.content)
                    employee_results[employee_id]['match_count'] += 1
                
                # Convert to list and sort by match count
                result_list = list(employee_results.values())
                result_list.sort(key=lambda x: x['match_count'], reverse=True)
                
                # VALIDATION: Log final results
                logger.info(f"search_employees: Found {len(result_list)} employees with {sum(len(r['matches']) for r in result_list)} total chunks")
                
                return result_list[:n_results]
                
        except Exception as e:
            logger.error(f"Error in search_employees: {e}")
            return []
    
    # =============================================================================
    # COMPATIBILITY METHODS (maintain same API as ChromaDB version)
    # =============================================================================
    
    def search_employees_advanced(self, query: str, filters: Dict[str, Any] = None, 
                                n_results: int = 10, 
                                hogan_filters: Dict[str, str] = None,
                                idi_filters: Dict[str, str] = None,
                                hr_filters: Dict[str, Any] = None) -> List[Dict[str, Any]]:
        """Advanced search with enhanced filtering capabilities."""
        # Combine all filters
        combined_filters = {}
        if filters:
            combined_filters.update(filters)
        if hogan_filters:
            combined_filters.update(hogan_filters)
        if idi_filters:
            combined_filters.update(idi_filters)
        if hr_filters:
            combined_filters.update(hr_filters)
        
        return self.search_employees(query, combined_filters, n_results)
    
    def search_by_assessment_profile(self, hogan_profile: Dict[str, str] = None,
                                   idi_profile: Dict[str, str] = None,
                                   similarity_threshold: float = 0.7,
                                   n_results: int = 10) -> List[Dict[str, Any]]:
        """Find employees with similar assessment profiles."""
        # This is a simplified implementation - could be enhanced with ML similarity
        try:
            with SessionLocal() as session:
                filter_conditions = []
                
                if hogan_profile:
                    for measure, level in hogan_profile.items():
                        filter_conditions.append(
                            EmbeddingChunk.chunk_label.like(f'%{measure}%')
                        )
                
                if idi_profile:
                    for measure, level in idi_profile.items():
                        filter_conditions.append(
                            EmbeddingChunk.chunk_label.like(f'%{measure}%')
                        )
                
                if not filter_conditions:
                    return []
                
                results = session.query(EmbeddingChunk, EmbeddingDocument).join(
                    EmbeddingDocument, 
                    EmbeddingChunk.external_document_id == EmbeddingDocument.external_document_id
                ).filter(
                    and_(*filter_conditions)
                ).limit(n_results).all()
                
                # Group by employee and calculate similarity scores
                employee_results = {}
                for chunk, doc in results:
                    employee_id = doc.employee_id
                    if employee_id not in employee_results:
                        employee_results[employee_id] = {
                            'employee_id': str(employee_id),
                            'similarity_score': 1.0,  # Simplified scoring
                            'metadata': {
                                'document_type': doc.document_type,
                                'source_filename': doc.source_filename
                            }
                        }
                
                return list(employee_results.values())
                
        except Exception as e:
            logger.error(f"Error in search_by_assessment_profile: {e}")
            return []
    
    def get_assessment_analytics(self) -> Dict[str, Any]:
        """Get analytics about assessment data in the vector store."""
        try:
            with SessionLocal() as session:
                # Count total employees with profiles
                total_employees = session.query(EmbeddingDocument.employee_id).distinct().count()
                
                # Count total profile sections
                total_sections = session.query(EmbeddingChunk).count()
                
                # Count total document chunks
                total_docs = session.query(EmbeddingChunk).count()
                
                return {
                    'total_employees': total_employees,
                    'total_profile_sections': total_sections,
                    'total_document_chunks': total_docs,
                    'avg_sections_per_employee': total_sections / max(total_employees, 1)
                }
                
        except Exception as e:
            logger.error(f"Error getting assessment analytics: {e}")
            return {}
    
    # LEGACY COMPATIBILITY METHODS (for backward compatibility) 
    
    def search_all_content(self, query: str, n_results: int = 15, 
                          employee_filter: str = None,
                          document_type_filter: str = None) -> List[Dict[str, Any]]:
        """Search across all content with optional filters."""
        try:
            with SessionLocal() as session:
                query_embedding = self._generate_embedding(query)
                
                base_query = session.query(EmbeddingChunk, EmbeddingDocument).join(
                    EmbeddingDocument, 
                    EmbeddingChunk.external_document_id == EmbeddingDocument.external_document_id
                ).order_by(
                    EmbeddingChunk.embedding.op('<->')(query_embedding)
                )
                
                # Apply filters
                if employee_filter:
                    base_query = base_query.filter(EmbeddingDocument.employee_id == employee_filter)
                
                if document_type_filter:
                    base_query = base_query.filter(EmbeddingDocument.document_type == document_type_filter)
                
                results = base_query.limit(n_results).all()
                
                return [
                    {
                        'content': chunk.content,
                        'score': 0.0,  # Simplified scoring
                        'metadata': {
                            'employee_id': str(doc.employee_id),
                            'document_type': doc.document_type,
                            'source_filename': doc.source_filename
                        }
                    }
                    for chunk, doc in results
                ]
                
        except Exception as e:
            logger.error(f"Error in search_all_content: {e}")
            return []
    
    def search_employee_documents(self, employee_name: str, query: str = None,
                                document_type: str = None, n_results: int = 5) -> List[Dict[str, Any]]:
        """Search within a specific employee's documents."""
        try:
            with SessionLocal() as session:
                # First find the employee by name
                from backend.db.models import Employee
                employee = session.query(Employee).filter(
                    func.lower(Employee.full_name) == func.lower(employee_name)
                ).first()
                
                if not employee:
                    return []
                
                # Search their documents
                base_query = session.query(EmbeddingChunk, EmbeddingDocument).join(
                    EmbeddingDocument, 
                    EmbeddingChunk.external_document_id == EmbeddingDocument.external_document_id
                ).filter(
                    EmbeddingDocument.employee_id == employee.id
                )
                
                if query:
                    query_embedding = self._generate_embedding(query)
                    base_query = base_query.order_by(
                        EmbeddingChunk.embedding.op('<->')(query_embedding)
                    )
                
                if document_type:
                    base_query = base_query.filter(EmbeddingDocument.document_type == document_type)
                
                results = base_query.limit(n_results).all()
                
                return [
                    {
                        'content': chunk.content,
                        'score': 0.0,  # Simplified scoring
                        'metadata': {
                            'employee_id': str(doc.employee_id),
                            'document_type': doc.document_type,
                            'source_filename': doc.source_filename
                        }
                    }
                    for chunk, doc in results
                ]
                
        except Exception as e:
            logger.error(f"Error in search_employee_documents: {e}")
            return [] 