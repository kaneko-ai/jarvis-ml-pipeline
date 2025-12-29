"""Bundle Manifest Generator (Phase 2-ΩΩ).

Generates SHA256 hashes of all bundle files to detect tampering
and ensure integrity of research outputs.
"""
from pathlib import Path
from typing import Dict, Any
import hashlib
import json
import logging

logger = logging.getLogger(__name__)


def _load_qa_summary(run_dir: Path) -> Dict[str, Any]:
    qa_paths = [
        Path("data/runs") / run_dir.name / "qa" / "qa_report.json",
        run_dir / "qa" / "qa_report.json",
    ]
    for qa_path in qa_paths:
        if qa_path.exists():
            with open(qa_path, "r", encoding="utf-8") as f:
                qa_data = json.load(f)
            return {
                "ready_to_submit": qa_data.get("ready_to_submit", False),
                "error_count": qa_data.get("error_count", 0),
                "warn_count": qa_data.get("warn_count", 0),
                "top_errors": qa_data.get("top_errors", []),
            }
    return {}


def calculate_sha256(file_path: Path) -> str:
    """Calculate SHA256 hash of a file.
    
    Args:
        file_path: Path to file
        
    Returns:
        SHA256 hex digest
    """
    sha256_hash = hashlib.sha256()
    
    with open(file_path, "rb") as f:
        # Read in chunks for large files
        for byte_block in iter(lambda: f.read(4096), b""):
            sha256_hash.update(byte_block)
    
    return sha256_hash.hexdigest()


def build_manifest(run_dir: Path) -> Dict[str, Any]:
    """Build manifest with SHA256 hashes of all bundle files.
    
    Args:
        run_dir: Path to run directory
        
    Returns:
        Manifest dict
    """
    manifest = {
        "run_id": run_dir.name,
        "files": {},
        "version": "1.0"
    }
    
    # Required bundle files
    bundle_files = [
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
    
    # Optional Phase 2 files
    optional_files = [
        "cost_report.json",
        "features.jsonl",
        "retrieval_snapshot.json",
    ]
    
    all_files = bundle_files + optional_files
    
    for filename in all_files:
        file_path = run_dir / filename
        
        if file_path.exists():
            try:
                sha256 = calculate_sha256(file_path)
                file_size = file_path.stat().st_size
                
                manifest["files"][filename] = {
                    "sha256": sha256,
                    "size_bytes": file_size,
                    "exists": True
                }
            except Exception as e:
                logger.warning(f"Failed to hash {filename}: {e}")
                manifest["files"][filename] = {
                    "sha256": None,
                    "size_bytes": None,
                    "exists": True,
                    "error": str(e)
                }
        else:
            manifest["files"][filename] = {
                "sha256": None,
                "size_bytes": None,
                "exists": False
            }

    qa_summary = _load_qa_summary(run_dir)
    if qa_summary:
        manifest["qa"] = qa_summary
    
    return manifest


def export_manifest(run_dir: Path) -> Path:
    """Generate and export manifest to bundle.
    
    Args:
        run_dir: Path to run directory
        
    Returns:
        Path to manifest file
    """
    manifest = build_manifest(run_dir)
    
    manifest_path = run_dir / "bundle_manifest.json"
    
    with open(manifest_path, "w", encoding="utf-8") as f:
        json.dump(manifest, f, indent=2, ensure_ascii=False)
    
    logger.info(f"Bundle manifest exported to {manifest_path}")
    
    return manifest_path


def verify_manifest(run_dir: Path) -> Dict[str, Any]:
    """Verify bundle integrity against manifest.
    
    Args:
        run_dir: Path to run directory
        
    Returns:
        Dict with 'valid', 'mismatches', 'errors'
    """
    manifest_path = run_dir / "bundle_manifest.json"
    
    if not manifest_path.exists():
        return {
            "valid": False,
            "errors": ["bundle_manifest.json not found"]
        }
    
    with open(manifest_path, "r", encoding="utf-8") as f:
        manifest = json.load(f)
    
    mismatches = []
    errors = []
    
    for filename, file_info in manifest["files"].items():
        if not file_info["exists"]:
            continue
        
        file_path = run_dir / filename
        
        if not file_path.exists():
            mismatches.append({
                "file": filename,
                "issue": "File missing (was in manifest)"
            })
            continue
        
        expected_sha256 = file_info.get("sha256")
        if expected_sha256 is None:
            continue
        
        try:
            actual_sha256 = calculate_sha256(file_path)
            
            if actual_sha256 != expected_sha256:
                mismatches.append({
                    "file": filename,
                    "issue": "SHA256 mismatch",
                    "expected": expected_sha256,
                    "actual": actual_sha256
                })
        except Exception as e:
            errors.append({
                "file": filename,
                "error": str(e)
            })
    
    valid = len(mismatches) == 0 and len(errors) == 0
    
    return {
        "valid": valid,
        "mismatches": mismatches,
        "errors": errors
    }
