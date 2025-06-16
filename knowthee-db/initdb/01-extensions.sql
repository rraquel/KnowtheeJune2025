-- knowthee-db/initdb/02-schema.sql

-- Enable required extensions
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "vector";
CREATE EXTENSION IF NOT EXISTS "pg_trgm";

-- Create employees table
CREATE TABLE employees (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    full_name TEXT NOT NULL,
    email TEXT,
    location TEXT,
    current_position TEXT,
    department TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Create employee_contacts table
CREATE TABLE employee_contacts (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    employee_id UUID NOT NULL REFERENCES employees(id) ON DELETE CASCADE,
    type TEXT NOT NULL CHECK (type IN ('email', 'phone', 'linkedin', 'other')),
    value TEXT NOT NULL,
    is_primary BOOLEAN DEFAULT false,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(employee_id, type, value)
);

-- Create employee_education table
CREATE TABLE employee_education (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    employee_id UUID NOT NULL REFERENCES employees(id) ON DELETE CASCADE,
    degree TEXT NOT NULL,
    field TEXT,
    institution TEXT NOT NULL,
    start_date DATE,
    end_date DATE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Create employee_experiences table
CREATE TABLE employee_experiences (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    employee_id UUID NOT NULL REFERENCES employees(id) ON DELETE CASCADE,
    title TEXT NOT NULL,
    company TEXT NOT NULL,
    start_date DATE,
    end_date DATE,
    description TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Create employee_skills table
CREATE TABLE employee_skills (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    employee_id UUID NOT NULL REFERENCES employees(id) ON DELETE CASCADE,
    skill TEXT NOT NULL,
    type TEXT NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Create employee_assessments table
CREATE TABLE employee_assessments (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    employee_id UUID NOT NULL REFERENCES employees(id) ON DELETE CASCADE,
    assessment_type TEXT NOT NULL,
    assessment_date DATE NOT NULL,
    source_filename TEXT NOT NULL,
    status TEXT NOT NULL DEFAULT 'active',
    notes TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Create idi_scores table
CREATE TABLE idi_scores (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    assessment_id UUID NOT NULL REFERENCES employee_assessments(id) ON DELETE CASCADE,
    category TEXT NOT NULL,
    dimension TEXT NOT NULL,
    score INTEGER NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Create hogan_scores table
CREATE TABLE hogan_scores (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    assessment_id UUID NOT NULL REFERENCES employee_assessments(id) ON DELETE CASCADE,
    trait TEXT NOT NULL,
    score INTEGER NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Create embedding_runs table
CREATE TABLE embedding_runs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name TEXT NOT NULL,
    chunking_method TEXT,
    embedding_model TEXT,
    run_parameters JSONB,  -- Stores chunk size, overlap, etc.
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Create embedding_documents table
CREATE TABLE embedding_documents (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    employee_id UUID NOT NULL REFERENCES employees(id) ON DELETE CASCADE,
    embedding_run_id UUID NOT NULL REFERENCES embedding_runs(id) ON DELETE CASCADE,
    
    document_type TEXT NOT NULL CHECK (document_type IN ('cv', 'assessment', 'summary', 'json', 'other')),
    source_filename TEXT NOT NULL,
    title TEXT,
    
    document_id UUID,  -- Optional: links to original document
    document_origin TEXT,  -- Optional: e.g. 'assessment_source', 'cv_import', 'json_upload'
    
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    
    -- Add unique constraint to prevent duplicate processing
    CONSTRAINT uix_source_run UNIQUE (source_filename, embedding_run_id)
);

-- Create embedding_chunks table
CREATE TABLE embedding_chunks (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    document_id UUID NOT NULL REFERENCES embedding_documents(id) ON DELETE CASCADE,
    chunk_index INTEGER NOT NULL,
    
    content TEXT NOT NULL,
    embedding VECTOR(1536) NOT NULL,
    
    token_count INTEGER,
    char_count INTEGER,
    chunk_label TEXT,  -- Optional: e.g. 'header', 'conclusion'
    score FLOAT,  -- Optional: for ranking in RAG
    
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Create indexes
CREATE INDEX idx_embedding_docs_employee ON embedding_documents(employee_id);
CREATE INDEX idx_embedding_docs_run ON embedding_documents(embedding_run_id);
CREATE INDEX idx_embedding_docs_type ON embedding_documents(document_type);
CREATE INDEX idx_embedding_chunks_doc ON embedding_chunks(document_id);
CREATE INDEX idx_embedding_chunks_vector ON embedding_chunks USING ivfflat(embedding);
