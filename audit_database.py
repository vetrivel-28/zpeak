import sqlite3
from pathlib import Path
from knowledge_quality import validate_definition, validate_fake_term

DB_PATH = Path(__file__).parent / "database" / "terms.db"

def main():
    if not DB_PATH.exists():
        print(f"Database not found at {DB_PATH}")
        return

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    cursor.execute("SELECT term, definition, category, aliases, source FROM terms WHERE status='active'")
    rows = cursor.fetchall()
    
    report_lines = ["Database Audit Report", "=====================\n"]
    
    seen_terms = set()
    all_aliases = {}
    
    for row in rows:
        term, definition, category, aliases, source = row
        term_lower = term.lower()
        
        issues = []
        
        # 1. Fake term
        if not validate_fake_term(term):
            issues.append("- Fake Term detected.")
            
        # 2. Suspicious definition
        if not validate_definition(term, definition, category):
            issues.append("- Suspicious/Low-quality definition.")
            
        # 3. Wrong category
        if not category or category.strip().lower() == "other":
            issues.append("- Wrong or missing category.")
            
        # 4. Duplicate term names
        if term_lower in seen_terms:
            issues.append("- Duplicate active term in database.")
        seen_terms.add(term_lower)
        
        # 5. Duplicate aliases
        if aliases:
            alias_list = [a.strip().lower() for a in aliases.split(",") if a.strip()]
            for a in alias_list:
                if a in all_aliases:
                    issues.append(f"- Duplicate alias '{a}' (also used by '{all_aliases[a]}').")
                else:
                    all_aliases[a] = term
                    
        if issues:
            report_lines.append(f"Term: {term} (Source: {source})")
            report_lines.extend(issues)
            report_lines.append("")
            
    conn.close()
    
    if len(report_lines) == 2:
        report_lines.append("No issues found! The database is clean.")
        
    report_text = "\n".join(report_lines)
    
    with open("database_audit_report.txt", "w", encoding="utf-8") as f:
        f.write(report_text)
        
    print("Audit complete. Report generated at database_audit_report.txt")

if __name__ == "__main__":
    main()
