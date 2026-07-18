"""Database migration script for new employee system tables."""
from sqlalchemy import text

MIGRATION_SQL = """
-- Active Tasks for Micro-Segmentation
CREATE TABLE IF NOT EXISTS employee_active_tasks (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    employee_id INTEGER REFERENCES employees(id) ON DELETE CASCADE,
    task_name VARCHAR(200) NOT NULL,
    task_type VARCHAR(50) NOT NULL,
    country_code VARCHAR(10),
    permission_scope TEXT,
    start_time TIMESTAMP,
    end_time TIMESTAMP,
    status VARCHAR(20) DEFAULT 'active',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Risk Scores for Flight Risk AI
CREATE TABLE IF NOT EXISTS employee_risk_scores (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    employee_id INTEGER REFERENCES employees(id) ON DELETE CASCADE,
    metric_name VARCHAR(100) NOT NULL,
    score NUMERIC(5,2) NOT NULL,
    recorded_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(employee_id, metric_name)
);

-- WORM Audit Trail
CREATE TABLE IF NOT EXISTS employee_audit_timeline (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    employee_id INTEGER REFERENCES employees(id) ON DELETE CASCADE,
    event_type VARCHAR(100) NOT NULL,
    event_data TEXT,
    actor_id INTEGER REFERENCES users(id),
    ip_address VARCHAR(45),
    user_agent TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Video Rooms
CREATE TABLE IF NOT EXISTS video_rooms (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    room_id VARCHAR(100) UNIQUE NOT NULL,
    room_uuid VARCHAR(50) UNIQUE NOT NULL,
    title VARCHAR(200),
    created_by INTEGER REFERENCES users(id),
    max_participants INTEGER DEFAULT 100,
    is_recording BOOLEAN DEFAULT FALSE,
    settings TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Chat Threads
CREATE TABLE IF NOT EXISTS chat_threads (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    thread_id VARCHAR(100) UNIQUE NOT NULL,
    entity_type VARCHAR(50),
    entity_id INTEGER,
    title VARCHAR(200),
    created_by INTEGER REFERENCES users(id),
    is_direct BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Masked Messages
CREATE TABLE IF NOT EXISTS masked_messages (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    sender_id INTEGER REFERENCES employees(id),
    recipient_ref VARCHAR(100),
    message_hash BIGINT,
    content TEXT,
    sent_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Incident Rooms
CREATE TABLE IF NOT EXISTS incident_rooms (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    room_id VARCHAR(100) UNIQUE NOT NULL,
    severity VARCHAR(20),
    title VARCHAR(200),
    description TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Training Modules
CREATE TABLE IF NOT EXISTS training_modules (
    module_id VARCHAR(100) PRIMARY KEY,
    title VARCHAR(200) NOT NULL,
    description TEXT,
    required_for_role VARCHAR(100),
    duration_minutes INTEGER DEFAULT 30,
    is_active BOOLEAN DEFAULT TRUE,
    permission_key VARCHAR(100),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Employee Trainings
CREATE TABLE IF NOT EXISTS employee_trainings (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    employee_id INTEGER REFERENCES employees(id) ON DELETE CASCADE,
    module_id VARCHAR(100) REFERENCES training_modules(module_id),
    assigned_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    completed_at TIMESTAMP,
    score NUMERIC(5,2),
    status VARCHAR(20) DEFAULT 'assigned',
    UNIQUE(employee_id, module_id)
);

-- Blackout Dates
CREATE TABLE IF NOT EXISTS country_blackout_dates (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    country_code VARCHAR(10) NOT NULL,
    date DATE NOT NULL,
    max_leave_percentage NUMERIC(5,2) DEFAULT 20.0,
    reason VARCHAR(200),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(country_code, date)
);

-- Shift Rosters
CREATE TABLE IF NOT EXISTS shift_rosters (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    employee_id INTEGER REFERENCES employees(id) ON DELETE CASCADE,
    shift_date DATE NOT NULL,
    start_time TIME NOT NULL,
    end_time TIME NOT NULL,
    shift_type VARCHAR(30) DEFAULT 'scheduled',
    status VARCHAR(20) DEFAULT 'scheduled',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(employee_id, shift_date)
);

-- Treasury Ledger
CREATE TABLE IF NOT EXISTS treasury_ledger (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    account_id INTEGER REFERENCES treasury_accounts(id),
    entry_type VARCHAR(20) NOT NULL,
    amount NUMERIC(15,2) NOT NULL,
    description TEXT,
    reference_id VARCHAR(100),
    entry_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Treasury Accounts
CREATE TABLE IF NOT EXISTS treasury_accounts (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    employee_id INTEGER REFERENCES employees(id),
    account_name VARCHAR(200),
    account_type VARCHAR(50),
    balance NUMERIC(15,2) DEFAULT 0,
    currency VARCHAR(3) DEFAULT 'OMR',
    is_locked BOOLEAN DEFAULT FALSE,
    locked_reason VARCHAR(200),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Indexes for performance
CREATE INDEX IF NOT EXISTS idx_audit_timeline_employee ON employee_audit_timeline(employee_id);
CREATE INDEX IF NOT EXISTS idx_audit_timeline_created ON employee_audit_timeline(created_at);
CREATE INDEX IF NOT EXISTS idx_risk_scores_employee ON employee_risk_scores(employee_id);
CREATE INDEX IF NOT EXISTS idx_active_tasks_employee ON employee_active_tasks(employee_id);
CREATE INDEX IF NOT EXISTS idx_shift_roster_date ON shift_rosters(shift_date);
CREATE INDEX IF NOT EXISTS idx_video_rooms_created ON video_rooms(created_at);
CREATE INDEX IF NOT EXISTS idx_chat_threads_entity ON chat_threads(entity_type, entity_id);
"""


def run_migration(engine):
    """Execute the migration SQL."""
    with engine.connect() as conn:
        for statement in MIGRATION_SQL.split(';'):
            statement = statement.strip()
            if statement:
                conn.execute(text(statement))
        conn.commit()
    print("Migration completed successfully!")
