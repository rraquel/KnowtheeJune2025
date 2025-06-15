-- unified vector storage for docs/profiles/etc
CREATE TABLE document_embeddings (
  id          UUID    PRIMARY KEY DEFAULT uuid_generate_v4(),
  employee_id UUID    REFERENCES employees(id) ON DELETE CASCADE,
  doc_type    VARCHAR(50) NOT NULL,        -- 'leadership','profile','document'
  document_id VARCHAR(100) NOT NULL,
  content     TEXT    NOT NULL,
  embedding   vector(1536) NOT NULL,
  metadata    JSONB,
  tenant_id   VARCHAR(36) NOT NULL,
  created_at  TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  UNIQUE(doc_type, document_id)
);

CREATE INDEX idx_embeddings_employee ON document_embeddings(employee_id);
CREATE INDEX idx_embeddings_vector ON document_embeddings USING ivfflat(embedding);
