-- Tabla de sesiones de IA
CREATE TABLE IF NOT EXISTS ai_sessions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    created_at TEXT DEFAULT (datetime('now')),
    prompt TEXT,
    context TEXT,
    savings REAL DEFAULT 0.00,
    file_path TEXT
);

-- Tabla de archivos recientes
CREATE TABLE IF NOT EXISTS recent_files (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    file_path TEXT,
    created_at TEXT DEFAULT (datetime('now'))
);
