from dotenv import load_dotenv
load_dotenv()
import unittest
from unittest.mock import patch, MagicMock
import numpy as np
from backend.ingestion.vector.embedders import BaseEmbedder, OpenAIEmbedder

class TestBaseEmbedder(unittest.TestCase):
    def test_abstract_methods(self):
        """Test that BaseEmbedder is abstract."""
        with self.assertRaises(TypeError):
            BaseEmbedder()

class TestOpenAIEmbedder(unittest.TestCase):
    def setUp(self):
        """Set up test fixtures."""
        # Create a mock response
        self.mock_embedding = np.random.rand(1536)
        self.mock_embedding = self.mock_embedding / np.linalg.norm(self.mock_embedding)
        
        self.mock_response = MagicMock()
        self.mock_response.data = [MagicMock(embedding=self.mock_embedding.tolist())]
        
        # Create a mock client
        self.mock_client = MagicMock()
        self.mock_client.embeddings.create.return_value = self.mock_response
        
        # Patch the OpenAI client
        self.patcher = patch('openai.OpenAI', return_value=self.mock_client)
        self.mock_openai = self.patcher.start()
        
        # Initialize the embedder
        self.embedder = OpenAIEmbedder(api_key="dummy_key")

    def tearDown(self):
        """Clean up test fixtures."""
        self.patcher.stop()

    def test_embed_single_text(self):
        """Test embedding a single text."""
        text = "This is a test"
        embedding = self.embedder.embed(text)
        
        # Verify OpenAI client was called correctly
        self.mock_client.embeddings.create.assert_called_once()
        call_args = self.mock_client.embeddings.create.call_args[1]
        self.assertEqual(call_args['input'], [text])
        self.assertEqual(call_args['model'], 'text-embedding-3-small')
        
        # Verify embedding shape and type
        self.assertEqual(embedding.shape, (1536,))
        self.assertTrue(isinstance(embedding, np.ndarray))

    def test_embed_multiple_texts(self):
        """Test embedding multiple texts."""
        texts = ["Text 1", "Text 2"]
        embeddings = self.embedder.embed(texts)
        
        # Verify OpenAI client was called correctly
        self.mock_client.embeddings.create.assert_called_once()
        call_args = self.mock_client.embeddings.create.call_args[1]
        self.assertEqual(call_args['input'], texts)
        
        # Verify embeddings shape and type
        self.assertEqual(embeddings.shape, (2, 1536))
        self.assertTrue(isinstance(embeddings, np.ndarray))

    def test_embed_empty_text(self):
        """Test embedding empty text."""
        text = ""
        embedding = self.embedder.embed(text)
        
        # Verify OpenAI client was called
        self.mock_client.embeddings.create.assert_called_once()
        
        # Verify embedding shape and type
        self.assertEqual(embedding.shape, (1536,))
        self.assertTrue(isinstance(embedding, np.ndarray))

    def test_embed_long_text(self):
        """Test embedding long text that exceeds token limit."""
        # Create a long text that would exceed the token limit
        text = "test " * 10000
        
        # Mock the tokenizer to simulate token limit
        with patch('tiktoken.get_encoding') as mock_get_encoding:
            mock_encoding = MagicMock()
            mock_encoding.encode.return_value = [1] * 8192  # Simulate max tokens
            mock_get_encoding.return_value = mock_encoding
            
            embedding = self.embedder.embed(text)
            
            # Verify OpenAI client was called
            self.mock_client.embeddings.create.assert_called_once()
            
            # Verify embedding shape and type
            self.assertEqual(embedding.shape, (1536,))
            self.assertTrue(isinstance(embedding, np.ndarray))

    def test_embed_error_handling(self):
        """Test error handling during embedding."""
        # Mock an API error
        self.mock_client.embeddings.create.side_effect = Exception("API Error")
        
        with self.assertRaises(Exception):
            self.embedder.embed("test")

    def test_embedding_normalization(self):
        """Test that embeddings are normalized."""
        text = "This is a test"
        embedding = self.embedder.embed(text)
        norm = np.linalg.norm(embedding)
        self.assertAlmostEqual(norm, 1.0, places=6)

if __name__ == '__main__':
    unittest.main() 