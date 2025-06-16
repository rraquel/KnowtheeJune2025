from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
import os
from dotenv import load_dotenv
import logging

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Database connection
DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://postgres:postgres@postgres:5432/knowthee")
engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def init_db():
    """Initialize the database with all required tables."""
    try:
        # Create tables
        with engine.connect() as connection:
            # Create employees table
            connection.execute(text("""
                CREATE TABLE IF NOT EXISTS employees (
                    id SERIAL PRIMARY KEY,
                    name VARCHAR(255) NOT NULL,
                    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
                );
            """))
            
            # Create embedding_runs table
            connection.execute(text("""
                CREATE TABLE IF NOT EXISTS embedding_runs (
                    id UUID PRIMARY KEY,
                    name VARCHAR(255) NOT NULL,
                    chunking_method VARCHAR(50) NOT NULL,
                    embedding_model VARCHAR(50) NOT NULL,
                    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
                );
            """))
            
            # Create embedding_documents table
            connection.execute(text("""
                CREATE TABLE IF NOT EXISTS embedding_documents (
                    id UUID PRIMARY KEY,
                    employee_id INTEGER REFERENCES employees(id),
                    embedding_run_id UUID REFERENCES embedding_runs(id),
                    document_type VARCHAR(50) NOT NULL,
                    source_filename VARCHAR(255) NOT NULL,
                    title VARCHAR(255),
                    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
                    CONSTRAINT valid_document_type CHECK (document_type IN ('CV', 'IDI', 'HOGAN', 'SUMMARY'))
                );
            """))
            
            # Create embedding_chunks table
            connection.execute(text("""
                CREATE TABLE IF NOT EXISTS embedding_chunks (
                    id UUID PRIMARY KEY,
                    document_id UUID REFERENCES embedding_documents(id),
                    chunk_index INTEGER NOT NULL,
                    content TEXT NOT NULL,
                    embedding vector(1536),
                    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
                );
            """))
            
            connection.commit()
            logger.info("Database initialized successfully!")
            
    except Exception as e:
        logger.error(f"Error initializing database: {str(e)}")
        raise

if __name__ == "__main__":
    init_db() 