import sqlite3
import pandas as pd
from pathlib import Path

def create_database():
    """Reads terms from CSV and populates the SQLite database."""
    # Define paths using pathlib to avoid hardcoded strings
    base_dir = Path(__file__).parent
    csv_path = base_dir / "data" / "terms.csv"
    db_path = base_dir / "database" / "terms.db"

    # Ensure the database directory exists
    db_path.parent.mkdir(parents=True, exist_ok=True)

    print(f"Reading terms from {csv_path}...")
    try:
        df = pd.read_csv(csv_path)
    except FileNotFoundError:
        print(f"Error: Could not find {csv_path}. Please make sure the CSV exists.")
        return
    except Exception as e:
        print(f"Error reading CSV: {e}")
        return

    print(f"Connecting to database at {db_path}...")
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()

        # Drop table if it exists to replace existing data
        cursor.execute("DROP TABLE IF EXISTS terms")
        cursor.execute("DROP TABLE IF EXISTS review_queue")

        # Create table schema
        cursor.execute("""
            CREATE TABLE terms (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                term TEXT UNIQUE,
                definition TEXT,
                category TEXT,
                term_type TEXT DEFAULT 'Other',
                difficulty TEXT,
                aliases TEXT,
                source TEXT DEFAULT 'manual',
                status TEXT DEFAULT 'active',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)

        print("Inserting data into database...")
        success_count = 0
        
        # Insert each row one by one to handle potential duplicates gracefully
        for _, row in df.iterrows():
            try:
                term_type = row.get('term_type', 'Other')
                cursor.execute(
                    "INSERT INTO terms (term, definition, category, term_type, difficulty, aliases, status) VALUES (?, ?, ?, ?, ?, ?, 'active')",
                    (row['term'], row['definition'], row['category'], term_type, row['difficulty'], row.get('aliases', ''))
                )
                success_count += 1
            except sqlite3.IntegrityError:
                print(f"Warning: Term '{row['term']}' already exists or violates constraint.")
            except Exception as e:
                print(f"Error inserting row '{row['term']}': {e}")

        conn.commit()
        print(f"Successfully loaded {success_count} terms into the database.")
        
    except sqlite3.Error as e:
        print(f"Database error: {e}")
    finally:
        if 'conn' in locals() and conn:
            conn.close()

if __name__ == "__main__":
    create_database()
