-- ============================================================
-- schema_sqlite.sql – VORTEXA 3.0 local SQLite schema
-- Full parity with team's MySQL schema.sql
-- ============================================================

-- ── 1. Users ────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS users (
    id            INTEGER PRIMARY KEY AUTOINCREMENT,
    full_name     TEXT NOT NULL,
    email         TEXT NOT NULL UNIQUE,
    password_hash TEXT NOT NULL,
    role          TEXT CHECK(role IN ('jobseeker', 'employer', 'admin')) NOT NULL DEFAULT 'jobseeker',
    created_at    DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at    DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP
);

-- ── 2. Jobs ─────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS jobs (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    employer_id     INTEGER NOT NULL,
    title           TEXT NOT NULL,
    description     TEXT,
    skills_required TEXT,
    location        TEXT,
    salary_range    TEXT,
    is_active       INTEGER NOT NULL DEFAULT 1,
    created_at      DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at      DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (employer_id) REFERENCES users(id) ON DELETE CASCADE
);

-- ── 3. Applications ─────────────────────────────────────────
CREATE TABLE IF NOT EXISTS applications (
    id           INTEGER PRIMARY KEY AUTOINCREMENT,
    job_id       INTEGER NOT NULL,
    applicant_id INTEGER NOT NULL,
    status       TEXT CHECK(status IN ('pending', 'reviewed', 'accepted', 'rejected')) NOT NULL DEFAULT 'pending',
    applied_at   DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at   DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    UNIQUE (job_id, applicant_id),
    FOREIGN KEY (job_id)       REFERENCES jobs(id)  ON DELETE CASCADE,
    FOREIGN KEY (applicant_id) REFERENCES users(id) ON DELETE CASCADE
);

-- ── 4. Candidate Profiles ───────────────────────────────────
CREATE TABLE IF NOT EXISTS candidate_profiles (
    user_id     INTEGER PRIMARY KEY,
    phone       TEXT,
    experience  TEXT,
    bio         TEXT,
    created_at  DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at  DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
);

-- ── 5. Candidate Education ──────────────────────────────────
CREATE TABLE IF NOT EXISTS candidate_education (
    user_id         INTEGER PRIMARY KEY,
    degree          TEXT,
    branch          TEXT,
    college         TEXT,
    graduation_year INTEGER,
    updated_at      DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
);

-- ── 6. Skills ───────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS skills (
    id     INTEGER PRIMARY KEY AUTOINCREMENT,
    name   TEXT NOT NULL UNIQUE,
    active INTEGER DEFAULT 1
);

-- ── 7. Candidate Skills ─────────────────────────────────────
CREATE TABLE IF NOT EXISTS candidate_skills (
    user_id    INTEGER NOT NULL,
    skill_id   INTEGER NOT NULL,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (user_id, skill_id),
    FOREIGN KEY (user_id)  REFERENCES users(id)  ON DELETE CASCADE,
    FOREIGN KEY (skill_id) REFERENCES skills(id) ON DELETE CASCADE
);

-- ── 8. Assessment Questions ─────────────────────────────────
CREATE TABLE IF NOT EXISTS assessment_questions (
    id             INTEGER PRIMARY KEY AUTOINCREMENT,
    skill_id       INTEGER NOT NULL,
    question_text  TEXT NOT NULL,
    option_a       TEXT NOT NULL,
    option_b       TEXT NOT NULL,
    option_c       TEXT NOT NULL,
    option_d       TEXT NOT NULL,
    correct_option TEXT NOT NULL,
    marks          INTEGER DEFAULT 5,
    difficulty     TEXT DEFAULT 'MEDIUM',
    active         INTEGER DEFAULT 1,
    created_at     DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (skill_id) REFERENCES skills(id) ON DELETE CASCADE
);

