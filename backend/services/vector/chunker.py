from typing import List, Dict
import re

class TextChunker:
    """Service for chunking text into smaller pieces for vector operations."""
    
    def __init__(self, max_tokens: int = 1000):
        """
        Initialize chunker with maximum tokens per chunk.
        
        Args:
            max_tokens: Maximum number of tokens per chunk (default 1000 per cursor rules)
        """
        self.max_tokens = max_tokens
    
    def chunk_text(self, text: str) -> List[str]:
        """
        Split text into chunks respecting token limits.
        
        Args:
            text: Text to chunk
            
        Returns:
            List of text chunks
        """
        # Simple approximation: 1 token ≈ 4 chars
        max_chars = self.max_tokens * 4
        
        # Split into paragraphs first
        paragraphs = text.split('\n\n')
        
        chunks = []
        current_chunk = []
        current_length = 0
        
        for para in paragraphs:
            # If paragraph is too long, split it into sentences
            if len(para) > max_chars:
                sentences = re.split(r'(?<=[.!?])\s+', para)
                for sentence in sentences:
                    if current_length + len(sentence) > max_chars:
                        if current_chunk:
                            chunks.append('\n'.join(current_chunk))
                            current_chunk = []
                            current_length = 0
                    current_chunk.append(sentence)
                    current_length += len(sentence)
            else:
                if current_length + len(para) > max_chars:
                    chunks.append('\n'.join(current_chunk))
                    current_chunk = []
                    current_length = 0
                current_chunk.append(para)
                current_length += len(para)
        
        # Add the last chunk if any
        if current_chunk:
            chunks.append('\n'.join(current_chunk))
        
        return chunks
    
    def chunk_cv(self, cv_data: Dict) -> Dict[str, List[str]]:
        """
        Chunk CV data into sections.
        
        Args:
            cv_data: Parsed CV data
            
        Returns:
            Dictionary with chunked sections
        """
        return {
            "summary": self.chunk_text(cv_data.get("summary", "")),
            "experience": [
                self.chunk_text(exp.get("description", ""))
                for exp in cv_data.get("experience", [])
            ],
            "skills": self.chunk_text(" ".join(cv_data.get("skills", [])))
        }
    
    def chunk_assessment(self, assessment_data: Dict) -> Dict[str, List[str]]:
        """
        Chunk assessment data into sections.
        
        Args:
            assessment_data: Parsed assessment data
            
        Returns:
            Dictionary with chunked sections
        """
        return {
            "recommendations": self.chunk_text(assessment_data.get("recommendations", "")),
            "summary": self.chunk_text(assessment_data.get("summary", ""))
        } 