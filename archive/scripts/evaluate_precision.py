import json
from pathlib import Path
from knowledge_manager import process_transcript

def run_evaluation():
    db_path = Path(__file__).parent / "database" / "terms.db"
    
    # Ground truth
    tests = [
        {
            "transcript": "Let's circle back and align stakeholders before finalizing the roadmap.",
            "expected": {"circle back", "stakeholders", "roadmap", "align"} 
        },
        {
            "transcript": "The LangGraph workflow uses OpenTelemetry and DSPy.",
            "expected": {"LangGraph", "OpenTelemetry", "DSPy"}
        },
        {
            "transcript": "Vetrivel discussed lunch plans with Rahul near the library yesterday.",
            "expected": set()
        },
        {
            "transcript": "We used SMOTE before training XGBoost and evaluated ROC-AUC.",
            "expected": {"SMOTE", "XGBoost", "ROC-AUC"}
        },
        {
            "transcript": "The Helm deployment failed after a rollback inside Kubernetes.",
            "expected": {"Helm", "rollback", "Kubernetes"}
        }
    ]
    
    true_positives = 0
    false_positives = 0
    total_extracted = 0
    total_expected = 0
    
    print("--- Precision Evaluation ---")
    
    for i, test in enumerate(tests):
        print(f"\nTest {i+1}: {test['transcript']}")
        
        result = process_transcript(test["transcript"], db_path)
        
        extracted = set()
        for k in result.get("known_terms", []):
            extracted.add(k["term"].lower())
        for u in result.get("newly_learned_terms", []):
            if u["saved"]:
                extracted.add(u["term"].lower())
                
        expected_lower = {e.lower() for e in test["expected"]}
        
        print(f"Extracted: {extracted}")
        print(f"Expected:  {expected_lower}")
        
        # Calculate
        for ext in extracted:
            matched = False
            for exp in expected_lower:
                if ext in exp or exp in ext:
                    matched = True
                    break
            
            if matched:
                true_positives += 1
            else:
                false_positives += 1
                print(f"  False Positive: {ext}")
                
        total_extracted += len(extracted)
        total_expected += len(expected_lower)

    precision = 0
    if total_extracted > 0:
        precision = (true_positives / total_extracted) * 100
        
    false_positive_rate = 0
    if total_extracted > 0:
        false_positive_rate = (false_positives / total_extracted) * 100
        
    print("\n--- Summary ---")
    print(f"True Positives:  {true_positives}")
    print(f"False Positives: {false_positives}")
    print(f"Precision:       {precision:.2f}%")
    print(f"False Pos. Rate: {false_positive_rate:.2f}%")
    
    if precision >= 90 and false_positive_rate <= 10:
        print("\nPASSED (Precision >= 90%, FP <= 10%)")
    else:
        print("\nFAILED")

if __name__ == "__main__":
    run_evaluation()