-- ── 9. Assessment Attempts ──────────────────────────────────
CREATE TABLE IF NOT EXISTS assessment_attempts (
    id                 INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id            INTEGER NOT NULL,
    skill_id           INTEGER NOT NULL,
    status             TEXT DEFAULT 'IN_PROGRESS',
    started_at         DATETIME DEFAULT CURRENT_TIMESTAMP,
    time_limit_seconds INTEGER DEFAULT 900,
    score              INTEGER DEFAULT 0,
    total_marks        INTEGER DEFAULT 0,
    percentage         REAL,
    submitted_at       DATETIME,
    finish_reason      TEXT,
    FOREIGN KEY (user_id)  REFERENCES users(id)  ON DELETE CASCADE,
    FOREIGN KEY (skill_id) REFERENCES skills(id) ON DELETE CASCADE
);

-- ── 10. Assessment Attempt Questions ────────────────────────
CREATE TABLE IF NOT EXISTS assessment_attempt_questions (
    attempt_id      INTEGER NOT NULL,
    question_id     INTEGER NOT NULL,
    question_number INTEGER NOT NULL,
    marks           INTEGER NOT NULL,
    PRIMARY KEY (attempt_id, question_id),
    UNIQUE (attempt_id, question_number),
    FOREIGN KEY (attempt_id)  REFERENCES assessment_attempts(id)   ON DELETE CASCADE,
    FOREIGN KEY (question_id) REFERENCES assessment_questions(id) ON DELETE CASCADE
);

-- ── 11. Assessment Answers ──────────────────────────────────
CREATE TABLE IF NOT EXISTS assessment_answers (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    attempt_id      INTEGER NOT NULL,
    question_id     INTEGER NOT NULL,
    selected_answer TEXT,
    is_correct      INTEGER DEFAULT 0,
    marks_awarded   INTEGER DEFAULT 0,
    UNIQUE (attempt_id, question_id),
    FOREIGN KEY (attempt_id)  REFERENCES assessment_attempts(id)   ON DELETE CASCADE,
    FOREIGN KEY (question_id) REFERENCES assessment_questions(id) ON DELETE CASCADE
);

-- ── 11b. Assessment Proctor Events ──────────────────────────
CREATE TABLE IF NOT EXISTS assessment_proctor_events (
    id         INTEGER PRIMARY KEY AUTOINCREMENT,
    attempt_id INTEGER NOT NULL,
    user_id    INTEGER NOT NULL,
    event_type TEXT NOT NULL,
    details    TEXT,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (attempt_id) REFERENCES assessment_attempts(id) ON DELETE CASCADE,
    FOREIGN KEY (user_id)    REFERENCES users(id) ON DELETE CASCADE
);

-- ── 12. Assessment Results ──────────────────────────────────
CREATE TABLE IF NOT EXISTS assessment_results (
    id            INTEGER PRIMARY KEY AUTOINCREMENT,
    attempt_id    INTEGER NOT NULL UNIQUE,
    user_id       INTEGER NOT NULL,
    skill_id      INTEGER NOT NULL,
    score         INTEGER NOT NULL,
    total_marks   INTEGER NOT NULL,
    percentage    REAL NOT NULL,
    correct_count INTEGER NOT NULL,
    status        TEXT NOT NULL,
    created_at    DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (attempt_id) REFERENCES assessment_attempts(id) ON DELETE CASCADE,
    FOREIGN KEY (user_id)    REFERENCES users(id)               ON DELETE CASCADE,
    FOREIGN KEY (skill_id)   REFERENCES skills(id)              ON DELETE CASCADE
);

-- ── 13. Skill Passports ─────────────────────────────────────
CREATE TABLE IF NOT EXISTS skill_passports (
    user_id       INTEGER PRIMARY KEY,
    passport_code TEXT NOT NULL UNIQUE,
    generated_at  DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
);

-- ── 14. Candidate Projects (Practical Experience) ───────────
CREATE TABLE IF NOT EXISTS candidate_projects (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id     INTEGER NOT NULL,
    title       TEXT NOT NULL,
    description TEXT,
    tech_stack  TEXT,
    live_url    TEXT,
    github_url  TEXT,
    created_at  DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
);
