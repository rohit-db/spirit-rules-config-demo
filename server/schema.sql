CREATE EXTENSION IF NOT EXISTS "pgcrypto";

CREATE TABLE IF NOT EXISTS rule_headers (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    start_date DATE NOT NULL,
    end_date DATE NOT NULL,
    cost_category VARCHAR(100) NOT NULL,
    rate_category VARCHAR(100),
    category VARCHAR(100),
    account_group VARCHAR(100),
    groupby_costcenter BOOLEAN DEFAULT FALSE,
    groupby_account BOOLEAN DEFAULT FALSE,
    fixed_variable_pct_split DECIMAL(5,2),
    fixed_variable_type VARCHAR(50),
    status VARCHAR(20) NOT NULL DEFAULT 'draft',
    version INTEGER NOT NULL DEFAULT 1,
    cloned_from_id UUID REFERENCES rule_headers(id),
    created_by VARCHAR(100) NOT NULL,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS rule_lines (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    header_id UUID NOT NULL REFERENCES rule_headers(id) ON DELETE CASCADE,
    account_number VARCHAR(50) NOT NULL,
    account_name VARCHAR(200),
    stat_type VARCHAR(50) NOT NULL,
    proration_rate DECIMAL(10,6) NOT NULL,
    effective_date DATE,
    notes TEXT,
    sort_order INTEGER DEFAULT 0,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS rule_audit_log (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    header_id UUID NOT NULL REFERENCES rule_headers(id) ON DELETE CASCADE,
    action VARCHAR(20) NOT NULL,
    changed_by VARCHAR(100) NOT NULL,
    changed_at TIMESTAMP DEFAULT NOW(),
    old_values JSONB,
    new_values JSONB
);

CREATE INDEX IF NOT EXISTS idx_rule_headers_status ON rule_headers(status);
CREATE INDEX IF NOT EXISTS idx_rule_headers_cost_category ON rule_headers(cost_category);
CREATE INDEX IF NOT EXISTS idx_rule_lines_header_id ON rule_lines(header_id);
CREATE INDEX IF NOT EXISTS idx_rule_audit_header_id ON rule_audit_log(header_id);
