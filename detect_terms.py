import sqlite3
import re
from pathlib import Path
import json

def get_all_terms(db_path):
    """Fetches all terms, definitions, categories, and aliases from the database."""
    terms_dict = {}
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Check if aliases column exists (fallback if migration hasn't run)
        cursor.execute("PRAGMA table_info(terms)")
        columns = [info[1] for info in cursor.fetchall()]
        
        has_aliases = "aliases" in columns
        has_term_type = "term_type" in columns
        
        query_cols = "term, definition, category"
        query_cols += ", term_type" if has_term_type else ", 'Other' as term_type"
        query_cols += ", aliases" if has_aliases else ", '' as aliases"
        
        cursor.execute(f"SELECT {query_cols} FROM terms")
            
        for row in cursor.fetchall():
            term, definition, category, term_type, aliases = row
            terms_dict[term] = {
                "definition": definition,
                "category": category,
                "term_type": term_type,
                "aliases": [a.strip() for a in aliases.split(',')] if aliases else []
            }
        conn.close()
    except sqlite3.Error as e:
        print(f"Database error while fetching terms: {e}")
    
    return terms_dict

def detect_terms(text, db_path):
    """
    Detects technical terms in the provided text.
    Returns a list of dictionaries with matched terms and definitions.
    """
    if not Path(db_path).exists():
        print(f"Error: Database not found at {db_path}")
        return []

    terms_dict = get_all_terms(db_path)
    matched_terms = []

    # Build a list of all matching targets (primary terms and aliases)
    search_targets = []
    for term, data in terms_dict.items():
        search_targets.append({"target": term, "canonical": term})
        for alias in data["aliases"]:
            if alias:
                search_targets.append({"target": alias, "canonical": term})

    # Sort search targets by length of the target string in descending order
    # to match longer phrases first and avoid partial matches.
    search_targets.sort(key=lambda x: len(x["target"]), reverse=True)

    # Convert text to lower case to facilitate case-insensitive matching
    text_lower = text.lower()

    # Keep track of canonical terms we've already found to avoid duplicates
    found_canonical_terms = set()

    for item in search_targets:
        target_str = item["target"]
        canonical_term = item["canonical"]
        
        # Create a regex to match the term as a distinct word boundary
        # re.escape is used to safely handle any special characters
        pattern = r'\b' + re.escape(target_str.lower()) + r'\b'
        
        # Check if the term exists in the text
        if re.search(pattern, text_lower):
            if canonical_term.lower() not in found_canonical_terms:
                source = "Regex Match" if target_str.lower() == canonical_term.lower() else "Alias Match"
                matched_terms.append({
                    "term": canonical_term,
                    "matched_text": target_str,
                    "definition": terms_dict[canonical_term]["definition"],
                    "category": terms_dict[canonical_term]["category"],
                    "term_type": terms_dict[canonical_term]["term_type"],
                    "source": source,
                    "confidence": "High"
                })
                found_canonical_terms.add(canonical_term.lower())
                
                # Mask the matched target in the text to prevent nested matches
                text_lower = re.sub(pattern, ' ' * len(target_str), text_lower)

    return matched_terms

if __name__ == "__main__":
    # Define database path using pathlib
    base_dir = Path(__file__).parent
    db_file = base_dir / "database" / "terms.db"

    # Example input from the requirements
    sample_text = "The Kubernetes cluster failed because the CI/CD pipeline triggered a faulty deployment."
    
    print(f"Input text: '{sample_text}'\n")
    print("Detecting terms...\n")
    
    results = detect_terms(sample_text, db_file)
    
    # Print results in a structured JSON format
    if results:
        print("Expected Output:\n")
        print(json.dumps(results, indent=2))
    else:
        print("No terms detected or database is empty.")
