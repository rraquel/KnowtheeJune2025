-- core employee table
CREATE TABLE employees (
  id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  tenant_id VARCHAR(50) NOT NULL DEFAULT 'default',
  employee_id VARCHAR(100) NOT NULL UNIQUE,
  name VARCHAR(200) NOT NULL,
  department VARCHAR(100),
  position VARCHAR(100),
  manager_id UUID REFERENCES employees(id),
  hire_date DATE,
  years_experience INTEGER,
  education_level VARCHAR(50),
  location VARCHAR(100),
  status VARCHAR(20) DEFAULT 'active'
);


CREATE INDEX idx_employees_tenant_id ON employees(tenant_id);
CREATE INDEX idx_employees_department ON employees(department);
