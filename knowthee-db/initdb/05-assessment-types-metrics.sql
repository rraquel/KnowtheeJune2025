-- assessment type (HPI, HDS, MVPI, IDI…)
CREATE TABLE assessment_types (
  id   UUID   PRIMARY KEY DEFAULT uuid_generate_v4(),
  code VARCHAR(20) NOT NULL UNIQUE,  -- e.g. 'HPI'
  name TEXT    NOT NULL
);

-- individual metrics under each type
CREATE TABLE assessment_metrics (
  id      UUID   PRIMARY KEY DEFAULT uuid_generate_v4(),
  type_id UUID   NOT NULL REFERENCES assessment_types(id) ON DELETE CASCADE,
  code    VARCHAR(50) NOT NULL,      -- e.g. 'Ambition'
  label   VARCHAR(200) NOT NULL,
  UNIQUE(type_id, code)
);
