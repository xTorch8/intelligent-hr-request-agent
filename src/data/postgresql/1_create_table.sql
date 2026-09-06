-- ============================================================
-- Intelligent HR Request Management Agent
-- PostgreSQL Database Schema
-- ============================================================


CREATE EXTENSION IF NOT EXISTS pgcrypto;
CREATE EXTENSION IF NOT EXISTS vector;


CREATE TABLE employees (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),

    employee_number VARCHAR(50) NOT NULL UNIQUE,
    first_name       VARCHAR(100) NOT NULL,
    last_name        VARCHAR(100) NOT NULL,
    email            VARCHAR(255) NOT NULL UNIQUE,

    department       VARCHAR(100) NOT NULL,
    job_title        VARCHAR(150) NOT NULL,

    employment_type   VARCHAR(50) NOT NULL,
    employment_status VARCHAR(50) NOT NULL,

    hire_date DATE NOT NULL,

    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT chk_employees_employment_type
        CHECK (
            employment_type IN (
                'FULL_TIME',
                'PART_TIME',
                'CONTRACT',
                'INTERN',
                'TEMPORARY'
            )
        ),

    CONSTRAINT chk_employees_employment_status
        CHECK (
            employment_status IN (
                'ACTIVE',
                'INACTIVE',
                'ON_LEAVE',
                'TERMINATED'
            )
        )
);

CREATE TABLE users (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),

    employee_id UUID UNIQUE REFERENCES employees(id) ON DELETE CASCADE,
    email VARCHAR(255) NOT NULL UNIQUE,
    password_hash VARCHAR(255) NOT NULL,
    role VARCHAR(50) NOT NULL,

    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT chk_users_role
        CHECK (
            role IN (
                'EMPLOYEE',
                'HR_ADMIN'
            )
        )
);

CREATE TABLE leave_balances (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),

    employee_id UUID NOT NULL,

    leave_type VARCHAR(50) NOT NULL,

    total_days     DECIMAL(10,2) NOT NULL DEFAULT 0,
    used_days      DECIMAL(10,2) NOT NULL DEFAULT 0,
    remaining_days DECIMAL(10,2) NOT NULL DEFAULT 0,

    year INTEGER NOT NULL,

    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT fk_leave_balances_employee
        FOREIGN KEY (employee_id)
        REFERENCES employees(id)
        ON DELETE CASCADE,

    CONSTRAINT uq_leave_balance_employee_type_year
        UNIQUE (employee_id, leave_type, year),

    CONSTRAINT chk_leave_balances_year
        CHECK (year >= 2000 AND year <= 2100),

    CONSTRAINT chk_leave_balances_total_days
        CHECK (total_days >= 0),

    CONSTRAINT chk_leave_balances_used_days
        CHECK (used_days >= 0),

    CONSTRAINT chk_leave_balances_remaining_days
        CHECK (remaining_days >= 0),

    CONSTRAINT chk_leave_balances_used_not_exceed_total
        CHECK (used_days <= total_days)
);

CREATE TABLE employee_benefits (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),

    employee_id UUID NOT NULL,

    benefit_type VARCHAR(100) NOT NULL,
    plan_name VARCHAR(150) NOT NULL,

    coverage_percentage DECIMAL(5,2),
    annual_limit        DECIMAL(15,2),
    used_amount         DECIMAL(15,2) NOT NULL DEFAULT 0,

    effective_date  DATE NOT NULL,
    expiration_date DATE,

    status VARCHAR(50) NOT NULL,

    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT fk_employee_benefits_employee
        FOREIGN KEY (employee_id)
        REFERENCES employees(id)
        ON DELETE CASCADE,

    CONSTRAINT chk_employee_benefits_coverage
        CHECK (
            coverage_percentage IS NULL
            OR (
                coverage_percentage >= 0
                AND coverage_percentage <= 100
            )
        ),

    CONSTRAINT chk_employee_benefits_annual_limit
        CHECK (
            annual_limit IS NULL
            OR annual_limit >= 0
        ),

    CONSTRAINT chk_employee_benefits_used_amount
        CHECK (used_amount >= 0),

    CONSTRAINT chk_employee_benefits_dates
        CHECK (
            expiration_date IS NULL
            OR expiration_date >= effective_date
        ),

    CONSTRAINT chk_employee_benefits_status
        CHECK (
            status IN (
                'ACTIVE',
                'EXPIRED',
                'SUSPENDED',
                'CANCELLED'
            )
        )
);

