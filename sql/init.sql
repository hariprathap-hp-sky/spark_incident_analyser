-- Runs automatically on first Postgres container start (docker-entrypoint-initdb.d).
-- Schema matches the SELECT in backend/data_pipeline.py::run_pipeline().

CREATE TABLE IF NOT EXISTS incidents (
    incident_id   VARCHAR(50) PRIMARY KEY,
    created_date  TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    cluster       VARCHAR(100),
    application   VARCHAR(100),
    description   TEXT,
    work_notes    TEXT,
    status        VARCHAR(20) NOT NULL DEFAULT 'RESOLVED',
    ingested      BOOLEAN     NOT NULL DEFAULT FALSE,
    ingested_at   TIMESTAMPTZ
);

-- Speeds up the WHERE ingested = FALSE AND status = 'RESOLVED' scan in
-- data_pipeline.py once this table grows to tens of thousands of rows.
CREATE INDEX IF NOT EXISTS idx_incidents_pending
    ON incidents (ingested, status);

-- feedback_manager.py also auto-creates this on app startup, but declaring
-- it here means the schema is fully visible in one place.
CREATE TABLE IF NOT EXISTS feedback (
    id               SERIAL PRIMARY KEY,
    query            TEXT        NOT NULL,
    answer           TEXT        NOT NULL,
    rating           VARCHAR(20) NOT NULL CHECK (rating IN ('thumbs_up', 'thumbs_down')),
    timestamp        TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    confidence_score FLOAT,
    path_taken       VARCHAR(50)
);