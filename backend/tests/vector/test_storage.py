from dotenv import load_dotenv
load_dotenv()
import unittest
import numpy as np
from backend.ingestion.vector.storage import PostgresVectorStore
from backend.ingestion.vector.models import DocumentEmbedding

class TestPostgresVectorStore(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        """Set up test fixtures."""
        cls.store = PostgresVectorStore()
        
        # Create test data
        cls.test_embedding = np.random.rand(1536)
        cls.test_embedding = cls.test_embedding / np.linalg.norm(cls.test_embedding)
        
        cls.test_metadata = {
            'type': 'test',
            'employee_id': 'test_1',
            'doc_type': 'test_doc'
        }
    
    def test_store_and_search(self):
        """Test storing and searching embeddings."""
        # Store test document
        doc_id = self.store.store(
            document_id='test_1',
            embedding=self.test_embedding,
            metadata=self.test_metadata
        )
        
        # Search for similar documents
        results = self.store.search(
            query_embedding=self.test_embedding,
            limit=1
        )
        
        # Verify results
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0]['document_id'], 'test_1')
        self.assertEqual(results[0]['metadata']['type'], 'test')
    
    def test_metadata_filtering(self):
        """Test searching with metadata filters."""
        # Store test document
        self.store.store(
            document_id='test_2',
            embedding=self.test_embedding,
            metadata={
                'type': 'test',
                'employee_id': 'test_2',
                'doc_type': 'test_doc'
            }
        )
        
        # Search with metadata filter
        results = self.store.search(
            query_embedding=self.test_embedding,
            metadata_filter={'type': 'test'},
            limit=2
        )
        
        # Verify results
        self.assertEqual(len(results), 2)
        for result in results:
            self.assertEqual(result['metadata']['type'], 'test')
    
    def test_delete(self):
        """Test deleting documents."""
        # Store test document
        doc_id = self.store.store(
            document_id='test_3',
            embedding=self.test_embedding,
            metadata=self.test_metadata
        )
        
        # Delete document
        self.store.delete(doc_id)
        
        # Verify document is deleted
        results = self.store.search(
            query_embedding=self.test_embedding,
            metadata_filter={'document_id': 'test_3'},
            limit=1
        )
        self.assertEqual(len(results), 0)

if __name__ == '__main__':
    unittest.main() 