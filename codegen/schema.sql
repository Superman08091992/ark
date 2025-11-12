-- ARK Phase 7: Self-Modification & Code Generation
-- Database Schema for Code Generation Systems
-- Created: 2025-11-12

-- ============================================================================
-- STAGE 1: CODE UNDERSTANDING
-- ============================================================================

-- Index of all code files in the ARK codebase
CREATE TABLE IF NOT EXISTS code_index (
    file_id TEXT PRIMARY KEY,
    file_path TEXT NOT NULL UNIQUE,
    module_name TEXT,
    functions TEXT,              -- JSON: [{name, signature, docstring, line_start, line_end}]
    classes TEXT,                -- JSON: [{name, methods, docstring, line_start, line_end}]
    imports TEXT,                -- JSON: [module_names]
    dependencies TEXT,           -- JSON: [file_paths that this file depends on]
    embedding BLOB,              -- Semantic embedding of file content
    complexity_score REAL,       -- Cyclomatic complexity
    lines_of_code INTEGER,
    last_modified INTEGER,       -- Unix timestamp
    indexed_at INTEGER,          -- Unix timestamp
    trust_tier TEXT DEFAULT 'sandbox'
);

CREATE INDEX IF NOT EXISTS idx_code_index_path ON code_index(file_path);
CREATE INDEX IF NOT EXISTS idx_code_index_module ON code_index(module_name);
CREATE INDEX IF NOT EXISTS idx_code_index_trust ON code_index(trust_tier);

-- Reusable code patterns extracted from codebase
CREATE TABLE IF NOT EXISTS code_patterns (
    pattern_id TEXT PRIMARY KEY,
    pattern_type TEXT NOT NULL,  -- 'function', 'class', 'module', 'snippet'
    name TEXT,
    code_snippet TEXT NOT NULL,
    description TEXT,
    usage_examples TEXT,         -- JSON: [examples of how to use this pattern]
    usage_count INTEGER DEFAULT 0,
    quality_score REAL DEFAULT 0.5,
    embedding BLOB,              -- Semantic embedding
    tags TEXT,                   -- JSON: [tag1, tag2, ...]
    created_at INTEGER,
    last_used INTEGER
);

CREATE INDEX IF NOT EXISTS idx_patterns_type ON code_patterns(pattern_type);
CREATE INDEX IF NOT EXISTS idx_patterns_quality ON code_patterns(quality_score);

-- ============================================================================
-- STAGE 2: SANDBOX EXECUTION
-- ============================================================================

-- Sandbox execution history
CREATE TABLE IF NOT EXISTS sandbox_executions (
    execution_id TEXT PRIMARY KEY,
    code_hash TEXT NOT NULL,     -- SHA256 of executed code
    code_snippet TEXT,           -- The actual code executed
    trust_tier TEXT DEFAULT 'sandbox',
    started_at INTEGER,
    completed_at INTEGER,
    duration_ms INTEGER,
    status TEXT NOT NULL,        -- 'running', 'success', 'error', 'timeout', 'killed'
    stdout TEXT,
    stderr TEXT,
    exit_code INTEGER,
    resource_usage TEXT,         -- JSON: {cpu_time, memory_peak, disk_io}
    security_violations TEXT,    -- JSON: [violation1, violation2, ...]
    validated_by TEXT,           -- Agent that validated this execution
    notes TEXT
);

CREATE INDEX IF NOT EXISTS idx_sandbox_hash ON sandbox_executions(code_hash);
CREATE INDEX IF NOT EXISTS idx_sandbox_status ON sandbox_executions(status);
CREATE INDEX IF NOT EXISTS idx_sandbox_started ON sandbox_executions(started_at);

-- Validation rules for code
CREATE TABLE IF NOT EXISTS validation_rules (
    rule_id TEXT PRIMARY KEY,
    rule_name TEXT NOT NULL UNIQUE,
    rule_type TEXT NOT NULL,     -- 'forbidden_import', 'forbidden_call', 'regex_pattern'
    rule_pattern TEXT NOT NULL,  -- Regex or exact match
    severity TEXT DEFAULT 'error', -- 'error', 'warning', 'info'
    description TEXT,
    enabled INTEGER DEFAULT 1,
    created_at INTEGER
);

