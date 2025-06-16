#!/usr/bin/env python3
import os
import json
import logging
from pathlib import Path
from typing import Dict, Any, List
from dotenv import load_dotenv

from backend.ingestion.vector.pipeline import DocumentPipeline
from backend.ingestion.vector.chunkers import SectionChunker
from backend.ingestion.vector.embedders import OpenAIEmbedder
from backend.ingestion.vector.storage import PostgresVectorStore

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def load_document(file_path: Path) -> Dict[str, Any]:
    """Load a single document from file."""
    with open(file_path) as f:
        return json.load(f)

def analyze_chunks(chunks: List[Dict[str, Any]]) -> None:
    """Analyze and print information about chunks."""
    logger.info(f"\nTotal chunks: {len(chunks)}")
    
    # Print first chunk as example
    if chunks:
        logger.info("\nExample chunk:")
        logger.info(f"Text length: {len(chunks[0]['text'])}")
        logger.info(f"Metadata: {chunks[0]['metadata']}")
        logger.info(f"Text preview: {chunks[0]['text'][:200]}...")

def main():
    """Run the pipeline on sample documents."""
    # Load environment variables
    load_dotenv()
    
    # Initialize components
    chunker = SectionChunker()
    embedder = OpenAIEmbedder()  # Will use OPENAI_API_KEY from env
    storage = PostgresVectorStore()
    
    # Initialize pipeline
    pipeline = DocumentPipeline(chunker, embedder, storage)
    
    # Process CV
    cv_path = Path("backend/data/processed/cv_sample.json")
    if cv_path.exists():
        logger.info("\nProcessing CV...")
        cv_data = load_document(cv_path)
        chunks = chunker.chunk(cv_data["text"], cv_data["metadata"])
        analyze_chunks(chunks)
        results = pipeline.process(cv_data["text"], cv_data["metadata"])
        logger.info(f"Stored {len(results)} CV embeddings")
    
    # Process Assessment
    assessment_path = Path("backend/data/processed/assessment_sample.json")
    if assessment_path.exists():
        logger.info("\nProcessing Assessment...")
        assessment_data = load_document(assessment_path)
        chunks = chunker.chunk(assessment_data["text"], assessment_data["metadata"])
        analyze_chunks(chunks)
        results = pipeline.process(assessment_data["text"], assessment_data["metadata"])
        logger.info(f"Stored {len(results)} Assessment embeddings")

if __name__ == "__main__":
    main() 