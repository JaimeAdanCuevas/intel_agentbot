import sqlite3
from datetime import datetime
from pathlib import Path

def track_coverage(report: dict, db_path: Path = Path('data/history/coverage.db')):
    conn = sqlite3.connect(db_path)
    c = conn.cursor()
    
    c.execute('''
        INSERT INTO coverage_history 
        (total_instructions, coverage_percent, top_category)
        VALUES (?, ?, ?)
    ''', (
        report['summary']['total_instructions'],
        report['summary']['coverage_percent'],
        report['summary']['top_category']
    ))
    
    conn.commit()
    conn.close()