CREATE TABLE hr_policies (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),

    policy_code VARCHAR(50) NOT NULL UNIQUE,
    policy_name VARCHAR(200) NOT NULL,

    policy_type VARCHAR(100) NOT NULL,
    version VARCHAR(50) NOT NULL,

    blob_url TEXT NOT NULL,

    effective_date  DATE NOT NULL,
    expiration_date DATE,

    status VARCHAR(50) NOT NULL,

    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT chk_hr_policies_dates
        CHECK (
            expiration_date IS NULL
            OR expiration_date >= effective_date
        ),

    CONSTRAINT chk_hr_policies_status
        CHECK (
            status IN (
                'DRAFT',
                'ACTIVE',
                'EXPIRED',
                'ARCHIVED'
            )
        )
);

CREATE TABLE policy_chunks (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),

    policy_id UUID NOT NULL,

    chunk_index INTEGER NOT NULL,
    content TEXT NOT NULL,

    /*
     * IMPORTANT:
     * Replace 1536 with the dimension of the embedding model
     * you actually use.
     *
     * Example:
     * - text-embedding-3-small default = 1536
     * - text-embedding-3-large can be configured
     */
    embedding VECTOR(1536),

    metadata JSONB NOT NULL DEFAULT '{}'::JSONB,

    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT fk_policy_chunks_policy
        FOREIGN KEY (policy_id)
        REFERENCES hr_policies(id)
        ON DELETE CASCADE,

    CONSTRAINT uq_policy_chunk_index
        UNIQUE (policy_id, chunk_index),

    CONSTRAINT chk_policy_chunks_chunk_index
        CHECK (chunk_index >= 0)
);

CREATE TABLE requests (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),

    request_number VARCHAR(50) NOT NULL UNIQUE,

    employee_id UUID NOT NULL,

    request_type VARCHAR(50) NOT NULL,
    status VARCHAR(50) NOT NULL,

    title VARCHAR(255) NOT NULL,
    description TEXT,

    submitted_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    completed_at TIMESTAMP,

    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT fk_requests_employee
        FOREIGN KEY (employee_id)
        REFERENCES employees(id)
        ON DELETE RESTRICT,

    CONSTRAINT chk_requests_type
        CHECK (
            request_type IN (
                'LEAVE',
                'EXPENSE',
                'BENEFIT'
            )
        ),

    CONSTRAINT chk_requests_status
        CHECK (
            status IN (
                'SUBMITTED',
                'PROCESSING',
                'PENDING_REVIEW',
                'APPROVED',
                'REJECTED',
                'COMPLETED',
                'CANCELLED'
            )
        ),

    CONSTRAINT chk_requests_completed_at
        CHECK (
            completed_at IS NULL
            OR completed_at >= submitted_at
        )
);

CREATE TABLE leave_requests (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),

    request_id UUID NOT NULL UNIQUE,

    leave_type VARCHAR(50) NOT NULL,

    start_date DATE NOT NULL,
    end_date DATE NOT NULL,

    requested_days DECIMAL(10,2) NOT NULL,

    reason TEXT,

    CONSTRAINT fk_leave_requests_request
        FOREIGN KEY (request_id)
        REFERENCES requests(id)
        ON DELETE CASCADE,

    CONSTRAINT chk_leave_requests_dates
        CHECK (end_date >= start_date),

    CONSTRAINT chk_leave_requests_requested_days
        CHECK (requested_days > 0)
);