-- Pre-populate with basic security rules
INSERT OR IGNORE INTO validation_rules (rule_id, rule_name, rule_type, rule_pattern, severity, description, created_at) VALUES
('rule_no_eval', 'No eval()', 'forbidden_call', 'eval\\s*\\(', 'error', 'eval() is dangerous and can execute arbitrary code', strftime('%s', 'now')),
('rule_no_exec', 'No exec()', 'forbidden_call', 'exec\\s*\\(', 'error', 'exec() is dangerous and can execute arbitrary code', strftime('%s', 'now')),
('rule_no_compile', 'No compile()', 'forbidden_call', 'compile\\s*\\(', 'error', 'compile() can create code objects dynamically', strftime('%s', 'now')),
('rule_no_os_system', 'No os.system()', 'forbidden_call', 'os\\.system\\s*\\(', 'error', 'os.system() can execute shell commands', strftime('%s', 'now')),
('rule_no_subprocess_shell', 'No subprocess with shell=True', 'regex_pattern', 'shell\\s*=\\s*True', 'error', 'shell=True in subprocess is dangerous', strftime('%s', 'now')),
('rule_no___import__', 'No __import__()', 'forbidden_call', '__import__\\s*\\(', 'error', '__import__() can import arbitrary modules', strftime('%s', 'now'));

-- ============================================================================
-- STAGE 3: CODE GENERATION
-- ============================================================================

-- Generated code storage
CREATE TABLE IF NOT EXISTS generated_code (
    code_id TEXT PRIMARY KEY,
    request TEXT NOT NULL,            -- Natural language request from user/agent
    specification TEXT,                -- Formal specification generated from request
    generated_code TEXT NOT NULL,
    generated_tests TEXT,
    generated_docs TEXT,
    file_path TEXT,                    -- Where this code should/will be deployed
    language TEXT DEFAULT 'python',
    template_used TEXT,                -- Template name used for generation
    quality_score REAL,
    test_coverage REAL,
    complexity_score REAL,
    deployed INTEGER DEFAULT 0,
    deployment_id TEXT,                -- Link to deployments table
    created_at INTEGER,
    created_by TEXT,                   -- Agent that requested generation
    version INTEGER DEFAULT 1,
    parent_code_id TEXT,               -- If this is an improvement of existing code
    trust_tier TEXT DEFAULT 'sandbox'
);

CREATE INDEX IF NOT EXISTS idx_generated_created ON generated_code(created_at);
CREATE INDEX IF NOT EXISTS idx_generated_deployed ON generated_code(deployed);
CREATE INDEX IF NOT EXISTS idx_generated_creator ON generated_code(created_by);

-- Code improvements tracking
CREATE TABLE IF NOT EXISTS code_improvements (
    improvement_id TEXT PRIMARY KEY,
    original_code_id TEXT NOT NULL,
    improved_code TEXT NOT NULL,
    improvement_type TEXT NOT NULL,   -- 'refactor', 'optimize', 'bugfix', 'enhance'
    description TEXT,
    performance_delta REAL,           -- Improvement in execution time (negative = slower)
    quality_delta REAL,               -- Improvement in quality score
    created_at INTEGER,
    reflection_id TEXT,               -- Link to reflection that triggered improvement
    applied INTEGER DEFAULT 0,
    applied_at INTEGER,
    FOREIGN KEY (original_code_id) REFERENCES generated_code(code_id)
);

CREATE INDEX IF NOT EXISTS idx_improvements_original ON code_improvements(original_code_id);
CREATE INDEX IF NOT EXISTS idx_improvements_type ON code_improvements(improvement_type);

-- ============================================================================
-- STAGE 4: TESTING & VALIDATION
-- ============================================================================

-- Quality reports for generated code
CREATE TABLE IF NOT EXISTS code_quality_reports (
    report_id TEXT PRIMARY KEY,
    code_id TEXT NOT NULL,
    pylint_score REAL,
    mypy_errors INTEGER,
    flake8_issues INTEGER,
    bandit_issues TEXT,              -- JSON: [security issues]
    test_coverage REAL,
    tests_passed INTEGER,
    tests_failed INTEGER,
    tests_total INTEGER,
    cyclomatic_complexity REAL,
    cognitive_complexity REAL,
    documentation_score REAL,       -- Docstring coverage
    overall_quality TEXT,           -- 'excellent', 'good', 'acceptable', 'needs_work', 'reject'
    recommendations TEXT,           -- JSON: [recommendation1, ...]
    created_at INTEGER,
    FOREIGN KEY (code_id) REFERENCES generated_code(code_id)
);

CREATE INDEX IF NOT EXISTS idx_quality_code ON code_quality_reports(code_id);
CREATE INDEX IF NOT EXISTS idx_quality_overall ON code_quality_reports(overall_quality);

