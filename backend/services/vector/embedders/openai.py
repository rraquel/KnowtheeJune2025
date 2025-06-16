from dotenv import load_dotenv
load_dotenv()
import os
import numpy as np
import openai
from typing import List, Dict, Any, Union
from .base import BaseEmbedder

class OpenAIEmbedder(BaseEmbedder):
    """OpenAI text embedding model."""
    
    def __init__(self, api_key=None, model="text-embedding-3-small"):
        """
        Initialize OpenAI embedder.
        
        Args:
            api_key: OpenAI API key (defaults to OPENAI_API_KEY env var)
            model: OpenAI embedding model to use
        """
        if api_key is None:
            api_key = os.getenv("OPENAI_API_KEY")
        if not api_key:
            raise ValueError("OPENAI_API_KEY must be set in the environment or passed explicitly.")
        self.api_key = api_key
        self.model = model
        self.client = openai.OpenAI(api_key=self.api_key)
    
    def embed(self, texts: Union[str, List[str]]) -> np.ndarray:
        """Get embeddings for one or more texts."""
        if isinstance(texts, str):
            texts = [texts]
        
        # Get embeddings from OpenAI
        response = self.client.embeddings.create(
            model=self.model,
            input=texts
        )
        
        # Convert to numpy array
        embeddings = np.array([data.embedding for data in response.data])
        
        # Normalize embeddings
        norms = np.linalg.norm(embeddings, axis=1, keepdims=True)
        embeddings = embeddings / norms
        
        return embeddings
        
        # Process results
        results = []
        for i, item in enumerate(response["data"]):
            results.append({
                "text": texts[i],
                "embedding": item["embedding"],
                "metadata": {
                    "model": self.model,
                    "index": i
                }
            })
        
        return results 