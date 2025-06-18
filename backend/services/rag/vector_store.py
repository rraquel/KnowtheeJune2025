"""
PostgreSQL pgvector-based vector store
Production-ready vector storage and retrieval using PostgreSQL + pgvector
"""
import os
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
                logger.warning("OPENAI_API_KEY not set - vector search will be limited")
                self.openai_client = None
            else:
                self.openai_client = openai.OpenAI(api_key=openai_api_key)
            
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
                session.query(EmbeddingChunk).filter(
                    EmbeddingChunk.employee_id == employee_id
                ).delete()
                
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
                    
                    profile = EmbeddingChunk(
                        document_id=f"{employee_id}_{i}",
                        employee_id=employee_id,
                        content=section_text,
                        embedding=embedding,
                        doc_metadata=section_metadata,
                        tenant_id=self.DEFAULT_TENANT_ID
                    )
                    session.add(profile)
                
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
                session.query(EmbeddingChunk).filter(
                    EmbeddingChunk.employee_id == employee_id
                ).delete()
                
                if not documents:
                    session.commit()
                    return
                
                # Store each document chunk
                for i, doc in enumerate(documents):
                    embedding = self._generate_embedding(doc)
                    
                    # Create metadata for this document
                    doc_metadata = {
                        "employee_id": employee_id,
                        "chunk_id": i
                    }
                    
                    # Add employee metadata if provided
                    if metadata:
                        for key, value in metadata.items():
                            # Handle list values by concatenating them
                            if isinstance(value, list):
                                doc_metadata[key] = ", ".join(str(item) for item in value)
                            else:
                                doc_metadata[key] = str(value)
                    
                    document = EmbeddingChunk(
                        document_id=f"{employee_id}_doc_{i}",
                        employee_id=employee_id,
                        content=doc,
                        embedding=embedding,
                        doc_metadata=doc_metadata,
                        tenant_id=self.DEFAULT_TENANT_ID
                    )
                    session.add(document)
                
                session.commit()
                logger.info(f"Stored {len(documents)} document chunks for employee {employee_id}")
                
        except Exception as e:
            logger.error(f"Failed to store employee documents {employee_id}: {e}")
            raise
    
    def delete_employee_profile(self, employee_id: str):
        """Delete all vector entries for an employee."""
        try:
            with SessionLocal() as session:
                # Delete from profiles
                session.query(EmbeddingChunk).filter(
                    EmbeddingChunk.employee_id == employee_id
                ).delete()
                
                # Delete from documents
                session.query(EmbeddingChunk).filter(
                    EmbeddingChunk.employee_id == employee_id
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
                session.query(EmbeddingChunk).filter(
                    EmbeddingChunk.employee_id.in_(employee_ids)
                ).delete(synchronize_session=False)
                
                # Process all employees
                profiles_to_add = []
                
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
                            
                            # Create metadata for this section
                            section_metadata = {
                                "employee_id": employee_id,
                                "section_id": section_idx
                            }
                            
                            # Add employee metadata if provided
                            if metadata:
                                for key, value in metadata.items():
                                    if isinstance(value, list):
                                        section_metadata[key] = ", ".join(str(item) for item in value)
                                    else:
                                        section_metadata[key] = str(value)
                            
                            profile = EmbeddingChunk(
                                document_id=f"{employee_id}_{section_idx}",
                                employee_id=employee_id,
                                content=section_text,
                                embedding=embedding,
                                doc_metadata=section_metadata,
                                tenant_id=self.DEFAULT_TENANT_ID
                            )
                            profiles_to_add.append(profile)
                            
                    except Exception as e:
                        logger.error(f"Error processing employee {employee_id}: {e}")
                        continue
                
                # Batch insert all profiles
                session.add_all(profiles_to_add)
                session.commit()
                
                logger.info(f"Batch stored {len(profiles_to_add)} profile sections for {len(employee_ids)} employees")
                
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
                        
                        docs_query = session.query(EmbeddingChunk).filter(
                            EmbeddingChunk.employee_id == employee_id
                        ).order_by(
                            EmbeddingChunk.embedding.op('<->')(query_embedding)
                        ).limit(n_results)
                        
                        docs_results = docs_query.all()
                        if docs_results:
                            return [doc.content for doc in docs_results]
                    
                    # Fall back to profile sections
                    if query:
                        query_embedding = self._generate_embedding(query)
                        
                        profile_query = session.query(EmbeddingChunk).filter(
                            EmbeddingChunk.employee_id == employee_id
                        ).order_by(
                            EmbeddingChunk.embedding.op('<->')(query_embedding)
                        ).limit(n_results)
                        
                        profile_results = profile_query.all()
                        return [profile.content for profile in profile_results]
                    else:
                        # No query - return all for this employee
                        all_docs = session.query(EmbeddingChunk).filter(
                            EmbeddingChunk.employee_id == employee_id
                        ).all()
                        
                        if all_docs:
                            return [doc.content for doc in all_docs]
                        
                        all_profiles = session.query(EmbeddingChunk).filter(
                            EmbeddingChunk.employee_id == employee_id
                        ).all()
                        
                        return [profile.content for profile in all_profiles]
                
                else:
                    # Search in leadership documents (single profile)
                    if query:
                        query_embedding = self._generate_embedding(query)
                        
                        results = session.query(EmbeddingDocument).order_by(
                            EmbeddingDocument.embedding.op('<->')(query_embedding)
                        ).limit(n_results).all()
                        
                        return [doc.content for doc in results]
                    else:
                        # Return all leadership documents
                        all_docs = session.query(EmbeddingDocument).all()
                        return [doc.content for doc in all_docs]
                
        except Exception as e:
            logger.error(f"Error retrieving chunks: {e}")
            return []
    
    def search_employees(self, query: str, filters: Dict[str, Any] = None, 
                         n_results: int = 10) -> List[Dict[str, Any]]:
        """
        Search for employees based on a natural language query and optional filters.
        
        Args:
            query: Natural language query
            filters: Dictionary of metadata filters
            n_results: Maximum number of results to return
            
        Returns:
            List of results with employee_id and matched text
        """
        try:
            with SessionLocal() as session:
                query_embedding = self._generate_embedding(query)
                
                # Build base query
                base_query = session.query(EmbeddingChunk).order_by(
                    EmbeddingChunk.embedding.op('<->')(query_embedding)
                )
                
                # Apply filters if provided
                if filters:
                    filter_conditions = []
                    for key, value in filters.items():
                        # Handle regex pattern filters
                        if isinstance(value, dict) and '$regex' in value:
                            pattern = value['$regex'].replace('.*', '')
                            filter_conditions.append(
                                func.lower(func.cast(EmbeddingChunk.doc_metadata[key], text())).like(f'%{pattern.lower()}%')
                            )
                        else:
                            # Exact match
                            filter_conditions.append(
                                EmbeddingChunk.doc_metadata[key].astext == str(value)
                            )
                    
                    if filter_conditions:
                        base_query = base_query.filter(and_(*filter_conditions))
                
                # Execute query
                results = base_query.limit(n_results * 2).all()
                
                # Group results by employee
                employee_results = {}
                for result in results:
                    employee_id = result.employee_id
                    if employee_id not in employee_results:
                        employee_results[employee_id] = {
                            'employee_id': employee_id,
                            'match_count': 0,
                            'matches': [],
                            'doc_metadata': result.doc_metadata
                        }
                    
                    employee_results[employee_id]['matches'].append(result.content)
                    employee_results[employee_id]['match_count'] += 1
                
                # Convert to list and sort by match count
                result_list = list(employee_results.values())
                result_list.sort(key=lambda x: x['match_count'], reverse=True)
                
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
                            EmbeddingChunk.doc_metadata[measure].astext == level
                        )
                
                if idi_profile:
                    for measure, level in idi_profile.items():
                        filter_conditions.append(
                            EmbeddingChunk.doc_metadata[measure].astext == level
                        )
                
                if not filter_conditions:
                    return []
                
                results = session.query(EmbeddingChunk).filter(
                    and_(*filter_conditions)
                ).limit(n_results).all()
                
                # Group by employee and calculate similarity scores
                employee_results = {}
                for result in results:
                    employee_id = result.employee_id
                    if employee_id not in employee_results:
                        employee_results[employee_id] = {
                            'employee_id': employee_id,
                            'similarity_score': 1.0,  # Simplified scoring
                            'metadata': result.doc_metadata
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
                total_employees = session.query(EmbeddingChunk.employee_id).distinct().count()
                
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