-- Approval queue for code deployment
CREATE TABLE IF NOT EXISTS approval_queue (
    queue_id TEXT PRIMARY KEY,
    code_id TEXT NOT NULL,
    status TEXT DEFAULT 'pending',   -- 'pending', 'approved', 'rejected', 'needs_review'
    reviewer TEXT,                   -- 'hrm_auto', 'aletheia', 'human', agent name
    review_notes TEXT,
    quality_threshold_met INTEGER,
    safety_checks_passed INTEGER,
    requires_human_approval INTEGER DEFAULT 0,
    submitted_at INTEGER,
    reviewed_at INTEGER,
    approved_at INTEGER,
    FOREIGN KEY (code_id) REFERENCES generated_code(code_id)
);

CREATE INDEX IF NOT EXISTS idx_approval_status ON approval_queue(status);
CREATE INDEX IF NOT EXISTS idx_approval_submitted ON approval_queue(submitted_at);

-- ============================================================================
-- STAGE 5: DEPLOYMENT
-- ============================================================================

-- Deployment history
CREATE TABLE IF NOT EXISTS deployments (
    deployment_id TEXT PRIMARY KEY,
    code_id TEXT NOT NULL,
    file_path TEXT NOT NULL,
    git_commit TEXT,
    git_branch TEXT DEFAULT 'main',
    backup_path TEXT,               -- Path to backup before deployment
    deployed_at INTEGER,
    deployed_by TEXT,               -- Agent that triggered deployment
    status TEXT NOT NULL,           -- 'success', 'failed', 'rolled_back', 'pending'
    health_check_passed INTEGER,
    rollback_commit TEXT,
    error_message TEXT,
    notes TEXT,
    FOREIGN KEY (code_id) REFERENCES generated_code(code_id)
);

CREATE INDEX IF NOT EXISTS idx_deploy_code ON deployments(code_id);
CREATE INDEX IF NOT EXISTS idx_deploy_status ON deployments(status);
CREATE INDEX IF NOT EXISTS idx_deploy_time ON deployments(deployed_at);

-- Health checks after deployment
CREATE TABLE IF NOT EXISTS deployment_health (
    check_id TEXT PRIMARY KEY,
    deployment_id TEXT NOT NULL,
    check_type TEXT NOT NULL,       -- 'unit_test', 'integration', 'performance', 'smoke'
    check_name TEXT,
    passed INTEGER NOT NULL,
    execution_time_ms INTEGER,
    details TEXT,                   -- JSON: {results}
    checked_at INTEGER,
    FOREIGN KEY (deployment_id) REFERENCES deployments(deployment_id)
);

CREATE INDEX IF NOT EXISTS idx_health_deployment ON deployment_health(deployment_id);
CREATE INDEX IF NOT EXISTS idx_health_type ON deployment_health(check_type);

-- ============================================================================
-- STAGE 6: REFLECTION & EVOLUTION
-- ============================================================================

-- Performance metrics for deployed code
CREATE TABLE IF NOT EXISTS code_performance (
    metric_id TEXT PRIMARY KEY,
    code_id TEXT NOT NULL,
    execution_count INTEGER DEFAULT 0,
    success_count INTEGER DEFAULT 0,
    error_count INTEGER DEFAULT 0,
    avg_execution_time_ms REAL,
    min_execution_time_ms REAL,
    max_execution_time_ms REAL,
    avg_memory_usage_mb REAL,
    success_rate REAL,              -- success_count / execution_count
    user_rating REAL,               -- If user provides feedback
    last_executed INTEGER,
    last_measured INTEGER,
    measurement_window_start INTEGER, -- Start of current measurement window
    FOREIGN KEY (code_id) REFERENCES generated_code(code_id)
);

CREATE INDEX IF NOT EXISTS idx_performance_code ON code_performance(code_id);
CREATE INDEX IF NOT EXISTS idx_performance_rate ON code_performance(success_rate);

-- Improvement tasks generated by reflection
CREATE TABLE IF NOT EXISTS improvement_tasks (
    task_id TEXT PRIMARY KEY,
    code_id TEXT,                   -- NULL if task is for new feature
    task_type TEXT NOT NULL,        -- 'optimize', 'refactor', 'fix_bug', 'enhance', 'new_feature'
    priority TEXT DEFAULT 'medium', -- 'critical', 'high', 'medium', 'low'
    title TEXT NOT NULL,
    description TEXT,
    reflection_id TEXT,             -- Link to reflection that identified this
    performance_issue TEXT,         -- Link to code_performance issue
    estimated_impact TEXT,          -- 'high', 'medium', 'low'
    status TEXT DEFAULT 'pending',  -- 'pending', 'in_progress', 'completed', 'cancelled'
    assigned_to TEXT,               -- Agent assigned to work on this
    created_at INTEGER,
    started_at INTEGER,
    completed_at INTEGER,
    completion_notes TEXT,
    result_code_id TEXT,            -- Generated code that addresses this task
    FOREIGN KEY (code_id) REFERENCES generated_code(code_id)
);

