import sqlite3
from pathlib import Path

def migrate():
    base_dir = Path(__file__).parent
    db_path = base_dir / "database" / "terms.db"

    print(f"Migrating database at {db_path}...")
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()

        # Check if the columns already exist
        cursor.execute("PRAGMA table_info(terms)")
        columns = [info[1] for info in cursor.fetchall()]

        if "source" not in columns:
            print("Adding 'source' and 'created_at' columns to 'terms' table...")
            
            # Rename existing table
            cursor.execute("ALTER TABLE terms RENAME TO terms_old")
            
            # Create new table with updated schema
            cursor.execute("""
                CREATE TABLE terms (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    term TEXT UNIQUE,
                    definition TEXT,
                    category TEXT,
                    difficulty TEXT,
                    aliases TEXT,
                    source TEXT DEFAULT 'manual',
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            # Copy data
            cursor.execute("""
                INSERT INTO terms (id, term, definition, category, difficulty, aliases)
                SELECT id, term, definition, category, difficulty, aliases FROM terms_old
            """)
            
            # Drop old table
            cursor.execute("DROP TABLE terms_old")
            
            conn.commit()
            print("Migration completed successfully.")
        else:
            print("Database schema is already up to date.")
            
    except sqlite3.Error as e:
        print(f"Database error during migration: {e}")
    finally:
        if 'conn' in locals() and conn:
            conn.close()

if __name__ == "__main__":
    migrate()
