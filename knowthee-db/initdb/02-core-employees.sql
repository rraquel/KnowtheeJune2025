-- core employee table
CREATE TABLE employees (
  id            UUID    PRIMARY KEY DEFAULT uuid_generate_v4(),
  tenant_id     VARCHAR(50) NOT NULL DEFAULT 'default',
  employee_code VARCHAR(100) NOT NULL UNIQUE,
  name          VARCHAR(200) NOT NULL,
  department    VARCHAR(100),
  position      VARCHAR(100),
  manager_id    UUID REFERENCES employees(id) ON DELETE SET NULL,
  hire_date     DATE,
  location      VARCHAR(100),
  status        VARCHAR(20) DEFAULT 'active',
  created_at    TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  updated_at    TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_employees_tenant_id ON employees(tenant_id);
CREATE INDEX idx_employees_department ON employees(department);
