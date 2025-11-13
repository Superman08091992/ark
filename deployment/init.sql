-- ARK Trading Intelligence Database Schema
-- PostgreSQL initialization script

-- Create database (if not exists)
CREATE DATABASE IF NOT EXISTS ark_trading;

-- Connect to database
\c ark_trading;

-- Enable extensions
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- ============================
-- Trade Setups Table
-- ============================
CREATE TABLE IF NOT EXISTS trade_setups (
    setup_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    correlation_id UUID NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    
    -- Symbol & Market
    symbol VARCHAR(20) NOT NULL,
    market_type VARCHAR(20) DEFAULT 'equity',
    direction VARCHAR(10) NOT NULL CHECK (direction IN ('long', 'short', 'swing')),
    
    -- Pattern & Strategy
    pattern VARCHAR(100),
    strategy VARCHAR(100),
    confidence DECIMAL(5,4) CHECK (confidence >= 0 AND confidence <= 1),
    
    -- Price & Volume
    price DECIMAL(12,4) NOT NULL,
    volume BIGINT,
    avg_volume BIGINT,
    
    -- Fundamentals
    float_shares DECIMAL(12,2),
    market_cap DECIMAL(15,2),
    short_interest DECIMAL(5,2),
    
    -- Technical Indicators (JSONB for flexibility)
    indicators JSONB DEFAULT '{}',
    
    -- Catalyst & Sentiment
    catalyst TEXT,
    sentiment VARCHAR(20) CHECK (sentiment IN ('bullish', 'bearish', 'neutral')),
    
    -- Scoring
    scores JSONB DEFAULT '{}',
    
    -- Execution Plan
    execution_plan JSONB DEFAULT '{}',
    
    -- Status & Validation
    status VARCHAR(20) DEFAULT 'pending' CHECK (status IN ('pending', 'approved', 'rejected', 'sent', 'executed')),
    validation_errors JSONB DEFAULT '[]',
    
    -- Agents
    agents_processed TEXT[] DEFAULT '{}',
    
    -- Metadata
    metadata JSONB DEFAULT '{}'
);

-- Indexes
CREATE INDEX idx_trade_setups_symbol ON trade_setups(symbol);
CREATE INDEX idx_trade_setups_correlation_id ON trade_setups(correlation_id);
CREATE INDEX idx_trade_setups_created_at ON trade_setups(created_at DESC);
CREATE INDEX idx_trade_setups_status ON trade_setups(status);
CREATE INDEX idx_trade_setups_direction ON trade_setups(direction);
CREATE INDEX idx_trade_setups_pattern ON trade_setups(pattern);

-- ============================
-- Agent Messages Table
-- ============================
CREATE TABLE IF NOT EXISTS agent_messages (
    message_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    correlation_id UUID NOT NULL,
    causation_id UUID,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    
    -- Routing
    from_agent VARCHAR(50) NOT NULL,
    to_agent VARCHAR(50) NOT NULL,
    message_type VARCHAR(20) NOT NULL,
    
    -- Payload
    payload JSONB DEFAULT '{}',
    
    -- Priority & TTL
    priority INTEGER DEFAULT 5,
    ttl_seconds INTEGER,
    expires_at TIMESTAMP WITH TIME ZONE,
    
    -- Metadata
    metadata JSONB DEFAULT '{}'
);

-- Indexes
CREATE INDEX idx_agent_messages_correlation_id ON agent_messages(correlation_id);
CREATE INDEX idx_agent_messages_created_at ON agent_messages(created_at DESC);
CREATE INDEX idx_agent_messages_from_agent ON agent_messages(from_agent);
CREATE INDEX idx_agent_messages_to_agent ON agent_messages(to_agent);

-- ============================
-- Error Log Table
-- ============================
CREATE TABLE IF NOT EXISTS error_log (
    error_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    correlation_id UUID,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    
    -- Error Details
    agent_name VARCHAR(50) NOT NULL,
    error_message TEXT NOT NULL,
    error_code VARCHAR(50),
    severity VARCHAR(20) NOT NULL CHECK (severity IN ('DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL')),
    
    -- Context
    exception_type VARCHAR(100),
    stack_trace TEXT,
    context JSONB DEFAULT '{}',
    
    -- Recovery
    retry_count INTEGER DEFAULT 0,
    resolved BOOLEAN DEFAULT FALSE,
    resolved_at TIMESTAMP WITH TIME ZONE
);

-- Indexes
CREATE INDEX idx_error_log_correlation_id ON error_log(correlation_id);
CREATE INDEX idx_error_log_created_at ON error_log(created_at DESC);
CREATE INDEX idx_error_log_severity ON error_log(severity);
CREATE INDEX idx_error_log_agent_name ON error_log(agent_name);
CREATE INDEX idx_error_log_resolved ON error_log(resolved) WHERE NOT resolved;

-- ============================
-- Signal History Table
-- ============================
CREATE TABLE IF NOT EXISTS signal_history (
    signal_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    setup_id UUID REFERENCES trade_setups(setup_id),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    
    -- Signal Details
    symbol VARCHAR(20) NOT NULL,
    direction VARCHAR(10) NOT NULL,
    entry_price DECIMAL(12,4),
    stop_loss DECIMAL(12,4),
    target_price DECIMAL(12,4),
    
    -- Execution
    executed BOOLEAN DEFAULT FALSE,
    executed_at TIMESTAMP WITH TIME ZONE,
    fill_price DECIMAL(12,4),
    position_size INTEGER,
    
    -- Results
    closed BOOLEAN DEFAULT FALSE,
    closed_at TIMESTAMP WITH TIME ZONE,
    close_price DECIMAL(12,4),
    pnl DECIMAL(12,2),
    pnl_percent DECIMAL(7,4),
    
    -- Metadata
    metadata JSONB DEFAULT '{}'
);