CREATE TABLE expense_claims (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),

    request_id UUID NOT NULL UNIQUE,

    expense_category VARCHAR(100) NOT NULL,

    expense_date DATE NOT NULL,

    merchant VARCHAR(255) NOT NULL,

    claim_amount DECIMAL(15,2) NOT NULL,

    currency VARCHAR(3) NOT NULL,

    description TEXT,

    blob_url TEXT,

    CONSTRAINT fk_expense_claims_request
        FOREIGN KEY (request_id)
        REFERENCES requests(id)
        ON DELETE CASCADE,

    CONSTRAINT chk_expense_claims_amount
        CHECK (claim_amount > 0),

    CONSTRAINT chk_expense_claims_currency
        CHECK (currency ~ '^[A-Z]{3}$')
);

CREATE TABLE benefit_claims (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),

    request_id UUID NOT NULL UNIQUE,

    benefit_type VARCHAR(100) NOT NULL,

    service_date DATE NOT NULL,

    provider_name VARCHAR(255) NOT NULL,

    claim_amount DECIMAL(15,2) NOT NULL,

    currency VARCHAR(3) NOT NULL,

    description TEXT,

    blob_url TEXT,

    CONSTRAINT fk_benefit_claims_request
        FOREIGN KEY (request_id)
        REFERENCES requests(id)
        ON DELETE CASCADE,

    CONSTRAINT chk_benefit_claims_amount
        CHECK (claim_amount > 0),

    CONSTRAINT chk_benefit_claims_currency
        CHECK (currency ~ '^[A-Z]{3}$')
);

CREATE TABLE agent_runs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),

    request_id UUID NOT NULL,

    agent_version VARCHAR(50) NOT NULL,

    status VARCHAR(50) NOT NULL,

    input_tokens  INTEGER,
    output_tokens INTEGER,

    started_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    completed_at TIMESTAMP,

    error_message TEXT,

    CONSTRAINT fk_agent_runs_request
        FOREIGN KEY (request_id)
        REFERENCES requests(id)
        ON DELETE CASCADE,

    CONSTRAINT chk_agent_runs_status
        CHECK (
            status IN (
                'RUNNING',
                'COMPLETED',
                'FAILED',
                'CANCELLED'
            )
        ),

    CONSTRAINT chk_agent_runs_input_tokens
        CHECK (
            input_tokens IS NULL
            OR input_tokens >= 0
        ),

    CONSTRAINT chk_agent_runs_output_tokens
        CHECK (
            output_tokens IS NULL
            OR output_tokens >= 0
        ),

    CONSTRAINT chk_agent_runs_completed_at
        CHECK (
            completed_at IS NULL
            OR completed_at >= started_at
        )
);

CREATE TABLE request_decisions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),

    request_id UUID NOT NULL,
    agent_run_id UUID NOT NULL,

    recommendation VARCHAR(50) NOT NULL,
    eligibility_result VARCHAR(50) NOT NULL,

    eligible_amount DECIMAL(15,2),

    currency VARCHAR(3),

    rule_results JSONB NOT NULL DEFAULT '{}'::JSONB,
    policy_references JSONB NOT NULL DEFAULT '{}'::JSONB,

    reasoning_summary TEXT,

    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT fk_request_decisions_request
        FOREIGN KEY (request_id)
        REFERENCES requests(id)
        ON DELETE CASCADE,

    CONSTRAINT fk_request_decisions_agent_run
        FOREIGN KEY (agent_run_id)
        REFERENCES agent_runs(id)
        ON DELETE CASCADE,

    CONSTRAINT chk_request_decisions_recommendation
        CHECK (
            recommendation IN (
                'APPROVE',
                'REJECT',
                'REVIEW'
            )
        ),

    CONSTRAINT chk_request_decisions_eligibility
        CHECK (
            eligibility_result IN (
                'ELIGIBLE',
                'NOT_ELIGIBLE',
                'PARTIALLY_ELIGIBLE',
                'REQUIRES_REVIEW'
            )
        ),

    CONSTRAINT chk_request_decisions_amount
        CHECK (
            eligible_amount IS NULL
            OR eligible_amount >= 0
        ),

    CONSTRAINT chk_request_decisions_currency
        CHECK (
            currency IS NULL
            OR currency ~ '^[A-Z]{3}$'
        )
);

