import sqlite3
from pathlib import Path

def test_database():
    """Connects to the SQLite database and prints the first 10 rows."""
    base_dir = Path(__file__).parent
    db_path = base_dir / "database" / "terms.db"

    # Check if the database file exists
    if not db_path.exists():
        print(f"Error: Database not found at {db_path}.")
        print("Please run create_db.py first to generate the database.")
        return

    print(f"Connecting to database at {db_path}...\n")
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()

        # Read first 10 rows
        cursor.execute("SELECT id, term, definition, category, difficulty FROM terms LIMIT 10")
        rows = cursor.fetchall()

        if not rows:
            print("Database is empty.")
        else:
            # Print table header
            print(f"{'ID':<4} | {'Term':<25} | {'Category':<15} | {'Difficulty':<12}")
            print("-" * 65)
            
            # Print each row nicely formatted
            for row in rows:
                row_id, term, definition, category, difficulty = row
                print(f"{row_id:<4} | {term:<25} | {category:<15} | {difficulty:<12}")
                print(f"     | Definition: {definition}")
                print("-" * 65)

    except sqlite3.Error as e:
        print(f"SQLite error: {e}")
    finally:
        if 'conn' in locals() and conn:
            conn.close()

if __name__ == "__main__":
    test_database()
