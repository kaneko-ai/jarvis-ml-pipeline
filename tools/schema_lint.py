#!/usr/bin/env python
"""Schema Linter for Phase 2 Artifacts.

Verifies that JSONL files comply with Phase 2 Schemas.
Usage:
    python tools/schema_lint.py logs/runs/{run_id}/
"""
import argparse
import json
import logging
from pathlib import Path
from typing import Dict
import sys

# Configure logging
logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
logger = logging.getLogger("SchemaLint")

SCHEMAS_DIR = Path("docs/SCHEMAS")


def load_schema(name: str) -> Dict:
    schema_path = SCHEMAS_DIR / f"{name}.schema.json"
    if not schema_path.exists():
        logger.error(f"Schema not found: {schema_path}")
        sys.exit(1)
    with open(schema_path, "r", encoding="utf-8") as f:
        return json.load(f)


def validate_jsonl(file_path: Path, schema: Dict) -> bool:
    if not file_path.exists():
        logger.warning(f"File not found: {file_path}")
        return False

    # Simple validation implementation (in production, use jsonschema library)
    # Here we check required fields manually to avoid heavy dependencies
    required_fields = schema.get("required", [])
    valid = True

    try:
        with open(file_path, "r", encoding="utf-8") as f:
            for i, line in enumerate(f):
                if not line.strip():
                    continue
                try:
                    data = json.loads(line)
                    for field in required_fields:
                        if field not in data:
                            logger.error(
                                f"{file_path.name} L{i+1}: Missing required field '{field}'"
                            )
                            valid = False
                except json.JSONDecodeError:
                    logger.error(f"{file_path.name} L{i+1}: Invalid JSON")
                    valid = False
    except Exception as e:
        logger.error(f"Error reading {file_path}: {e}")
        return False

    return valid


def main():
    parser = argparse.ArgumentParser(description="Schema Linter")
    parser.add_argument("run_dir", help="Path to run directory")
    args = parser.parse_args()

    run_path = Path(args.run_dir)
    if not run_path.exists():
        logger.error(f"Run directory not found: {run_path}")
        sys.exit(1)

    logger.info(f"Linting run: {run_path}")

    # 1. Validate claims.jsonl
    claims_schema = load_schema("claim_unit")
    claims_valid = validate_jsonl(run_path / "claims.jsonl", claims_schema)

    # 2. Validate evidence.jsonl
    evidence_schema = load_schema("evidence_unit")
    evidence_valid = validate_jsonl(run_path / "evidence.jsonl", evidence_schema)

    if claims_valid and evidence_valid:
        logger.info("✅ All artifacts are valid against Phase 2 schemas.")
        sys.exit(0)
    else:
        logger.error("❌ Schema validation failed.")
        sys.exit(1)


if __name__ == "__main__":
    main()
