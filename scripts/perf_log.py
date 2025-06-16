#!/usr/bin/env python3
import os
import json
import logging
import time
from pathlib import Path
from typing import Dict, Any, List
from collections import defaultdict
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

load_dotenv()

def load_documents(data_dir: Path) -> List[Dict[str, Any]]:
    """Load all documents from the data directory."""
    documents = []
    
    # Load CVs
    cv_dir = data_dir / "cvs"
    if cv_dir.exists():
        for cv_file in cv_dir.glob("*.json"):
            with open(cv_file) as f:
                doc = json.load(f)
                doc['metadata']['type'] = 'cv'
                documents.append(doc)
    
    # Load assessments
    assessment_dir = data_dir / "assessments"
    if assessment_dir.exists():
        for assessment_file in assessment_dir.glob("*.json"):
            with open(assessment_file) as f:
                doc = json.load(f)
                doc['metadata']['type'] = 'assessment'
                documents.append(doc)
    
    return documents

def process_batch(documents: List[Dict[str, Any]], pipeline: DocumentPipeline) -> Dict[str, Any]:
    """Process a batch of documents and collect performance metrics."""
    metrics = defaultdict(list)
    total_start = time.time()
    
    for doc in documents:
        try:
            # Process document
            doc_start = time.time()
            doc_id = pipeline.process(doc)
            doc_time = time.time() - doc_start
            
            # Collect metrics
            doc_type = doc['metadata']['type']
            metrics['total_time'].append(doc_time)
            metrics['doc_type'].append(doc_type)
            metrics['doc_id'].append(doc_id)
            
            logger.info(f"Processed {doc_type} {doc_id} in {doc_time:.2f}s")
            
        except Exception as e:
            logger.error(f"Error processing document: {e}")
            metrics['errors'].append(str(e))
    
    # Calculate summary statistics
    total_time = time.time() - total_start
    metrics['summary'] = {
        'total_documents': len(documents),
        'total_time': total_time,
        'avg_time_per_doc': total_time / len(documents) if documents else 0,
        'doc_types': {
            'cv': metrics['doc_type'].count('cv'),
            'assessment': metrics['doc_type'].count('assessment')
        }
    }
    
    return metrics

def main():
    """Main function to process documents and log performance."""
    # Initialize components
    chunker = SectionChunker()
    embedder = OpenAIEmbedder(api_key=os.environ.get("OPENAI_API_KEY"))
    storage = PostgresVectorStore()
    
    # Initialize pipeline
    pipeline = DocumentPipeline(chunker, embedder, storage)
    
    # Load documents
    data_dir = Path(__file__).parent.parent / "backend" / "data" / "processed"
    documents = load_documents(data_dir)
    
    logger.info(f"Loaded {len(documents)} documents")
    
    # Process batch
    metrics = process_batch(documents, pipeline)
    
    # Log summary
    logger.info("Performance Summary:")
    logger.info(f"Total documents processed: {metrics['summary']['total_documents']}")
    logger.info(f"Total processing time: {metrics['summary']['total_time']:.2f}s")
    logger.info(f"Average time per document: {metrics['summary']['avg_time_per_doc']:.2f}s")
    logger.info("Document types:")
    for doc_type, count in metrics['summary']['doc_types'].items():
        logger.info(f"  {doc_type}: {count}")
    
    if metrics['errors']:
        logger.warning(f"Encountered {len(metrics['errors'])} errors during processing")

if __name__ == '__main__':
    main() 