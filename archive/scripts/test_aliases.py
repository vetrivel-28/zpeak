from pathlib import Path
import json
from detect_terms import detect_terms

def run_tests():
    """Runs test cases for Alias Detection (Phase 3)"""
    base_dir = Path(__file__).parent
    db_file = base_dir / "database" / "terms.db"
    
    test_cases = [
        "The k8s cluster failed due to continuous integration issues.",
        "Our API uses json web token authentication."
    ]
    
    print("=== Phase 3: Alias Detection Tests ===\n")
    
    for i, text in enumerate(test_cases, 1):
        print(f"--- Test Case {i} ---")
        print(f"Input: \"{text}\"\n")
        
        results = detect_terms(text, db_file)
        
        print("Expected Detection:")
        for r in results:
            print(f"* {r['term']}")
            
        print("\nFull Result Output:")
        print(json.dumps(results, indent=2))
        print("\n" + "="*40 + "\n")

if __name__ == "__main__":
    run_tests()
