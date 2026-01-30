import json
from pathlib import Path
import tempfile


class BundleValidator:
    REQUIRED_FILES = [
        "input.json",
        "run_config.json",
        "papers.jsonl",
        "claims.jsonl",
        "evidence.jsonl",
        "scores.json",
        "result.json",
        "eval_summary.json",
        "warnings.jsonl",
        "report.md",
    ]

    def validate(self, bundle_path: Path) -> list[str]:
        errors = []
        # 1. Existence Check
        for f in self.REQUIRED_FILES:
            if not (bundle_path / f).exists():
                errors.append(f"Missing required file: {f}")

        # 2. Schema Check (Basic keys)
        if (bundle_path / "result.json").exists():
            try:
                data = json.loads((bundle_path / "result.json").read_text(encoding="utf-8"))
                for key in ["run_id", "status", "answer", "citations"]:
                    if key not in data:
                        errors.append(f"result.json missing key: {key}")
            except Exception as e:
                errors.append(f"result.json parse error: {e}")

        if (bundle_path / "eval_summary.json").exists():
            try:
                data = json.loads((bundle_path / "eval_summary.json").read_text(encoding="utf-8"))
                for key in ["gate_passed", "fail_reasons", "metrics"]:
                    if key not in data:
                        errors.append(f"eval_summary.json missing key: {key}")

                # Consistency check: gate_passed=false should mean status is failed (conceptual)
                # But here we just check if it matches result.json if we have it
                if (bundle_path / "result.json").exists():
                    res_data = json.loads((bundle_path / "result.json").read_text())
                    if not data.get("gate_passed") and res_data.get("status") == "success":
                        errors.append(
                            "Consistency error: gate_passed=False but result status=success"
                        )
            except Exception as e:
                errors.append(f"eval_summary.json validation error: {e}")

        return errors


def test_bundle_contract_full_pass():
    validator = BundleValidator()
    with tempfile.TemporaryDirectory() as tmpdir:
        p = Path(tmpdir)
        # Create all required files
        for f in validator.REQUIRED_FILES:
            (p / f).write_text("{}" if f.endswith(".json") else "", encoding="utf-8")

        # Populate result.json
        (p / "result.json").write_text(
            json.dumps({"run_id": "r1", "status": "success", "answer": "a", "citations": []})
        )
        # Populate eval_summary.json
        (p / "eval_summary.json").write_text(
            json.dumps({"gate_passed": True, "fail_reasons": [], "metrics": {}})
        )

        errors = validator.validate(p)
        assert not errors


def test_bundle_contract_missing_files():
    validator = BundleValidator()
    with tempfile.TemporaryDirectory() as tmpdir:
        p = Path(tmpdir)
        (p / "input.json").write_text("{}")
        errors = validator.validate(p)
        assert len(errors) > 0
        assert any("Missing required file: result.json" in e for e in errors)


def test_bundle_contract_schema_violation():
    validator = BundleValidator()
    with tempfile.TemporaryDirectory() as tmpdir:
        p = Path(tmpdir)
        for f in validator.REQUIRED_FILES:
            (p / f).write_text("{}")

        # Corrupt result.json
        (p / "result.json").write_text(json.dumps({"wrong": "keys"}))

        errors = validator.validate(p)
        assert any("result.json missing key: run_id" in e for e in errors)


def test_bundle_contract_inconsistency():
    validator = BundleValidator()
    with tempfile.TemporaryDirectory() as tmpdir:
        p = Path(tmpdir)
        for f in validator.REQUIRED_FILES:
            (p / f).write_text("{}")

        (p / "result.json").write_text(
            json.dumps({"run_id": "r1", "status": "success", "answer": "a", "citations": []})
        )
        (p / "eval_summary.json").write_text(
            json.dumps({"gate_passed": False, "fail_reasons": ["FAIL"], "metrics": {}})
        )

        errors = validator.validate(p)
        assert any("Consistency error" in e for e in errors)