CREATE TABLE audit_logs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),

    request_id UUID NOT NULL,

    actor_type VARCHAR(50) NOT NULL,
    actor_id UUID,

    action VARCHAR(100) NOT NULL,

    previous_status VARCHAR(50),
    new_status VARCHAR(50),

    metadata JSONB NOT NULL DEFAULT '{}'::JSONB,

    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT fk_audit_logs_request
        FOREIGN KEY (request_id)
        REFERENCES requests(id)
        ON DELETE CASCADE,

    CONSTRAINT chk_audit_logs_actor_type
        CHECK (
            actor_type IN (
                'EMPLOYEE',
                'AGENT',
                'HR_ADMIN',
                'SYSTEM'
            )
        )
);


CREATE INDEX idx_employees_department
    ON employees(department);

CREATE INDEX idx_employees_status
    ON employees(employment_status);


CREATE INDEX idx_leave_balances_employee
    ON leave_balances(employee_id);

CREATE INDEX idx_leave_balances_employee_year
    ON leave_balances(employee_id, year);


CREATE INDEX idx_employee_benefits_employee
    ON employee_benefits(employee_id);

CREATE INDEX idx_employee_benefits_type_status
    ON employee_benefits(benefit_type, status);


CREATE INDEX idx_hr_policies_type_status
    ON hr_policies(policy_type, status);

CREATE INDEX idx_hr_policies_effective_date
    ON hr_policies(effective_date);


CREATE INDEX idx_policy_chunks_policy
    ON policy_chunks(policy_id);


CREATE INDEX idx_policy_chunks_embedding
    ON policy_chunks
    USING hnsw (embedding vector_cosine_ops);


CREATE INDEX idx_requests_employee
    ON requests(employee_id);

CREATE INDEX idx_requests_type_status
    ON requests(request_type, status);

CREATE INDEX idx_requests_submitted_at
    ON requests(submitted_at);


CREATE INDEX idx_agent_runs_request
    ON agent_runs(request_id);

CREATE INDEX idx_agent_runs_status
    ON agent_runs(status);


CREATE INDEX idx_request_decisions_request
    ON request_decisions(request_id);

CREATE INDEX idx_request_decisions_agent_run
    ON request_decisions(agent_run_id);


CREATE INDEX idx_audit_logs_request
    ON audit_logs(request_id);

CREATE INDEX idx_audit_logs_created_at
    ON audit_logs(created_at);


CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;


CREATE TRIGGER trg_employees_updated_at
BEFORE UPDATE ON employees
FOR EACH ROW
EXECUTE FUNCTION update_updated_at_column();


CREATE TRIGGER trg_leave_balances_updated_at
BEFORE UPDATE ON leave_balances
FOR EACH ROW
EXECUTE FUNCTION update_updated_at_column();


CREATE TRIGGER trg_employee_benefits_updated_at
BEFORE UPDATE ON employee_benefits
FOR EACH ROW
EXECUTE FUNCTION update_updated_at_column();


CREATE TRIGGER trg_hr_policies_updated_at
BEFORE UPDATE ON hr_policies
FOR EACH ROW
EXECUTE FUNCTION update_updated_at_column();


CREATE TRIGGER trg_requests_updated_at
BEFORE UPDATE ON requests
FOR EACH ROW
EXECUTE FUNCTION update_updated_at_column();
