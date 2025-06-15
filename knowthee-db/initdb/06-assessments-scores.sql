CREATE TABLE employee_assessments (
  id              UUID    PRIMARY KEY DEFAULT uuid_generate_v4(),
  employee_id     UUID    NOT NULL REFERENCES employees(id) ON DELETE CASCADE,
  type_id         UUID    NOT NULL REFERENCES assessment_types(id),
  assessment_date DATE    DEFAULT CURRENT_DATE,
  tenant_id       VARCHAR(50) NOT NULL DEFAULT 'default',
  created_at      TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_assessments_employee ON employee_assessments(employee_id);

-- one row per metric scored in that event
CREATE TABLE employee_assessment_scores (
  id            UUID    PRIMARY KEY DEFAULT uuid_generate_v4(),
  assessment_id UUID    NOT NULL REFERENCES employee_assessments(id) ON DELETE CASCADE,
  metric_id     UUID    NOT NULL REFERENCES assessment_metrics(id),
  value         NUMERIC NOT NULL,
  UNIQUE(assessment_id, metric_id)
);

CREATE INDEX idx_scores_assessment ON employee_assessment_scores(assessment_id);
