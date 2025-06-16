from sqlalchemy import Column, String, Integer, JSON, Float
from sqlalchemy.dialects.postgresql import ARRAY
from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()

class DocumentEmbedding(Base):
    """SQLAlchemy model for document embeddings."""
    __tablename__ = 'document_embeddings'

    id = Column(Integer, primary_key=True)
    document_id = Column(String, nullable=False, index=True)
    chunk_index = Column(Integer, nullable=False)
    embedding = Column(ARRAY(Float), nullable=False)
    doc_metadata = Column(JSON, nullable=True)

    def __repr__(self):
        return f"<DocumentEmbedding(document_id='{self.document_id}', chunk_index={self.chunk_index})>" 