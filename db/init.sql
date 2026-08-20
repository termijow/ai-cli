-- Base de datos de métricas AI-CLI (valores en COP)
CREATE TABLE IF NOT EXISTS usage_logs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    created_at TEXT DEFAULT (datetime('now')),
    input_tokens INTEGER DEFAULT 0,
    output_tokens INTEGER DEFAULT 0,
    input_cost REAL DEFAULT 0.00,
    output_savings REAL DEFAULT 0.00,
    total_savings REAL DEFAULT 0.00
);

CREATE TABLE IF NOT EXISTS config (
    key TEXT PRIMARY KEY,
    value TEXT
);

-- Insertar datos de configuración iniciales (precios en USD)
INSERT OR REPLACE INTO config (key, value) VALUES
    ('input_price', '5.00'),
    ('output_price', '25.00');
