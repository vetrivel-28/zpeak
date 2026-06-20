import sqlite3
from pathlib import Path

DB_PATH = Path(__file__).parent / "database" / "terms.db"

authoritative_terms = [
    ("LangGraph", "Framework for building stateful LLM workflows and agent systems.", "AI/ML", "Framework"),
    ("CrewAI", "Multi-agent orchestration framework for collaborative AI agents.", "AI/ML", "Framework"),
    ("OpenTelemetry", "Observability framework for collecting traces, metrics, and logs.", "Observability", "Framework"),
    ("Agno", "Agent framework for building AI applications.", "AI/ML", "Framework")
]

def main():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    for term, definition, category, term_type in authoritative_terms:
        # Check if exists
        cursor.execute("SELECT id FROM terms WHERE term=? COLLATE NOCASE", (term,))
        row = cursor.fetchone()
        
        if row:
            cursor.execute(
                "UPDATE terms SET definition=?, category=?, term_type=?, source='authoritative', status='active' WHERE id=?",
                (definition, category, term_type, row[0])
            )
            print(f"Updated {term}")
        else:
            cursor.execute(
                "INSERT INTO terms (term, definition, category, term_type, difficulty, aliases, source, status) VALUES (?, ?, ?, ?, 'Intermediate', '', 'authoritative', 'active')",
                (term, definition, category, term_type)
            )
            print(f"Inserted {term}")
            
    conn.commit()
    conn.close()

if __name__ == "__main__":
    main()
