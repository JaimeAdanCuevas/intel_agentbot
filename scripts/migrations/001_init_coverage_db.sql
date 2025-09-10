CREATE TABLE IF NOT EXISTS coverage_history (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
    total_instructions INTEGER,
    coverage_percent REAL,
    top_category TEXT,
    test_parameters TEXT
);
