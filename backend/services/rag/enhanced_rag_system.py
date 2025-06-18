import os
import json
import re
import tiktoken
from typing import List, Dict, Any, Optional
from openai import OpenAI
import streamlit as st
import logging

from backend.services.rag.enhanced_vector_store import EnhancedVectorStore
from backend.services.rag.document_loader import DocumentLoader
from backend.services.data_access.employee_database import EmployeeDatabase

logger = logging.getLogger(__name__)

class EnhancedRAGSystem:
    """Enhanced RAG system with access to both processed profiles and original documents"""
    
    def __init__(self, vector_store=None, employee_db=None):
        """Initialize the enhanced RAG system"""
        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key:
            raise ValueError("OPENAI_API_KEY environment variable is not set.")
        self.client = OpenAI(api_key=api_key)
        
        # Use enhanced vector store
        if vector_store is not None and isinstance(vector_store, EnhancedVectorStore):
            self.vector_store = vector_store
        else:
            self.vector_store = EnhancedVectorStore()
            
        if employee_db is not None:
            self.employee_db = employee_db
        else:
            self.employee_db = EmployeeDatabase()
        
        # Initialize document loader (integrated with vector store)
        self.document_loader = self.vector_store.document_loader
        
        # Initialize token encoder for GPT-4
        self.encoding = tiktoken.encoding_for_model("gpt-4")
        
        # Enhanced conversation management settings
        self.max_context_tokens = 6000
        self.max_conversation_tokens = 2000
        self.min_conversation_exchanges = 2
        
        # Enhanced system prompt that acknowledges access to original documents
        self.system_prompt = """You are a world-class expert in leadership psychology, organizational behavior, and executive development. You specialize in synthesizing diverse data sources—such as personality assessments, 360 feedback, coaching notes, performance reviews, and CVs—into insightful, psychologically sophisticated leadership profiles.

Your capabilities include:
1. Access to both processed employee profiles AND original documents (CVs, Hogan assessments, IDI reports)
2. Fine-grained analysis from specific sections of original documents
3. Cross-employee analysis and comparisons
4. Pattern recognition across teams and departments
5. Sophisticated interpretation of assessment data
6. Strategic recommendations for talent development and placement

CRITICAL DOCUMENT ACCESS:
You have access to:
- Processed leadership profiles (summaries and analyses)
- Original CV/Resume documents (detailed career history, education, skills)
- Original Hogan assessment reports (raw scores and detailed interpretations)
- Original IDI assessment reports (developmental dimensions and scores)
- Other supporting documents when available

When citing information, please specify the source type (e.g., "From their CV", "Based on Hogan assessment", "According to IDI report", "From leadership profile analysis").

CRITICAL NUMERICAL SCORE REQUIREMENT:
When discussing assessment scores, you MUST ALWAYS provide the exact numerical values from the source documents. NEVER use vague descriptions like "high adjustment", "moderate ambition", or "low sociability". Instead, always state the precise score (e.g., "Adjustment: 58", "Ambition: 24", "Sociability: 39").

CRITICAL SOURCE VALIDATION: 
ONLY cite sources explicitly found in the provided context. Always verify that the sources you are citing exist in the data provided. It is better to say 'I don't have sufficient data' than to reference non-existent sources. When you have access to original documents, you can provide much more detailed and specific information than from summaries alone."""

        # Conversation tracking
        self.conversation_history = []
        self.context_employees = []
        self.conversation_metadata = {
            "total_tokens_used": 0,
            "peak_employee_count": 0,
            "conversation_theme": None
        }
        
        logger.info("Enhanced RAG System initialized with document access")
    
    def _count_tokens(self, text: str) -> int:
        """Count tokens in text using GPT-4 tokenizer"""
        try:
            return len(self.encoding.encode(text))
        except:
            return len(text) // 4
    
    def initialize_system(self, employees: List[Dict[str, Any]]):
        """Initialize the system with employee data and build indexes"""
        logger.info("Initializing Enhanced RAG System with employee data...")
        
        try:
            # Rebuild the vector store with both profiles and documents
            self.vector_store.rebuild_index(employees)
            
            # Get statistics
            stats = self.vector_store.get_statistics()
            logger.info(f"System initialized successfully:")
            logger.info(f"  - Profiles indexed: {stats['profiles']['count']} employees, {stats['profiles']['chunks']} chunks")
            logger.info(f"  - Documents indexed: {stats['documents']['count']} documents, {stats['documents']['chunks']} chunks")
            logger.info(f"  - Document types: {stats['document_loader'].get('document_types', {})}")
            
            return True
            
        except Exception as e:
            logger.error(f"Error initializing Enhanced RAG System: {e}")
            return False
    
    def query(self, question: str, employee_focus: Optional[str] = None, 
              document_type_filter: Optional[str] = None) -> str:
        """Enhanced query with access to both profiles and original documents"""
        
        try:
            # Determine query strategy based on content
            query_analysis = self._analyze_query_intent(question)
            
            # Search across both profiles and documents
            search_results = self.vector_store.search_all_content(
                query=question,
                n_results=15,
                employee_filter=employee_focus,
                document_type_filter=document_type_filter
            )
            
            # If employee focus is specified, also get their specific documents
            employee_doc_results = []
            if employee_focus:
                employee_doc_results = self.vector_store.search_employee_documents(
                    employee_name=employee_focus,
                    query=question,
                    n_results=5,
                    document_type=document_type_filter
                )
                search_results.extend(employee_doc_results)
            
            # Build context from search results
            context_chunks = []
            context_sources = set()
            
            for result in search_results[:12]:  # Limit to top results
                content = result['content']
                metadata = result['metadata']
                source = result['source']
                
                # Add source information to the content
                if source == 'original_document':
                    doc_type = metadata.get('document_type', 'unknown')
                    employee = metadata.get('employee_name', 'unknown')
                    source_header = f"[Source: {doc_type.upper()} document for {employee}]"
                else:
                    employee = metadata.get('employee_name', 'unknown')
                    source_header = f"[Source: Leadership profile for {employee}]"
                
                context_chunks.append(f"{source_header}\n{content}")
                context_sources.add(f"{source}:{metadata.get('document_type', 'profile')}")
            
            # Generate response
            if not context_chunks:
                return "I don't have sufficient information to answer your question. Please ensure the employee database has been loaded and indexed."
            
            context_text = "\n\n".join(context_chunks)
            
            # Build enhanced prompt
            enhanced_prompt = f"""Based on the provided context that includes both leadership profile analyses and original documents (CVs, assessments, etc.), please answer the following question:

Question: {question}

Context from multiple sources:
{context_text}

Please provide a comprehensive answer that:
1. Cites specific sources (CV, Hogan assessment, IDI report, leadership profile, etc.)
2. Includes exact numerical scores when discussing assessments
3. Distinguishes between information from processed analyses vs. original documents
4. Provides detailed, evidence-based insights

Answer:"""

            # Generate response
            response = self.client.chat.completions.create(
                model="gpt-4",
                messages=[
                    {"role": "system", "content": self.system_prompt},
                    {"role": "user", "content": enhanced_prompt}
                ],
                max_tokens=1500,
                temperature=0.3
            )
            
            answer = response.choices[0].message.content
            
            # Update conversation history
            self._update_conversation_history(question, answer, list(context_sources))
            
            return answer
            
        except Exception as e:
            logger.error(f"Error in enhanced query: {e}")
            return f"I encountered an error while processing your question: {str(e)}"
    
    def get_employee_document_details(self, employee_name: str) -> Dict[str, Any]:
        """Get detailed information about available documents for an employee"""
        
        # Get document summary from vector store
        doc_summary = self.vector_store.get_employee_document_summary(employee_name)
        
        if not doc_summary.get('found'):
            return {
                'found': False,
                'message': f"No documents found for {employee_name}"
            }
        
        # Get additional details from document loader
        employee_docs = self.document_loader.get_employee_documents(employee_name)
        
        detailed_info = {
            'found': True,
            'employee_name': employee_name,
            'available_documents': doc_summary['available_documents'],
            'indexed_documents': doc_summary['indexed_documents'],
            'total_documents': doc_summary['total_documents'],
            'document_details': {}
        }
        
        # Add size and filename info for each document
        for doc_type in doc_summary['available_documents']:
            if doc_type in employee_docs.get('documents', {}):
                doc_info = employee_docs['documents'][doc_type]
                detailed_info['document_details'][doc_type] = {
                    'filename': doc_info['filename'],
                    'size_bytes': doc_info['size'],
                    'size_readable': f"{doc_info['size'] / 1024:.1f} KB"
                }
        
        return detailed_info
    
    def search_specific_document(self, employee_name: str, document_type: str, query: str) -> Dict[str, Any]:
        """Search within a specific document for an employee"""
        
        # Search the specific document
        results = self.vector_store.search_employee_documents(
            employee_name=employee_name,
            query=query,
            document_type=document_type,
            n_results=5
        )
        
        if not results:
            return {
                'found': False,
                'message': f"No relevant content found in {document_type} document for {employee_name}"
            }
        
        # Format results
        formatted_results = []
        for result in results:
            formatted_results.append({
                'content': result['content'],
                'relevance_score': result['score'],
                'document_type': result['document_type'],
                'chunk_info': result['metadata']
            })
        
        return {
            'found': True,
            'employee_name': employee_name,
            'document_type': document_type,
            'query': query,
            'results': formatted_results,
            'total_chunks': len(formatted_results)
        }
    
    def _analyze_query_intent(self, query: str) -> Dict[str, Any]:
        """Analyze query to understand intent and optimize search strategy"""
        query_lower = query.lower()
        
        # Detect if asking for specific document types
        document_indicators = {
            'cv': ['cv', 'resume', 'career', 'education', 'experience', 'job history'],
            'hogan': ['hogan', 'personality', 'hpi', 'hds', 'mvpi', 'adjustment', 'ambition'],
            'idi': ['idi', 'individual directions', 'development', 'giving', 'receiving'],
            'assessment': ['assessment', 'scores', 'results', 'evaluation']
        }
        
        likely_documents = []
        for doc_type, indicators in document_indicators.items():
            if any(indicator in query_lower for indicator in indicators):
                likely_documents.append(doc_type)
        
        # Detect scope
        if any(word in query_lower for word in ['compare', 'versus', 'vs', 'difference']):
            scope = 'comparison'
        elif any(word in query_lower for word in ['team', 'group', 'department']):
            scope = 'team_analysis'
        elif any(word in query_lower for word in ['top', 'best', 'highest', 'lowest', 'rank']):
            scope = 'ranking'
        else:
            scope = 'individual'
        
        return {
            'likely_documents': likely_documents,
            'scope': scope,
            'requires_original_docs': len(likely_documents) > 0 or 'specific' in query_lower
        }
    
    def _update_conversation_history(self, question: str, answer: str, sources: List[str]):
        """Update conversation history with source tracking"""
        
        tokens_used = self._count_tokens(question + answer)
        
        conversation_entry = {
            "original_query": question,
            "response": answer,
            "sources": sources,
            "tokens_used": tokens_used,
            "timestamp": self._get_timestamp()
        }
        
        self.conversation_history.append(conversation_entry)
        self.conversation_metadata["total_tokens_used"] += tokens_used
    
    def _get_timestamp(self) -> str:
        """Get current timestamp"""
        from datetime import datetime
        return datetime.now().isoformat()
    
    def get_conversation_insights(self) -> Dict[str, Any]:
        """Get insights about the current conversation"""
        return {
            "status": "active" if self.conversation_history else "no_conversation",
            "conversation_length": len(self.conversation_history),
            "total_tokens_used": self.conversation_metadata["total_tokens_used"],
            "conversation_theme": self.conversation_metadata.get("conversation_theme", "general"),
            "available_documents": self.document_loader.get_statistics()
        }
    
    def clear_conversation_history(self):
        """Clear conversation history"""
        self.conversation_history = []
        self.context_employees = []
        self.conversation_metadata = {
            "total_tokens_used": 0,
            "peak_employee_count": 0,
            "conversation_theme": None
        }
        logger.info("Conversation history cleared")
    
    def get_system_statistics(self) -> Dict[str, Any]:
        """Get comprehensive system statistics"""
        return {
            'vector_store': self.vector_store.get_statistics(),
            'document_loader': self.document_loader.get_statistics(),
            'conversation': {
                'total_conversations': len(self.conversation_history),
                'total_tokens_used': self.conversation_metadata["total_tokens_used"]
            }
        }
    
    def validate_system_health(self) -> Dict[str, Any]:
        """Validate system health and document accessibility"""
        health_report = {
            'status': 'healthy',
            'issues': [],
            'warnings': []
        }
        
        try:
            # Check vector store
            stats = self.vector_store.get_statistics()
            if stats['documents']['count'] == 0:
                health_report['warnings'].append("No original documents indexed")
            
            # Check document loader
            doc_issues = self.document_loader.validate_documents()
            for issue_type, files in doc_issues.items():
                if files:
                    health_report['issues'].append(f"{issue_type}: {len(files)} files")
            
            # Check OpenAI connection
            test_embedding = self.vector_store._get_embedding("test")
            if not test_embedding:
                health_report['issues'].append("OpenAI embedding service not accessible")
            
            if health_report['issues']:
                health_report['status'] = 'degraded'
            elif health_report['warnings']:
                health_report['status'] = 'warning'
                
        except Exception as e:
            health_report['status'] = 'error'
            health_report['issues'].append(f"System validation error: {str(e)}")
        
        return health_report 