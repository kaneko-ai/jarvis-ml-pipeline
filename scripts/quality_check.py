import sys
import subprocess


def run_check(name: str, command: list[str]) -> bool:
    print(f"Running {name}...")
    try:
        # Use shell=False for security, and handle output encoding safely
        result = subprocess.run(
            command, capture_output=True, text=True, encoding="utf-8", errors="replace"
        )
        if result.returncode == 0:
            print(f"✅ {name} PASSED")
            return True
        else:
            print(f"❌ {name} FAILED (Exit Code: {result.returncode})")
            # Print output while replacing unencodable characters for the current console
            print("--- STDOUT ---")
            print(
                result.stdout.encode(sys.stdout.encoding, errors="replace").decode(
                    sys.stdout.encoding
                )
            )
            print("--- STDERR ---")
            print(
                result.stderr.encode(sys.stderr.encoding, errors="replace").decode(
                    sys.stderr.encoding
                )
            )
            return False
    except Exception as e:
        print(f"❌ {name} ERROR: {e}")
        return False


def main():
    success = True

    # 1. Architecture Gate
    if not run_check("Architecture Gate", [sys.executable, "scripts/arch_gate.py"]):
        success = False

    if not success:
        print("\nQuality checks failed.")
        sys.exit(1)
    else:
        print("\nAll quality checks passed.")
        sys.exit(0)


if __name__ == "__main__":
    main()
