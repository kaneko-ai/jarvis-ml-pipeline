import subprocess
import sys

print("Running bandit low-checker...")
try:
    with open("bandit_remaining.txt", "w", encoding="utf-8") as f:
        # show_bandit_high.py already filters JSON.
        # We need to ensure show_bandit_high.py exists.
        # Assuming it does from previous steps.
        subprocess.call([sys.executable, "tools/show_bandit_high.py"], stdout=f)
except Exception as e:
    print(f"Error running bandit tool: {e}")

print("Running spec lint...")
try:
    with open("lint_remaining.txt", "w", encoding="utf-8") as f:
        subprocess.call([sys.executable, "tools/spec_lint.py"], stdout=f)
except Exception as e:
    print(f"Error running spec lint: {e}")
