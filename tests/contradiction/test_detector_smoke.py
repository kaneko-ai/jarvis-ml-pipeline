import sys
from pathlib import Path
from jarvis_core.contradiction.detector import ContradictionDetector
sys.path.append(str(Path(__file__).parents[3]))


def test_contradiction_smoke():
    detector = ContradictionDetector()
    
    claims = [
        "Drug A significantly increases blood pressure.",
        "Drug A significantly decreases blood pressure.",
        "Drug B is safe.",
    ]
    
    contradictions = detector.detect(claims)
    
    # Needs to find at least one contradiction between 0 and 1
    found = False
    for c in contradictions:
        if "increases" in c.statement_a and "decreases" in c.statement_b:
            found = True
        elif "decreases" in c.statement_a and "increases" in c.statement_b:
            found = True
            
    assert found, "Failed to detect 'increase' vs 'decrease' contradiction"

def test_no_contradiction():
    detector = ContradictionDetector()
    claims = [
        "Drug A increases blood pressure.",
        "Drug A increases heart rate.",
    ]
    
    contradictions = detector.detect(claims)
    assert len(contradictions) == 0
