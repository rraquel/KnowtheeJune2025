-- Drop existing document_embeddings table if it exists
DROP TABLE IF EXISTS document_embeddings;

-- Create embedding_runs table
CREATE TABLE embedding_runs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name TEXT NOT NULL,
    chunking_method TEXT NOT NULL,
    embedding_model TEXT NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Create embedding_documents table
CREATE TABLE embedding_documents (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    employee_id UUID NOT NULL REFERENCES employees(id) ON DELETE CASCADE,
    assessment_id UUID REFERENCES employee_assessments(id) ON DELETE SET NULL,
    embedding_run_id UUID NOT NULL REFERENCES embedding_runs(id) ON DELETE CASCADE,
    type TEXT NOT NULL,  -- 'CV', 'IDI', 'Hogan'
    filename TEXT NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Create embedding_chunks table
CREATE TABLE embedding_chunks (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    document_id UUID NOT NULL REFERENCES embedding_documents(id) ON DELETE CASCADE,
    chunk_index INTEGER NOT NULL,
    content TEXT NOT NULL,
    embedding VECTOR(1536) NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Create indexes
CREATE INDEX idx_embedding_docs_employee ON embedding_documents(employee_id);
CREATE INDEX idx_embedding_docs_assessment ON embedding_documents(assessment_id);
CREATE INDEX idx_embedding_docs_run ON embedding_documents(embedding_run_id);
CREATE INDEX idx_embedding_chunks_doc ON embedding_chunks(document_id);
CREATE INDEX idx_embedding_chunks_vector ON embedding_chunks USING ivfflat(embedding);
