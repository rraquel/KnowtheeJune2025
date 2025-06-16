from typing import List, Optional, Union
import os
import logging
from pathlib import Path
from openai import OpenAI
from dotenv import load_dotenv

logger = logging.getLogger(__name__)

class OpenAIEmbedder:
    """OpenAI embedding model implementation."""
    
    def __init__(
        self,
        model: str = "text-embedding-3-small",
        api_key: Optional[str] = None
    ):
        """Initialize the OpenAI embedder.
        
        Args:
            model: OpenAI embedding model to use
            api_key: OpenAI API key. If not provided, will try to get from environment.
        """
        # Load environment variables from root .env file
        root_dir = Path(__file__).resolve().parents[3]
        env_path = root_dir / ".env"
        if not env_path.exists():
            raise ValueError(f"Could not find .env file at {env_path}")
        load_dotenv(dotenv_path=env_path)
        
        self.model = model
        self.api_key = api_key or os.getenv("OPENAI_API_KEY")
        if not self.api_key:
            raise ValueError("OpenAI API key not found in environment. Please set OPENAI_API_KEY in .env file")
            
        self.client = OpenAI(api_key=self.api_key)
        self.dimensions = 1536  # text-embedding-3-small dimension
        
    def embed(
        self,
        texts: Union[str, List[str]],
        batch_size: int = 100
    ) -> Union[List[float], List[List[float]]]:
        """Generate embeddings for input text(s).
        
        Args:
            texts: Single text string or list of text strings to embed
            batch_size: Number of texts to process in each API call
            
        Returns:
            For single text: List of floats representing the embedding
            For multiple texts: List of lists of floats, one embedding per text
        """
        if isinstance(texts, str):
            texts = [texts]
            
        all_embeddings = []
        
        # Process in batches to avoid API limits
        for i in range(0, len(texts), batch_size):
            batch = texts[i:i + batch_size]
            
            try:
                response = self.client.embeddings.create(
                    model=self.model,
                    input=batch
                )
                
                batch_embeddings = [data.embedding for data in response.data]
                all_embeddings.extend(batch_embeddings)
                
            except Exception as e:
                logger.error(f"Error generating embeddings for batch {i//batch_size + 1}: {str(e)}")
                raise
                
        return all_embeddings[0] if len(texts) == 1 else all_embeddings 