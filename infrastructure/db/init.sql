-- Initialize TimescaleDB for financial data storage
-- This script runs automatically when the database container starts

-- Create the TimescaleDB extension
CREATE EXTENSION IF NOT EXISTS timescaledb;

-- Create table for processed stock data
CREATE TABLE IF NOT EXISTS stock_data_processed (
    id SERIAL PRIMARY KEY,
    symbol VARCHAR(10) NOT NULL,
    price DECIMAL(10, 4) NOT NULL,
    volume BIGINT NOT NULL,
    timestamp TIMESTAMPTZ NOT NULL,
    change DECIMAL(10, 4),
    change_percent DECIMAL(8, 4),
    high DECIMAL(10, 4),
    low DECIMAL(10, 4),
    open DECIMAL(10, 4),
    previous_close DECIMAL(10, 4),
    sma_5 DECIMAL(10, 4),
    sma_20 DECIMAL(10, 4),
    volatility DECIMAL(10, 6),
    momentum DECIMAL(10, 4),
    volume_ma BIGINT,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Convert to hypertable for time-series optimization
SELECT create_hypertable('stock_data_processed', 'timestamp', if_not_exists => TRUE);

-- Create indexes for better query performance
CREATE INDEX IF NOT EXISTS idx_stock_data_symbol_timestamp ON stock_data_processed (symbol, timestamp DESC);
CREATE INDEX IF NOT EXISTS idx_stock_data_timestamp ON stock_data_processed (timestamp DESC);
CREATE INDEX IF NOT EXISTS idx_stock_data_symbol ON stock_data_processed (symbol);

-- Create table for market aggregations
CREATE TABLE IF NOT EXISTS market_summary (
    id SERIAL PRIMARY KEY,
    timestamp TIMESTAMPTZ NOT NULL,
    avg_market_price DECIMAL(10, 4),
    total_volume BIGINT,
    active_symbols INTEGER,
    avg_change_percent DECIMAL(8, 4),
    max_change_percent DECIMAL(8, 4),
    min_change_percent DECIMAL(8, 4),
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Convert to hypertable
SELECT create_hypertable('market_summary', 'timestamp', if_not_exists => TRUE);

-- Create table for alerts
CREATE TABLE IF NOT EXISTS price_alerts (
    id SERIAL PRIMARY KEY,
    user_id VARCHAR(255) NOT NULL,
    symbol VARCHAR(10) NOT NULL,
    target_price DECIMAL(10, 4) NOT NULL,
    condition VARCHAR(10) NOT NULL, -- 'above' or 'below'
    is_active BOOLEAN DEFAULT TRUE,
    triggered_at TIMESTAMPTZ,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Create indexes for alerts
CREATE INDEX IF NOT EXISTS idx_alerts_symbol_active ON price_alerts (symbol, is_active);
CREATE INDEX IF NOT EXISTS idx_alerts_user_id ON price_alerts (user_id);

-- Create a function to clean up old data (data retention policy)
CREATE OR REPLACE FUNCTION cleanup_old_data() 
RETURNS void AS $$
BEGIN
    -- Keep only 30 days of detailed stock data
    DELETE FROM stock_data_processed 
    WHERE timestamp < NOW() - INTERVAL '30 days';
    
    -- Keep only 7 days of market summary data
    DELETE FROM market_summary 
    WHERE timestamp < NOW() - INTERVAL '7 days';
    
    -- Clean up triggered alerts older than 1 day
    DELETE FROM price_alerts 
    WHERE triggered_at IS NOT NULL AND triggered_at < NOW() - INTERVAL '1 day';
    
    RAISE NOTICE 'Data cleanup completed';
END;
$$ LANGUAGE plpgsql;

-- Create a materialized view for quick market stats
CREATE MATERIALIZED VIEW IF NOT EXISTS latest_market_stats AS
WITH latest_prices AS (
    SELECT DISTINCT ON (symbol) 
        symbol, 
        price, 
        change_percent,
        volume,
        timestamp
    FROM stock_data_processed
    ORDER BY symbol, timestamp DESC
)
SELECT 
    COUNT(*) as total_symbols,
    AVG(change_percent) as avg_change_percent,
    MAX(change_percent) as max_change_percent,
    MIN(change_percent) as min_change_percent,
    SUM(volume) as total_volume,
    NOW() as calculated_at
FROM latest_prices;

-- Create index on materialized view
CREATE UNIQUE INDEX IF NOT EXISTS idx_latest_market_stats ON latest_market_stats (calculated_at);

-- Function to refresh the materialized view
CREATE OR REPLACE FUNCTION refresh_market_stats() 
RETURNS void AS $$
BEGIN
    REFRESH MATERIALIZED VIEW latest_market_stats;
    RAISE NOTICE 'Market stats refreshed';
END;
$$ LANGUAGE plpgsql;

-- Sample data insertion (for testing)
INSERT INTO stock_data_processed (
    symbol, price, volume, timestamp, change, change_percent, 
    high, low, open, previous_close
) VALUES 
    ('AAPL', 150.25, 1000000, NOW(), 2.15, 1.45, 151.00, 148.50, 149.00, 148.10),
    ('GOOGL', 2750.80, 500000, NOW(), -15.20, -0.55, 2780.00, 2740.00, 2765.00, 2766.00),
    ('MSFT', 342.15, 800000, NOW(), 5.25, 1.56, 344.00, 340.00, 341.00, 336.90),
    ('TSLA', 245.67, 2000000, NOW(), -8.33, -3.28, 250.00, 244.00, 249.50, 254.00),
    ('NVDA', 465.89, 1200000, NOW(), 12.45, 2.75, 470.00, 460.00, 462.00, 453.44)
ON CONFLICT DO NOTHING;

-- Print success message
DO $$
BEGIN
    RAISE NOTICE 'TimescaleDB initialization completed successfully!';
    RAISE NOTICE 'Created tables: stock_data_processed, market_summary, price_alerts';
    RAISE NOTICE 'Created hypertables for time-series optimization';
    RAISE NOTICE 'Created indexes for query performance';
    RAISE NOTICE 'Sample data inserted for testing';
END $$;