import logging
import time
from typing import List, Dict, Any
from datetime import datetime
from .chunkers.base import BaseChunker
from .embedders.base import BaseEmbedder
from .storage.postgres import PostgresVectorStore
from .summarizer import SummaryGenerator

logger = logging.getLogger(__name__)

class DocumentPipeline:
    """Orchestrates the document processing pipeline: chunk → embed → store."""
    
    def __init__(
        self,
        chunker: BaseChunker,
        embedder: BaseEmbedder,
        storage: PostgresVectorStore
    ):
        """
        Initialize pipeline with components.
        
        Args:
            chunker: Text chunking strategy
            embedder: Text embedding strategy
            storage: Vector storage backend
        """
        self.chunker = chunker
        self.embedder = embedder
        self.storage = storage
        self.summarizer = SummaryGenerator()
    
    def _validate_metadata(self, metadata: Dict[str, Any], required_fields: List[str]) -> bool:
        """
        Validate required metadata fields.
        
        Args:
            metadata: Document metadata
            required_fields: List of required field names
            
        Returns:
            True if all required fields are present and valid
        """
        if not metadata:
            logger.error("No metadata provided")
            return False
            
        missing_fields = [field for field in required_fields if field not in metadata]
        if missing_fields:
            logger.error(f"Missing required metadata fields: {missing_fields}")
            return False
            
        return True
    
    def _generate_document_id(self, metadata: Dict[str, Any]) -> str:
        """
        Generate a unique document ID.
        
        Args:
            metadata: Document metadata
            
        Returns:
            Unique document ID string
        """
        employee_id = metadata.get("employee_id")
        doc_type = metadata.get("doc_type")
        
        if not employee_id or not doc_type:
            raise ValueError("employee_id and doc_type are required for document_id generation")
        
        # For assessments, include assessment date
        if doc_type in ["hogan", "idi"]:
            assessment_date = metadata.get("assessment_date")
            if not assessment_date:
                raise ValueError("assessment_date is required for assessment documents")
            return f"{employee_id}_{doc_type}_{assessment_date}"
        
        # For CVs and other documents, use timestamp
        timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
        return f"{employee_id}_{doc_type}_{timestamp}"
    
    def process(self, text: str, metadata: Dict[str, Any] = None) -> List[Dict[str, Any]]:
        """
        Process a document through the pipeline.
        
        Args:
            text: Document text to process
            metadata: Optional metadata to attach to chunks and embeddings
            
        Returns:
            List of dictionaries containing processed chunks with embeddings
        """
        if not metadata:
            metadata = {}
            
        # Validate required metadata
        if not self._validate_metadata(metadata, ["employee_id", "doc_type"]):
            return []
            
        # Generate unique document ID
        try:
            document_id = self._generate_document_id(metadata)
            metadata["document_id"] = document_id
        except ValueError as e:
            logger.error(f"Failed to generate document ID: {e}")
            return []
            
        # Start timing
        start_time = time.time()
        
        # 1. Chunk the text
        chunk_start = time.time()
        chunks = self.chunker.chunk(text, metadata)
        chunk_time = time.time() - chunk_start
        
        # 2. Generate embeddings for chunks
        embed_start = time.time()
        texts = [chunk["text"] for chunk in chunks]
        chunk_metadata = [chunk["metadata"] for chunk in chunks]
        
        # Log embedding model
        logger.info(f"Using embedding model: {self.embedder.model}")
        
        embeddings = self.embedder.embed(texts, metadata)
        embed_time = time.time() - embed_start
        
        # 3. Store in vector database
        store_start = time.time()
        results = []
        for i, embedding in enumerate(embeddings):
            # Merge chunk metadata with embedding metadata
            combined_metadata = {
                **chunk_metadata[i],
                **embedding["metadata"]
            }
            
            # Store in database
            doc_id = self.storage.store(
                text=embedding["text"],
                embedding=embedding["embedding"],
                metadata=combined_metadata
            )
            
            results.append({
                "id": doc_id,
                "text": embedding["text"],
                "embedding": embedding["embedding"],
                "metadata": combined_metadata
            })
        
        store_time = time.time() - store_start
        
        # Log performance metrics
        total_time = time.time() - start_time
        logger.info(f"Pipeline Performance:")
        logger.info(f"  Total time: {total_time:.2f}s")
        logger.info(f"  Chunking time: {chunk_time:.2f}s ({len(chunks)} chunks)")
        logger.info(f"  Embedding time: {embed_time:.2f}s")
        logger.info(f"  Storage time: {store_time:.2f}s")
        logger.info(f"  Document type: {metadata.get('doc_type')}")
        logger.info(f"  Document ID: {doc_id}")
        
        return results
    
    def process_cv(self, cv_data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Process CV data through the pipeline.
        
        Args:
            cv_data: Parsed CV data
            
        Returns:
            List of dictionaries containing processed chunks with embeddings
        """
        if not isinstance(self.chunker, SectionChunker):
            raise ValueError("CV processing requires SectionChunker")
            
        # Validate required metadata
        if not self._validate_metadata(cv_data, ["employee_id"]):
            return []
            
        # Get chunks from specialized CV chunking
        chunks = self.chunker.chunk_cv(cv_data)
        
        # Process each chunk
        results = []
        for chunk in chunks:
            chunk_results = self.process(chunk["text"], chunk["metadata"])
            results.extend(chunk_results)
        
        return results
    
    def process_assessment(
        self,
        assessment_data: Dict[str, Any],
        use_summary: bool = False
    ) -> List[Dict[str, Any]]:
        """
        Process assessment data through the pipeline.
        
        Args:
            assessment_data: Parsed assessment data
            use_summary: Whether to generate and use a summary
            
        Returns:
            List of dictionaries containing processed chunks with embeddings
        """
        if not isinstance(self.chunker, SectionChunker):
            raise ValueError("Assessment processing requires SectionChunker")
        
        # Validate required metadata
        required_fields = ["employee_id", "assessment_type", "assessment_date"]
        if not self._validate_metadata(assessment_data, required_fields):
            return []
        
        results = []
        
        # Generate and process summary if requested
        if use_summary:
            # Get assessment type and scores
            assessment_type = assessment_data.get("type", "").lower()
            scores = assessment_data.get("scores", {})
            
            if not scores:
                logger.error("No scores found in assessment data")
                return []
            
            # Generate summary based on assessment type
            try:
                if assessment_type == "hogan":
                    summary = self.summarizer.summarize_hogan(scores)
                elif assessment_type == "idi":
                    summary = self.summarizer.summarize_idi(scores)
                else:
                    logger.error(f"Unsupported assessment type: {assessment_type}")
                    return []
            except Exception as e:
                logger.error(f"Failed to generate summary: {e}")
                return []
            
            # Process summary as a single chunk
            summary_metadata = {
                "employee_id": assessment_data.get("employee_id"),
                "doc_type": "assessment_summary",
                "document_id": self._generate_document_id({
                    "employee_id": assessment_data.get("employee_id"),
                    "doc_type": "assessment_summary",
                    "assessment_date": assessment_data.get("assessment_date")
                }),
                "assessment_type": assessment_type,
                "assessment_date": assessment_data.get("assessment_date"),
                "source_filename": assessment_data.get("source_filename")
            }
            
            summary_results = self.process(summary, summary_metadata)
            results.extend(summary_results)
        
        # Process detailed chunks
        chunks = self.chunker.chunk_assessment(assessment_data)
        for chunk in chunks:
            chunk_results = self.process(chunk["text"], chunk["metadata"])
            results.extend(chunk_results)
        
        return results 