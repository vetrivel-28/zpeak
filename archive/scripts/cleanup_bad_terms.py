import argparse
import sqlite3
from pathlib import Path
from knowledge_quality import validate_definition, validate_fake_term

DB_PATH = Path(__file__).parent / "database" / "terms.db"

def main():
    parser = argparse.ArgumentParser(description="Clean up bad or hallucinated terms from the database.")
    parser.add_argument("--dry-run", action="store_true", help="Show terms to be deleted without actually deleting them.")
    parser.add_argument("--apply", action="store_true", help="Actually delete the bad terms from the database.")
    args = parser.parse_args()

    if not args.dry_run and not args.apply:
        print("Please specify --dry-run or --apply")
        return

    if not DB_PATH.exists():
        print(f"Database not found at {DB_PATH}")
        return

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    cursor.execute("SELECT term, definition, category, source FROM terms WHERE status='active'")
    rows = cursor.fetchall()
    
    to_delete = []
    
    for row in rows:
        term, definition, category, source = row
        
        is_fake = not validate_fake_term(term)
        is_bad_def = not validate_definition(term, definition, category)
        
        if (is_fake or is_bad_def) and source == 'AI Extraction':
            to_delete.append(term)
            if args.dry_run:
                reason = "Fake Term" if is_fake else "Bad Definition"
                print(f"[DRY RUN] Will delete: '{term}' (Reason: {reason})")
                
    if args.apply:
        if not to_delete:
            print("No bad terms found to delete.")
        else:
            for term in to_delete:
                cursor.execute("DELETE FROM terms WHERE term=?", (term,))
            conn.commit()
            print(f"Successfully deleted {len(to_delete)} bad terms.")
            
    conn.close()

if __name__ == "__main__":
    main()
