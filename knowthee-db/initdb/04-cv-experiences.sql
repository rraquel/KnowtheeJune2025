-- free‐form experience entries
CREATE TABLE employee_experiences (
  id               UUID    PRIMARY KEY DEFAULT uuid_generate_v4(),
  employee_id      UUID    NOT NULL REFERENCES employees(id) ON DELETE CASCADE,
  company          VARCHAR(255),
  title            VARCHAR(255),
  start_date       DATE,
  end_date         DATE,
  description      TEXT,
  responsabilities TEXT,
  sort_order       INT     NOT NULL DEFAULT 0,
  created_at       TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  updated_at       TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  UNIQUE(employee_id, sort_order)
);

CREATE INDEX idx_experiences_employee ON employee_experiences(employee_id);