CREATE INDEX IF NOT EXISTS idx_tasks_status ON improvement_tasks(status);
CREATE INDEX IF NOT EXISTS idx_tasks_priority ON improvement_tasks(priority);
CREATE INDEX IF NOT EXISTS idx_tasks_type ON improvement_tasks(task_type);

-- ============================================================================
-- VIEWS FOR COMMON QUERIES
-- ============================================================================

-- View: High-quality generated code ready for deployment
CREATE VIEW IF NOT EXISTS v_deployable_code AS
SELECT 
    gc.code_id,
    gc.request,
    gc.file_path,
    gc.quality_score,
    gc.test_coverage,
    cqr.overall_quality,
    aq.status as approval_status,
    gc.created_at
FROM generated_code gc
LEFT JOIN code_quality_reports cqr ON gc.code_id = cqr.code_id
LEFT JOIN approval_queue aq ON gc.code_id = aq.code_id
WHERE gc.deployed = 0
  AND cqr.overall_quality IN ('excellent', 'good')
  AND aq.status = 'approved';

-- View: Code needing attention
CREATE VIEW IF NOT EXISTS v_code_needs_attention AS
SELECT 
    gc.code_id,
    gc.file_path,
    cp.success_rate,
    cp.error_count,
    cp.execution_count,
    it.task_id,
    it.priority,
    it.task_type
FROM generated_code gc
JOIN code_performance cp ON gc.code_id = cp.code_id
LEFT JOIN improvement_tasks it ON gc.code_id = it.code_id
WHERE gc.deployed = 1
  AND (cp.success_rate < 0.9 OR cp.error_count > 10)
  AND (it.status IS NULL OR it.status = 'pending');

-- View: Sandbox execution summary
CREATE VIEW IF NOT EXISTS v_sandbox_stats AS
SELECT 
    DATE(started_at, 'unixepoch') as execution_date,
    status,
    COUNT(*) as execution_count,
    AVG(duration_ms) as avg_duration_ms,
    SUM(CASE WHEN security_violations IS NOT NULL THEN 1 ELSE 0 END) as violation_count
FROM sandbox_executions
GROUP BY DATE(started_at, 'unixepoch'), status;

-- ============================================================================
-- TRIGGERS FOR AUTOMATION
-- ============================================================================

-- Auto-update code_performance when execution completes
CREATE TRIGGER IF NOT EXISTS update_performance_on_execution
AFTER INSERT ON sandbox_executions
WHEN NEW.status = 'success' AND NEW.code_hash IN (SELECT code_id FROM generated_code)
BEGIN
    INSERT OR REPLACE INTO code_performance (
        metric_id,
        code_id,
        execution_count,
        success_count,
        error_count,
        last_executed,
        last_measured
    ) VALUES (
        'perf_' || NEW.code_hash,
        NEW.code_hash,
        COALESCE((SELECT execution_count FROM code_performance WHERE code_id = NEW.code_hash), 0) + 1,
        COALESCE((SELECT success_count FROM code_performance WHERE code_id = NEW.code_hash), 0) + 1,
        COALESCE((SELECT error_count FROM code_performance WHERE code_id = NEW.code_hash), 0),
        NEW.completed_at,
        strftime('%s', 'now')
    );
END;

-- ============================================================================
-- INITIAL DATA
-- ============================================================================

-- Common code templates (metadata only, actual templates in codegen/templates/)
INSERT OR IGNORE INTO code_patterns (pattern_id, pattern_type, name, description, quality_score, created_at) VALUES
('pattern_fastapi_endpoint', 'function', 'FastAPI Endpoint', 'Standard FastAPI endpoint with error handling', 0.9, strftime('%s', 'now')),
('pattern_async_function', 'function', 'Async Function', 'Async function with proper error handling', 0.85, strftime('%s', 'now')),
('pattern_class_init', 'class', 'Class with __init__', 'Class definition with initialization', 0.8, strftime('%s', 'now')),
('pattern_dataclass', 'class', 'Python Dataclass', 'Dataclass with type hints', 0.9, strftime('%s', 'now')),
('pattern_pytest_test', 'function', 'Pytest Test Function', 'Standard pytest test with fixtures', 0.85, strftime('%s', 'now'));

-- ============================================================================
-- SCHEMA VERSION
-- ============================================================================

CREATE TABLE IF NOT EXISTS schema_version (
    version TEXT PRIMARY KEY,
    applied_at INTEGER,
    description TEXT
);

INSERT OR REPLACE INTO schema_version (version, applied_at, description) VALUES
('phase7_v1.0', strftime('%s', 'now'), 'Initial Phase 7 schema for self-modification and code generation');