-- Indexes
CREATE INDEX idx_signal_history_symbol ON signal_history(symbol);
CREATE INDEX idx_signal_history_created_at ON signal_history(created_at DESC);
CREATE INDEX idx_signal_history_executed ON signal_history(executed);
CREATE INDEX idx_signal_history_closed ON signal_history(closed);

-- ============================
-- Pattern Performance Table
-- ============================
CREATE TABLE IF NOT EXISTS pattern_performance (
    id SERIAL PRIMARY KEY,
    pattern_name VARCHAR(100) NOT NULL,
    date DATE NOT NULL DEFAULT CURRENT_DATE,
    
    -- Counts
    total_signals INTEGER DEFAULT 0,
    winning_signals INTEGER DEFAULT 0,
    losing_signals INTEGER DEFAULT 0,
    
    -- Win Rate
    win_rate DECIMAL(5,4),
    
    -- P&L
    total_pnl DECIMAL(12,2) DEFAULT 0,
    avg_pnl DECIMAL(12,2),
    
    -- Confidence
    avg_confidence DECIMAL(5,4),
    
    UNIQUE(pattern_name, date)
);

-- Indexes
CREATE INDEX idx_pattern_performance_date ON pattern_performance(date DESC);
CREATE INDEX idx_pattern_performance_pattern ON pattern_performance(pattern_name);

-- ============================
-- Views
-- ============================

-- Active Signals View
CREATE OR REPLACE VIEW active_signals AS
SELECT 
    s.signal_id,
    s.symbol,
    s.direction,
    s.entry_price,
    s.stop_loss,
    s.target_price,
    s.executed,
    s.executed_at,
    t.pattern,
    t.confidence,
    EXTRACT(EPOCH FROM (NOW() - s.created_at)) / 3600 as age_hours
FROM signal_history s
LEFT JOIN trade_setups t ON s.setup_id = t.setup_id
WHERE s.executed = TRUE AND s.closed = FALSE
ORDER BY s.executed_at DESC;

-- Daily Performance View
CREATE OR REPLACE VIEW daily_performance AS
SELECT 
    DATE(created_at) as trade_date,
    COUNT(*) as total_signals,
    SUM(CASE WHEN pnl > 0 THEN 1 ELSE 0 END) as winners,
    SUM(CASE WHEN pnl < 0 THEN 1 ELSE 0 END) as losers,
    ROUND(SUM(CASE WHEN pnl > 0 THEN 1 ELSE 0 END)::NUMERIC / NULLIF(COUNT(*), 0), 4) as win_rate,
    SUM(pnl) as total_pnl,
    AVG(pnl) as avg_pnl
FROM signal_history
WHERE closed = TRUE
GROUP BY DATE(created_at)
ORDER BY trade_date DESC;

-- Pattern Leaderboard View
CREATE OR REPLACE VIEW pattern_leaderboard AS
SELECT 
    pattern,
    COUNT(*) as total_trades,
    SUM(CASE WHEN sh.pnl > 0 THEN 1 ELSE 0 END) as winners,
    ROUND(SUM(CASE WHEN sh.pnl > 0 THEN 1 ELSE 0 END)::NUMERIC / NULLIF(COUNT(*), 0), 4) as win_rate,
    AVG(confidence) as avg_confidence,
    SUM(sh.pnl) as total_pnl,
    AVG(sh.pnl) as avg_pnl
FROM trade_setups t
LEFT JOIN signal_history sh ON t.setup_id = sh.setup_id
WHERE sh.closed = TRUE
GROUP BY pattern
ORDER BY total_pnl DESC;

-- ============================
-- Functions
-- ============================

-- Update updated_at timestamp
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ language 'plpgsql';

-- Trigger for trade_setups
CREATE TRIGGER update_trade_setups_updated_at BEFORE UPDATE ON trade_setups
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- Calculate win rate for patterns
CREATE OR REPLACE FUNCTION calculate_pattern_win_rate(p_pattern_name VARCHAR)
RETURNS TABLE(
    pattern_name VARCHAR,
    total_trades BIGINT,
    winners BIGINT,
    win_rate DECIMAL,
    total_pnl DECIMAL
) AS $$
BEGIN
    RETURN QUERY
    SELECT 
        p_pattern_name,
        COUNT(*) as total_trades,
        SUM(CASE WHEN sh.pnl > 0 THEN 1 ELSE 0 END) as winners,
        ROUND(SUM(CASE WHEN sh.pnl > 0 THEN 1 ELSE 0 END)::NUMERIC / NULLIF(COUNT(*), 0), 4) as win_rate,
        SUM(sh.pnl) as total_pnl
    FROM trade_setups t
    LEFT JOIN signal_history sh ON t.setup_id = sh.setup_id
    WHERE t.pattern = p_pattern_name AND sh.closed = TRUE
    GROUP BY p_pattern_name;
END;
$$ LANGUAGE plpgsql;

-- ============================
-- Sample Data (Optional)
-- ============================

-- Insert sample trade setup
-- INSERT INTO trade_setups (
--     correlation_id, symbol, direction, price, pattern, confidence, status
-- ) VALUES (
--     uuid_generate_v4(), 'TSLA', 'long', 250.50, 'Squeezer', 0.85, 'approved'
-- );

-- ============================
-- Permissions
-- ============================

-- Grant permissions to arkuser
GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA public TO arkuser;
GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA public TO arkuser;
GRANT EXECUTE ON ALL FUNCTIONS IN SCHEMA public TO arkuser;
