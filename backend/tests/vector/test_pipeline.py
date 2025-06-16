import os
import json
import logging
import time
from pathlib import Path
from typing import Dict, Any
import unittest
from unittest.mock import patch
from dotenv import load_dotenv

from backend.services.vector.pipeline import DocumentPipeline
from backend.services.vector.chunkers import SectionChunker
from backend.services.vector.embedders import OpenAIEmbedder
from backend.services.vector.storage import PostgresVectorStore

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

load_dotenv()

class TestDocumentPipeline(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        """Set up test fixtures."""
        # Initialize real components
        cls.chunker = SectionChunker()
        cls.embedder = OpenAIEmbedder(api_key=os.environ.get("OPENAI_API_KEY"))
        cls.storage = PostgresVectorStore()
        
        # Initialize pipeline
        cls.pipeline = DocumentPipeline(
            chunker=cls.chunker,
            embedder=cls.embedder,
            storage=cls.storage
        )
        
        # Load test data
        data_dir = Path(__file__).parent.parent.parent / "data" / "processed"
        cls.test_files = {
            'cv': data_dir / "cv_sample.json",
            'assessment': data_dir / "assessment_sample.json"
        }
    
    def test_process_cv(self):
        """Test processing a CV document from file."""
        # Load CV data
        with open(self.test_files['cv']) as f:
            cv_data = json.load(f)
        
        # Process document
        start_time = time.time()
        result = self.pipeline.process(cv_data)
        process_time = time.time() - start_time
        
        # Log performance metrics
        logger.info(f"CV Processing Time: {process_time:.2f}s")
        logger.info(f"Document ID: {result}")
        
        # Verify result
        self.assertIsNotNone(result)
        self.assertIsInstance(result, str)
    
    def test_process_assessment(self):
        """Test processing an assessment document from file."""
        # Load assessment data
        with open(self.test_files['assessment']) as f:
            assessment_data = json.load(f)
        
        # Process document
        start_time = time.time()
        result = self.pipeline.process(assessment_data)
        process_time = time.time() - start_time
        
        # Log performance metrics
        logger.info(f"Assessment Processing Time: {process_time:.2f}s")
        logger.info(f"Document ID: {result}")
        
        # Verify result
        self.assertIsNotNone(result)
        self.assertIsInstance(result, str)
    
    def test_process_with_invalid_data(self):
        """Test processing invalid document data."""
        invalid_data = {
            'text': 'Invalid document',
            'metadata': {
                'type': 'invalid',
                'id': 'test_1'
            }
        }
        
        with self.assertRaises(ValueError):
            self.pipeline.process(invalid_data)
    
    def test_process_with_missing_metadata(self):
        """Test processing document with missing metadata."""
        invalid_data = {
            'text': 'Document without metadata'
        }
        
        with self.assertRaises(ValueError):
            self.pipeline.process(invalid_data)

if __name__ == '__main__':
    unittest.main() 