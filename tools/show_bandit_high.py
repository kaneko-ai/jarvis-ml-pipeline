import json
import os

if not os.path.exists("bandit_report.json"):
    print("bandit_report.json not found")
    exit(1)

try:
    with open("bandit_report.json", "r", encoding="utf-8") as f:
        data = json.load(f)
    print(f"Total results: {len(data.get('results', []))}")
    for res in data.get("results", []):
        if res.get("issue_severity") == "HIGH":
            print(
                f"{res.get('filename')} line {res.get('line_number')}: {res.get('issue_text')} ({res.get('test_id')})"
            )
except Exception as e:
    print(f"Error: {e}")
