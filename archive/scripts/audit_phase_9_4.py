import sqlite3
import os

DB_PATH = os.path.join(os.path.dirname(__file__), '..', 'database', 'terms.db')

BAD_TERMS = [
    'Land', 'Graph', 'Telement', 'DEP', 'FA', 'WebCam',
    'Font', 'English', 'Subject', 'Hello', 'Plan'
]

def audit():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    placeholders = ','.join(['?'] * len(BAD_TERMS))
    query = f"SELECT term, category, definition, source, created_at FROM terms WHERE term IN ({placeholders})"
    
    cursor.execute(query, BAD_TERMS)
    results = cursor.fetchall()
    
    report_path = os.path.join(os.path.dirname(__file__), '..', 'database_phase_9_4_audit.txt')
    with open(report_path, 'w') as f:
        f.write("=== PHASE 9.4 DATABASE AUDIT ===\n\n")
        if not results:
            f.write("No bad terms found.\n")
        else:
            for row in results:
                f.write(f"Term: {row[0]}\n")
                f.write(f"Category: {row[1]}\n")
                f.write(f"Definition: {row[2]}\n")
                f.write(f"Source: {row[3]}\n")
                f.write(f"Created: {row[4]}\n")
                f.write("-" * 40 + "\n")
                
    print(f"Audit saved to {report_path}")
    conn.close()

if __name__ == '__main__':
    audit()
