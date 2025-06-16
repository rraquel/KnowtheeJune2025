from typing import Optional, Union, List, Dict, Any
import os
from openai import OpenAI
from log import logger

class OpenAIEmbedder(BaseEmbedder):
    """OpenAI embedding model implementation."""
    
    def __init__(self, api_key: Optional[str] = None):
        """Initialize the OpenAI embedder.
        
        Args:
            api_key: OpenAI API key. If not provided, will try to get from environment.
        """
        self.api_key = api_key or os.getenv("OPENAI_API_KEY")
        if not self.api_key:
            raise ValueError("OpenAI API key not provided and not found in environment")
        
        self.client = OpenAI(api_key=self.api_key)
        self.model = "text-embedding-3-small"
        self.dimensions = 1536  # text-embedding-3-small dimension
    
    def embed(self, texts: Union[str, List[str]], metadata: Optional[Dict[str, Any]] = None) -> Union[List[float], List[List[float]]]:
        """Generate embeddings for input text(s).
        
        Args:
            texts: Single text string or list of text strings to embed
            metadata: Optional metadata about the texts
            
        Returns:
            For single text: List of floats representing the embedding
            For multiple texts: List of lists of floats, one embedding per text
        """
        if isinstance(texts, str):
            texts = [texts]
            
        try:
            response = self.client.embeddings.create(
                model=self.model,
                input=texts
            )
            
            embeddings = [data.embedding for data in response.data]
            return embeddings[0] if len(texts) == 1 else embeddings
            
        except Exception as e:
            logger.error(f"Error generating embeddings: {str(e)}")
            raise 