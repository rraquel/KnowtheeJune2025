from abc import ABC, abstractmethod
from typing import List, Dict, Any

class BaseChunker(ABC):
    """Base class for text chunking strategies."""
    
    @abstractmethod
    def chunk(self, text: str, metadata: Dict[str, Any] = None) -> List[Dict[str, Any]]:
        """
        Split text into chunks with metadata.
        
        Args:
            text: Text to chunk
            metadata: Optional metadata to attach to chunks
            
        Returns:
            List of dictionaries containing:
            - text: The chunked text
            - metadata: Original metadata plus any chunk-specific metadata
        """
        pass 