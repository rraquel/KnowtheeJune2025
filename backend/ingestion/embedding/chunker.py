from typing import List, Dict, Optional
import re
import logging
from .chunking_registry import registry

logger = logging.getLogger(__name__)

class TextChunker:
    """Service for chunking text into smaller pieces for vector operations."""
    
    def __init__(
        self,
        max_chunk_size: int = 800,
        min_chunk_size: int = 300
    ):
        """Initialize chunker with size constraints.
        
        Args:
            max_chunk_size: Maximum characters per chunk
            min_chunk_size: Minimum characters per chunk
        """
        self.max_chunk_size = max_chunk_size
        self.min_chunk_size = min_chunk_size
        
    def chunk_text(self, text: str, doc_type: Optional[str] = None) -> List[str]:
        """Split text into chunks respecting size constraints.
        
        Args:
            text: Text to chunk
            doc_type: Optional document type ('CV', 'IDI', 'Hogan')
            
        Returns:
            List of text chunks
        """
        if doc_type == "CV":
            return self._chunk_cv(text)
        elif doc_type in ["IDI", "Hogan"]:
            return self._chunk_assessment(text)
        else:
            return self._chunk_generic(text)
            
    @registry.register("cv")
    def _chunk_cv(self, text: str) -> List[str]:
        """Chunk CV text based on sections and paragraphs.
        
        Args:
            text: CV text to chunk
            
        Returns:
            List of CV text chunks
        """
        # Common CV section headers
        section_patterns = [
            r"(?i)^\s*(?:PROFESSIONAL|WORK)\s+EXPERIENCE\s*$",
            r"(?i)^\s*EDUCATION\s*$",
            r"(?i)^\s*SKILLS\s*$",
            r"(?i)^\s*SUMMARY\s*$",
            r"(?i)^\s*CERTIFICATIONS\s*$",
            r"(?i)^\s*PROJECTS\s*$"
        ]
        
        # Split into sections
        sections = []
        current_section = []
        
        for line in text.split('\n'):
            # Check if line matches any section header
            is_section = any(re.match(pattern, line) for pattern in section_patterns)
            
            if is_section and current_section:
                sections.append('\n'.join(current_section))
                current_section = []
            
            current_section.append(line)
            
        if current_section:
            sections.append('\n'.join(current_section))
            
        # Further chunk each section if needed
        chunks = []
        for section in sections:
            if len(section) <= self.max_chunk_size:
                chunks.append(section)
            else:
                # Split section into paragraphs
                paragraphs = section.split('\n\n')
                current_chunk = []
                current_length = 0
                
                for para in paragraphs:
                    if current_length + len(para) > self.max_chunk_size:
                        if current_chunk:
                            chunk_text = '\n\n'.join(current_chunk)
                            if len(chunk_text) >= self.min_chunk_size:
                                chunks.append(chunk_text)
                            current_chunk = []
                            current_length = 0
                            
                    current_chunk.append(para)
                    current_length += len(para)
                    
                if current_chunk:
                    chunk_text = '\n\n'.join(current_chunk)
                    if len(chunk_text) >= self.min_chunk_size:
                        chunks.append(chunk_text)
                        
        return chunks
        
    @registry.register("assessment")
    def _chunk_assessment(self, text: str) -> List[str]:
        """Chunk assessment text based on question-answer pairs.
        
        Args:
            text: Assessment text to chunk
            
        Returns:
            List of assessment text chunks
        """
        # Split into question-answer pairs
        qa_pairs = []
        current_pair = []
        
        for line in text.split('\n'):
            # Check for question markers
            is_question = re.match(r'^(?:Q:|Question:|[0-9]+\.)', line.strip())
            
            if is_question and current_pair:
                qa_pairs.append('\n'.join(current_pair))
                current_pair = []
                
            current_pair.append(line)
            
        if current_pair:
            qa_pairs.append('\n'.join(current_pair))
            
        # Further chunk long pairs if needed
        chunks = []
        for pair in qa_pairs:
            if len(pair) <= self.max_chunk_size:
                chunks.append(pair)
            else:
                # Split pair into sentences
                sentences = re.split(r'(?<=[.!?])\s+', pair)
                current_chunk = []
                current_length = 0
                
                for sentence in sentences:
                    if current_length + len(sentence) > self.max_chunk_size:
                        if current_chunk:
                            chunk_text = ' '.join(current_chunk)
                            if len(chunk_text) >= self.min_chunk_size:
                                chunks.append(chunk_text)
                            current_chunk = []
                            current_length = 0
                            
                    current_chunk.append(sentence)
                    current_length += len(sentence)
                    
                if current_chunk:
                    chunk_text = ' '.join(current_chunk)
                    if len(chunk_text) >= self.min_chunk_size:
                        chunks.append(chunk_text)
                        
        return chunks
        
    @registry.register("generic")
    def _chunk_generic(self, text: str) -> List[str]:
        """Chunk generic text based on paragraphs and sentences.
        
        Args:
            text: Text to chunk
            
        Returns:
            List of text chunks
        """
        # Split into paragraphs first
        paragraphs = text.split('\n\n')
        chunks = []
        current_chunk = []
        current_length = 0
        
        for para in paragraphs:
            if len(para) > self.max_chunk_size:
                # Split paragraph into sentences
                sentences = re.split(r'(?<=[.!?])\s+', para)
                for sentence in sentences:
                    if current_length + len(sentence) > self.max_chunk_size:
                        if current_chunk:
                            chunk_text = ' '.join(current_chunk)
                            if len(chunk_text) >= self.min_chunk_size:
                                chunks.append(chunk_text)
                            current_chunk = []
                            current_length = 0
                            
                    current_chunk.append(sentence)
                    current_length += len(sentence)
            else:
                if current_length + len(para) > self.max_chunk_size:
                    if current_chunk:
                        chunk_text = '\n\n'.join(current_chunk)
                        if len(chunk_text) >= self.min_chunk_size:
                            chunks.append(chunk_text)
                        current_chunk = []
                        current_length = 0
                        
                current_chunk.append(para)
                current_length += len(para)
                
        if current_chunk:
            chunk_text = '\n\n'.join(current_chunk)
            if len(chunk_text) >= self.min_chunk_size:
                chunks.append(chunk_text)
                
        return chunks 