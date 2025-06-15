-- allow multiple contact methods per employee
CREATE TABLE employee_contacts (
  id          UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  employee_id UUID NOT NULL REFERENCES employees(id) ON DELETE CASCADE,
  type        VARCHAR(20) NOT NULL CHECK (type IN ('email', 'phone', 'linkedin', 'other')),
  value       TEXT NOT NULL,
  created_at  TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  updated_at  TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  UNIQUE(employee_id, type, value)
);

CREATE INDEX idx_contacts_employee ON employee_contacts(employee_id);

-- record education history
CREATE TABLE employee_education (
  id            UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  employee_id   UUID NOT NULL REFERENCES employees(id) ON DELETE CASCADE,
  institution   VARCHAR(200),
  degree        TEXT,
  field_of_study VARCHAR(200),
  start_date    DATE,
  end_date      DATE,
  gpa           NUMERIC(3,2),
  created_at    TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  updated_at    TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  UNIQUE(employee_id, institution, degree)
);

CREATE INDEX idx_education_employee ON employee_education(employee_id);
