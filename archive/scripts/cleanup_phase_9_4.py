import sqlite3
import os

DB_PATH = os.path.join(os.path.dirname(__file__), '..', 'database', 'terms.db')

BAD_TERMS = [
    'Land', 'Graph', 'Telement', 'DEP', 'FA', 'WebCam',
    'Font', 'English', 'Subject', 'Hello', 'Plan'
]

def cleanup():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    placeholders = ','.join(['?'] * len(BAD_TERMS))
    
    # First, let's see how many there are
    cursor.execute(f"SELECT COUNT(*) FROM terms WHERE term IN ({placeholders})", BAD_TERMS)
    count = cursor.fetchone()[0]
    
    query = f"DELETE FROM terms WHERE term IN ({placeholders})"
    
    cursor.execute(query, BAD_TERMS)
    conn.commit()
    
    report_path = os.path.join(os.path.dirname(__file__), '..', 'database_phase_9_4_cleanup.txt')
    with open(report_path, 'w') as f:
        f.write("=== PHASE 9.4 DATABASE CLEANUP ===\n\n")
        f.write(f"Deleted {count} bad terms from the database.\n")
        f.write(f"Terms targeted: {', '.join(BAD_TERMS)}\n")
                
    print(f"Cleanup saved to {report_path}")
    conn.close()

if __name__ == '__main__':
    cleanup()
