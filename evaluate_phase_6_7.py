import json
from pathlib import Path
from knowledge_manager import process_transcript

def run_evaluation():
    db_path = Path(__file__).parent / "database" / "terms.db"
    
    # Ground truth
    tests = [
        {
            "transcript": "Hey guys, yesterday I worked on LangGraph and Kubernetes.",
            "expected": {"LangGraph", "Kubernetes"}
        },
        {
            "transcript": "The deployment failed around 2 PM.",
            "expected": {"deployment"}
        },
        {
            "transcript": "I'll check OpenTelemetry tomorrow.",
            "expected": {"OpenTelemetry"}
        },
        {
            "transcript": "Rahul worked on CrewAI.",
            "expected": {"CrewAI"}
        },
        {
            "transcript": "Let's circle back with stakeholders after the roadmap review.",
            "expected": {"circle back", "stakeholders", "roadmap"}
        },
        {
            "transcript": "We deployed a canary deployment with service mesh enabled.",
            "expected": {"canary deployment", "service mesh"}
        }
    ]
    
    true_positives = 0
    false_positives = 0
    total_extracted = 0
    total_expected = 0
    
    print("--- Phase 6.7 Precision Evaluation ---")
    
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
    
    if precision >= 95 and false_positive_rate <= 5:
        print("\nPASSED (Precision >= 95%, FP <= 5%)")
    else:
        print("\nFAILED")

if __name__ == "__main__":
    run_evaluation()
