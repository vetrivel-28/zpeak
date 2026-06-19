import sqlite3
from pathlib import Path

def migrate():
    """Migrates the database to include a table for tracking missing terms."""
    base_dir = Path(__file__).parent
    db_path = base_dir / "database" / "terms.db"

    if not db_path.exists():
        print(f"Error: Database not found at {db_path}.")
        return

    print("--- Phase 4: Missing Terms Migration ---")

    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    print("Creating 'missing_terms' table in SQLite database...")
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS missing_terms (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            term TEXT UNIQUE,
            first_seen DATETIME DEFAULT CURRENT_TIMESTAMP,
            frequency INTEGER DEFAULT 1
        )
    """)
    
    conn.commit()
    conn.close()
    print("SQLite database migration complete.\n")

if __name__ == "__main__":
    migrate()
