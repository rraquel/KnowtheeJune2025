"""Vector service package."""

import os
from .chunkers import BaseChunker, SectionChunker
from .embedders import BaseEmbedder, OpenAIEmbedder
from .storage import PostgresVectorStore
from .pipeline import DocumentPipeline
from .evaluator import EmbeddingEvaluator
from .summarizer import SummaryGenerator

# For backward compatibility
from .chunkers.section import SectionChunker as TextChunker

# Initialize components with environment variables
api_key = os.environ.get("OPENAI_API_KEY")
if not api_key:
    raise ValueError("OPENAI_API_KEY environment variable must be set")

default_embedder = OpenAIEmbedder(api_key=api_key)
default_chunker = SectionChunker()
default_storage = PostgresVectorStore()

# Create default pipeline
default_pipeline = DocumentPipeline(
    chunker=default_chunker,
    embedder=default_embedder,
    storage=default_storage
)

# Expose backward-compatible functions
def chunk_text(text: str):
    """Split text into chunks respecting token limits."""
    return default_chunker.chunk(text)

__all__ = [
    'BaseChunker',
    'SectionChunker',
    'BaseEmbedder',
    'OpenAIEmbedder',
    'PostgresVectorStore',
    'DocumentPipeline',
    'TextChunker',  # For backward compatibility
    'chunk_text',    # For backward compatibility
    'EmbeddingEvaluator',
    'SummaryGenerator',
    'default_pipeline'
] 