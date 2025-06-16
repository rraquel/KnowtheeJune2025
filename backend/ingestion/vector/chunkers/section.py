import re
from typing import List, Dict, Any, Optional
from .base import BaseChunker

class SectionChunker(BaseChunker):
    """Chunks text into sections based on headers."""
    
    def __init__(self, max_chunk_size: int = 1000):
        """
        Initialize section chunker.
        
        Args:
            max_chunk_size: Maximum size of each chunk in characters
        """
        self.max_chunk_size = max_chunk_size

    def chunk(self, text: str, metadata: Optional[Dict[str, Any]] = None, summary: Optional[str] = None) -> List[Dict[str, Any]]:
        """Split text into chunks based on sections."""
        if not text.strip():
            return []
        
        # Split text into sections
        sections = self._split_into_sections(text)
        chunks = []
        
        # Process each section
        for section_idx, (header, content) in enumerate(sections):
            # Split large sections into smaller chunks
            section_chunks = self._split_large_section(content)
            
            # Add each chunk with metadata
            for chunk_idx, chunk_text in enumerate(section_chunks):
                chunk_metadata = {
                    'section': header.strip() if header else 'No Section',
                    'section_index': section_idx,
                    'chunk_index': chunk_idx,
                    'total_chunks': len(section_chunks)
                }
                if metadata:
                    chunk_metadata.update(metadata)
                
                chunks.append({
                    'text': chunk_text.strip(),
                    'metadata': chunk_metadata
                })
        
        # Add summary as a separate chunk if provided
        if summary:
            summary_metadata = {
                'section': 'Summary',
                'section_index': len(sections),
                'chunk_index': 0,
                'total_chunks': 1
            }
            if metadata:
                summary_metadata.update(metadata)
            
            chunks.append({
                'text': summary.strip(),
                'metadata': summary_metadata
            })
        
        return chunks

    def _split_into_sections(self, text: str) -> List[tuple[str, str]]:
        """Split text into sections based on headers."""
        # Split by lines and find headers (uppercase lines)
        lines = text.split('\n')
        sections = []
        current_header = None
        current_content = []
        
        for line in lines:
            if line.strip().isupper() and len(line.strip()) > 3:
                # Save previous section if exists
                if current_content:
                    sections.append((current_header, '\n'.join(current_content)))
                current_header = line.strip()
                current_content = []
            else:
                current_content.append(line)
        
        # Add last section
        if current_content:
            sections.append((current_header, '\n'.join(current_content)))
        
        return sections

    def _split_large_section(self, text: str) -> List[str]:
        """Split a large section into smaller chunks."""
        if len(text) <= self.max_chunk_size:
            return [text]
        
        # Split by paragraphs first
        paragraphs = text.split('\n\n')
        chunks = []
        current_chunk = []
        current_size = 0
        
        for para in paragraphs:
            para_size = len(para)
            if current_size + para_size > self.max_chunk_size and current_chunk:
                chunks.append('\n\n'.join(current_chunk))
                current_chunk = []
                current_size = 0
            
            current_chunk.append(para)
            current_size += para_size
        
        if current_chunk:
            chunks.append('\n\n'.join(current_chunk))
        
        return chunks
    
    def chunk_cv(self, cv_data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Chunk CV data into sections.
        
        Args:
            cv_data: Parsed CV data
            
        Returns:
            List of dictionaries containing chunked sections with metadata
        """
        chunks = []
        
        # Chunk summary
        if summary := cv_data.get("summary"):
            chunks.extend(self.chunk(summary, {
                'section': 'summary',
                'employee_id': cv_data.get('employee_id'),
                'doc_type': 'CV'
            }))
        
        # Chunk experiences
        for i, exp in enumerate(cv_data.get("experience", [])):
            if description := exp.get("description"):
                chunks.extend(self.chunk(description, {
                    'section': 'experience',
                    'index': i,
                    'title': exp.get('title'),
                    'company': exp.get('company'),
                    'employee_id': cv_data.get('employee_id'),
                    'doc_type': 'CV'
                }))
        
        # Chunk skills
        if skills := cv_data.get("skills"):
            skills_text = " ".join(skills)
            chunks.extend(self.chunk(skills_text, {
                'section': 'skills',
                'employee_id': cv_data.get('employee_id'),
                'doc_type': 'CV'
            }))
        
        return chunks
    
    def chunk_assessment(self, assessment_data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Chunk assessment data into sections.
        
        Args:
            assessment_data: Parsed assessment data
            
        Returns:
            List of dictionaries containing chunked sections with metadata
        """
        chunks = []
        
        # Chunk recommendations
        if recommendations := assessment_data.get("recommendations"):
            chunks.extend(self.chunk(recommendations, {
                'section': 'recommendations',
                'employee_id': assessment_data.get('employee_id'),
                'doc_type': assessment_data.get('type', 'Assessment')
            }))
        
        # Chunk summary
        if summary := assessment_data.get("summary"):
            chunks.extend(self.chunk(summary, {
                'section': 'summary',
                'employee_id': assessment_data.get('employee_id'),
                'doc_type': assessment_data.get('type', 'Assessment')
            }))
        
        return chunks 