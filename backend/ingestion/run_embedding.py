import os
import argparse
import logging
from pathlib import Path
from contextlib import contextmanager

from backend.db.session import get_db
from backend.ingestion.embedding.pipeline import EmbeddingPipeline

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def main():
    parser = argparse.ArgumentParser(description='Run the embedding pipeline')
    parser.add_argument('--input-dir', type=str, required=True,
                      help='Directory containing documents to process')
    parser.add_argument('--model', type=str, default='text-embedding-3-small',
                      help='OpenAI embedding model to use')
    args = parser.parse_args()
    
    # Validate input directory
    input_dir = Path(args.input_dir)
    if not input_dir.exists():
        logger.error(f"Input directory does not exist: {args.input_dir}")
        return
        
    # Process documents
    with get_db() as db:
        try:
            pipeline = EmbeddingPipeline(db, embedding_model=args.model)
            pipeline.process_directory(str(input_dir))
            logger.info("Pipeline completed successfully")
        except Exception as e:
            logger.error(f"Pipeline failed: {str(e)}")
            raise

if __name__ == '__main__':
    main() 