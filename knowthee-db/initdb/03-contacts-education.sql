-- allow multiple contact methods per employee
CREATE TABLE employee_contacts (
  id          UUID    PRIMARY KEY DEFAULT uuid_generate_v4(),
  employee_id UUID    NOT NULL REFERENCES employees(id) ON DELETE CASCADE,
  type        VARCHAR(20) NOT NULL CHECK (type IN ('email','phone','linkedin')),
  value       TEXT    NOT NULL,
  UNIQUE(employee_id, type, value)
);

CREATE INDEX idx_contacts_employee ON employee_contacts(employee_id);

-- record education history
CREATE TABLE employee_education (
  id            UUID    PRIMARY KEY DEFAULT uuid_generate_v4(),
  employee_id   UUID    NOT NULL REFERENCES employees(id) ON DELETE CASCADE,
  institution   VARCHAR(200),
  degree        VARCHAR(200),
  start_year    INT,
  end_year      INT,
  UNIQUE(employee_id, institution, degree)
);

CREATE INDEX idx_education_employee ON employee_education(employee_id);
