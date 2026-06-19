import sqlite3
import pandas as pd
from pathlib import Path
import sys

def migrate():
    """Migrates the database and CSV to support aliases."""
    base_dir = Path(__file__).parent
    db_path = base_dir / "database" / "terms.db"
    csv_path = base_dir / "data" / "terms.csv"

    if not db_path.exists():
        print(f"Error: Database not found at {db_path}.")
        print("Please run create_db.py first to generate the database.")
        sys.exit(1)

    print("--- Phase 3: Alias Migration ---")

    # 1. Update SQLite DB
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # Check if 'aliases' column already exists
    cursor.execute("PRAGMA table_info(terms)")
    columns = [info[1] for info in cursor.fetchall()]
    
    if "aliases" not in columns:
        print("Adding 'aliases' column to SQLite database...")
        cursor.execute("ALTER TABLE terms ADD COLUMN aliases TEXT")
    else:
        print("'aliases' column already exists in SQLite database.")

    # Populate initial aliases as requested
    aliases_data = {
        "Kubernetes": "k8s",
        "CI/CD": "continuous integration,continuous delivery",
        "API": "application programming interface",
        "JWT": "json web token",
        "LLM": "large language model"
    }

    print("Updating specific terms with aliases in the database...")
    for term, aliases in aliases_data.items():
        cursor.execute("UPDATE terms SET aliases = ? WHERE term = ?", (aliases, term))
    
    conn.commit()
    conn.close()
    print("SQLite database migration complete.\n")

    # 2. Update CSV for future rebuilds using create_db.py
    try:
        print("Loading CSV to update aliases...")
        df = pd.read_csv(csv_path)
        
        # Check if aliases column exists in CSV
        if 'aliases' not in df.columns:
            print("Adding 'aliases' column to CSV...")
            df['aliases'] = ""
        
        print("Updating specific terms with aliases in CSV...")
        for term, aliases in aliases_data.items():
            df.loc[df['term'] == term, 'aliases'] = aliases
            
        # Ensure we write NaN as empty strings
        df.fillna('', inplace=True)
        df.to_csv(csv_path, index=False)
        print("CSV migration complete.")
    except Exception as e:
        print(f"Error updating CSV: {e}")

if __name__ == "__main__":
    migrate()
