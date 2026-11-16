-- TalentPulse AI Relational Schema (PostgreSQL / SQLite)
-- Licensed under the MIT License

CREATE TABLE users (
    user_id SERIAL PRIMARY KEY,
    emp_code VARCHAR(20) UNIQUE NOT NULL,
    full_name VARCHAR(120) NOT NULL,
    email VARCHAR(120) UNIQUE NOT NULL,
    password_hash TEXT NOT NULL,
    role VARCHAR(30) NOT NULL CHECK (role IN ('Employee', 'Manager', 'HR Executive', 'Admin')),
    department VARCHAR(80),
    job_role VARCHAR(80),
    tenure_months INTEGER DEFAULT 12,
    monthly_hours NUMERIC(5,1) DEFAULT 176.0,
    last_hike_months INTEGER DEFAULT 8,
    engagement_score NUMERIC(3,2) DEFAULT 4.0,
    perf_rating NUMERIC(3,2) DEFAULT 4.2,
    commute_km NUMERIC(5,1) DEFAULT 10.0,
    wfh_days INTEGER DEFAULT 2,
    promotions_3yr INTEGER DEFAULT 0,
    risk_probability NUMERIC(5,2),
    risk_tier VARCHAR(20)
);
