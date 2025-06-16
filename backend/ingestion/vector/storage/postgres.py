from typing import List, Dict, Any
import uuid
from sqlalchemy.orm import Session
from backend.services.db.session import SessionLocal
from backend.services.db.models import DocumentEmbedding

class PostgresVectorStore:
    """PostgreSQL vector storage implementation using pgvector."""
    
    def __init__(self, session: Session = None):
        """
        Initialize PostgreSQL vector store.
        
        Args:
            session: Optional SQLAlchemy session (creates new one if not provided)
        """
        self.session = session or SessionLocal()
    
    def store(
        self,
        text: str,
        embedding: List[float],
        metadata: Dict[str, Any]
    ) -> str:
        """
        Store a document embedding in the database.
        
        Args:
            text: Document text
            embedding: Vector embedding
            metadata: Document metadata
            
        Returns:
            Document ID
        """
        # Create document embedding record
        doc = DocumentEmbedding(
            id=uuid.uuid4(),
            employee_id=metadata.get("employee_id"),
            source=metadata.get("doc_type", "document"),
            embedding=embedding,
            content=text,
            metadata=metadata
        )
        
        # Save to database
        self.session.add(doc)
        self.session.commit()
        
        return str(doc.id)
    
    def search(
        self,
        query_embedding: List[float],
        k: int = 5,
        filters: Dict[str, Any] = None
    ) -> List[Dict[str, Any]]:
        """
        Search for similar documents.
        
        Args:
            query_embedding: Query vector
            k: Number of results to return
            filters: Optional metadata filters
            
        Returns:
            List of matching documents with scores
        """
        # Build base query
        query = self.session.query(DocumentEmbedding)
        
        # Apply filters if provided
        if filters:
            for key, value in filters.items():
                query = query.filter(DocumentEmbedding.metadata[key].astext == str(value))
        
        # Add vector similarity search
        query = query.order_by(DocumentEmbedding.embedding.cosine_distance(query_embedding))
        
        # Get top k results
        results = query.limit(k).all()
        
        # Format results
        return [{
            "id": str(doc.id),
            "text": doc.content,
            "metadata": doc.metadata,
            "score": 1 - doc.embedding.cosine_distance(query_embedding)
        } for doc in results]
    
    def close(self):
        """Close the database session."""
        if self.session:
            self.session.close() 