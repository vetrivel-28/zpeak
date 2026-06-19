import sqlite3
from pathlib import Path
from stopwords import check_rejection

def run_cleanup():
    db_path = Path(__file__).parent / "database" / "terms.db"
    if not db_path.exists():
        print(f"Database not found at {db_path}")
        return

    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # Select active terms
    cursor.execute("SELECT id, term, category, source, created_at FROM terms WHERE status='active'")
    rows = cursor.fetchall()
    
    flagged = []
    for row in rows:
        term_id, term, category, source, created_at = row
        if check_rejection(term)[0] or len(term) < 2 or term.isnumeric():
            flagged.append(row)
            
    if not flagged:
        print("No suspicious terms found. Database is clean!")
        conn.close()
        return
        
    print(f"\n--- Found {len(flagged)} suspicious terms ---")
    print(f"{'ID':<5} | {'Term':<25} | {'Category':<20} | {'Source':<15} | {'Created At'}")
    print("-" * 85)
    for row in flagged:
        term_id, term, category, source, created_at = row
        print(f"{term_id:<5} | {term:<25} | {category:<20} | {source:<15} | {created_at}")
        
    print("-" * 85)
    print("Options:")
    print("1. Delete all flagged terms")
    print("2. Delete specific term ID")
    print("3. Exit")
    
    choice = input("Enter choice (1/2/3): ").strip()
    
    if choice == '1':
        ids_to_delete = [str(r[0]) for r in flagged]
        placeholders = ",".join("?" * len(ids_to_delete))
        cursor.execute(f"UPDATE terms SET status='deleted' WHERE id IN ({placeholders})", ids_to_delete)
        conn.commit()
        print(f"Successfully deleted {len(flagged)} terms.")
    elif choice == '2':
        term_id = input("Enter ID to delete: ").strip()
        if term_id.isdigit():
            cursor.execute("UPDATE terms SET status='deleted' WHERE id=?", (term_id,))
            conn.commit()
            print(f"Successfully deleted term ID {term_id}.")
        else:
            print("Invalid ID.")
    else:
        print("Exiting without changes.")
        
    conn.close()

if __name__ == "__main__":
    run_cleanup()
