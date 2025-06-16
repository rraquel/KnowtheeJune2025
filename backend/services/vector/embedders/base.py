from abc import ABC, abstractmethod
from typing import List, Dict, Any

class BaseEmbedder(ABC):
    """Base class for text embedding strategies."""
    
    @abstractmethod
    def embed(self, texts: List[str], metadata: Dict[str, Any] = None) -> List[Dict[str, Any]]:
        """
        Generate embeddings for texts with metadata.
        
        Args:
            texts: List of texts to embed
            metadata: Optional metadata to attach to embeddings
            
        Returns:
            List of dictionaries containing:
            - text: Original text
            - embedding: Vector embedding
            - metadata: Original metadata plus any embedding-specific metadata
        """
        pass 