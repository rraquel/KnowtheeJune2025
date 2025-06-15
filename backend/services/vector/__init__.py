from .chunker import TextChunker

# Create singleton instance
chunker = TextChunker()
 
def chunk_text(text: str):
    """Split text into chunks respecting token limits."""
    return chunker.chunk_text(text) 