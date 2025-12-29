"""FastAPI Web Application (AG-05〜AG-07).

Per RP-167 and BUNDLE_CONTRACT.md, provides HTTP API for JARVIS.
- Run management (logs/runs/ based)
- File upload (PDF/BibTeX/ZIP)
- Dashboard data
"""
from __future__ import annotations

import hashlib
import json
import os
import re
import shutil
import tempfile
import zipfile
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, List, Optional

try:
    from fastapi import FastAPI, HTTPException, Depends, UploadFile, File
    from fastapi.responses import FileResponse
    from fastapi.middleware.cors import CORSMiddleware
    from pydantic import BaseModel

    FASTAPI_AVAILABLE = True
except ImportError:
    FASTAPI_AVAILABLE = False
    FastAPI = None
    HTTPException = None
    BaseModel = object

if FASTAPI_AVAILABLE:
    from jarvis_web.routes.submission import router as submission_router
else:
    submission_router = None


# Constants
RUNS_DIR = Path("data/runs")
LEGACY_RUNS_DIR = Path("logs/runs")
UPLOADS_DIR = Path("data/uploads")
MAX_UPLOAD_SIZE = 100 * 1024 * 1024  # 100MB per file
MAX_BATCH_FILES = 100


# Create app if FastAPI available
if FASTAPI_AVAILABLE:
    from jarvis_web.auth import verify_api_token, verify_token
    from jarvis_web.routes.research import router as research_router
    from jarvis_web.routes.finance import router as finance_router
    from jarvis_web.routes.schedules import router as schedules_router
    from jarvis_web.routes.cron import router as cron_router
    from jarvis_web.routes.queue import router as queue_router

    app = FastAPI(
        title="JARVIS Research OS",
        description="API for paper survey and knowledge synthesis",
        version="4.3.0",
    )

    from jarvis_web.routes.finance import router as finance_router
    
    # Add CORS middleware to allow cross-origin requests (for GitHub Pages dashboard)
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],  # Allow all origins for local development
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    app.include_router(research_router)
    app.include_router(finance_router)
    app.include_router(schedules_router)
    app.include_router(cron_router)
    app.include_router(queue_router)
else:
    app = None


# Request/Response models
class RunRequest(BaseModel):
    """Request to start a run."""
    query: str
    max_papers: int = 10
    seed: int = 42
    config: dict = {}


class RunResponse(BaseModel):
    """Response from a run."""
    run_id: str
    status: str
    message: str


class RunSummary(BaseModel):
    """Summary of a run."""
    run_id: str
    status: str
    timestamp: str
    gate_passed: bool
    contract_valid: bool
    metrics: dict
    qa_ready: bool = False
    qa_error_count: int = 0
    qa_warn_count: int = 0


class UploadResponse(BaseModel):
    """Response from file upload."""
    batch_id: str
    accepted: int
    rejected: int
    duplicates: int
    files: List[dict]


# Authentication (RP-168) moved to jarvis_web.auth


def _load_api_map() -> dict:
    if not API_MAP_PATH.exists():
        return {}
    with open(API_MAP_PATH, "r", encoding="utf-8") as handle:
        return json.load(handle)


def _compiled_path_patterns(paths: List[str]) -> List[str]:
    patterns = []
    for path in paths:
        pattern = "^" + path.replace("{", "(?P<").replace("}", ">[^/]+)") + "$"
        patterns.append(pattern)
    return patterns


def get_file_hash(filepath: Path) -> str:
    """Calculate SHA256 hash of file."""
    sha256 = hashlib.sha256()
    with open(filepath, "rb") as f:
        for chunk in iter(lambda: f.read(8192), b""):
            sha256.update(chunk)
    return sha256.hexdigest()

def normalize_status(status: str) -> str:
    """Normalize status into contract-compatible value."""
    normalized = status.lower().strip()
    if normalized in {"queued", "running", "success", "failed"}:
        return normalized
    if normalized in {"error", "failure", "failed"}:
        return "failed"
    if normalized in {"complete", "completed", "success", "succeeded"}:
        return "success"
    if normalized in {"pending", "queued"}:
        return "queued"
    if normalized in {"in_progress", "progress"}:
        return "running"
    return "running"


def _load_json(path: Path) -> dict:
    if not path.exists():
        return {}
    try:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return {}


def _load_jsonl(path: Path) -> list:
    if not path.exists():
        return []
    rows = []
    try:
        with open(path, "r", encoding="utf-8") as f:
            for line in f:
                if line.strip():
                    rows.append(json.loads(line))
    except Exception:
        return []
    return rows


def _iter_run_dirs() -> list[Path]:
    RUNS_DIR.mkdir(parents=True, exist_ok=True)
    legacy = []
    if LEGACY_RUNS_DIR.exists():
        legacy = [d for d in LEGACY_RUNS_DIR.iterdir() if d.is_dir() and not d.name.startswith(".")]
    current = [d for d in RUNS_DIR.iterdir() if d.is_dir() and not d.name.startswith(".")]
    run_dirs = {d.name: d for d in legacy}
    for run_dir in current:
        run_dirs[run_dir.name] = run_dir
    return list(run_dirs.values())


def _resolve_run_dir(run_id: str) -> Path:
    run_dir = RUNS_DIR / run_id
    if run_dir.exists():
        return run_dir
    legacy = LEGACY_RUNS_DIR / run_id
    if legacy.exists():
        return legacy
    raise HTTPException(status_code=404, detail=f"Run {run_id} not found")


def _run_timestamps(run_dir: Path) -> tuple[str, str]:
    stat = run_dir.stat()
    created_at = datetime.fromtimestamp(stat.st_ctime, tz=timezone.utc).isoformat()
    updated_at = datetime.fromtimestamp(stat.st_mtime, tz=timezone.utc).isoformat()
    return created_at, updated_at


def _list_run_files(run_dir: Path) -> list[dict]:
    files = []
    for file_path in sorted(run_dir.rglob("*")):
        if file_path.is_file():
            rel_path = file_path.relative_to(run_dir).as_posix()
            files.append(
                {
                    "path": rel_path,
                    "size": file_path.stat().st_size,
                    "sha256": get_file_hash(file_path),
                }
            )
    return files


def _build_run_response(run_dir: Path, include_files: bool) -> dict:
    result = _load_json(run_dir / "result.json")
    eval_summary = _load_json(run_dir / "eval_summary.json")
    warnings = _load_jsonl(run_dir / "warnings.jsonl")
    errors = _load_jsonl(run_dir / "errors.jsonl")
    progress = _load_json(run_dir / "progress.json")
    created_at, updated_at = _run_timestamps(run_dir)
    files_list = _list_run_files(run_dir) if include_files else []

    response = {
        "run_id": run_dir.name,
        "status": normalize_status(result.get("status", "running")),
        "created_at": created_at,
        "updated_at": updated_at,
        "progress": {
            "step": progress.get("step", ""),
            "percent": progress.get("percent", 0),
            "counts": progress.get("counts", {}),
        },
        "metrics": eval_summary.get("metrics", {}),
        "warnings": warnings,
        "errors": errors,
        "files": files_list,
    }

    files_map = {}
    for entry in files_list:
        files_map[entry["path"]] = {
            "exists": True,
            "size": entry["size"],
            "sha256": entry["sha256"],
        }
    response["files_map"] = files_map

    report_file = run_dir / "report.md"
    if report_file.exists():
        try:
            with open(report_file, "r", encoding="utf-8") as f:
                response["report"] = f.read()
        except Exception:
            response["report"] = ""
    return response


def load_run_summary(run_dir: Path) -> dict:
    """Load run summary from directory."""
    summary = {
        "run_id": run_dir.name,
        "status": "unknown",
        "timestamp": "",
        "gate_passed": False,
        "contract_valid": False,
        "metrics": {},
        "qa_ready": False,
        "qa_error_count": 0,
        "qa_warn_count": 0,
        "qa_top_errors": [],
    }
    
    # Load result.json
    result_file = run_dir / "result.json"
    if result_file.exists():
        try:
            with open(result_file, "r", encoding="utf-8") as f:
                result = json.load(f)
            summary["status"] = result.get("status", "unknown")
            summary["timestamp"] = result.get("timestamp", "")
        except:
            pass
    
    # Load eval_summary.json
    eval_file = run_dir / "eval_summary.json"
    if eval_file.exists():
        try:
            with open(eval_file, "r", encoding="utf-8") as f:
                eval_data = json.load(f)
            summary["gate_passed"] = eval_data.get("gate_passed", False)
            summary["metrics"] = eval_data.get("metrics", {})
        except:
            pass
    
    # Check contract
    required = ["input.json", "run_config.json", "papers.jsonl", "claims.jsonl",
                "evidence.jsonl", "scores.json", "result.json", "eval_summary.json",
                "warnings.jsonl", "report.md"]
    missing = [f for f in required if not (run_dir / f).exists()]
    summary["contract_valid"] = len(missing) == 0

    qa_summary = load_qa_summary(run_dir.name)
    if qa_summary:
        summary.update({
            "qa_ready": qa_summary.get("ready_to_submit", False),
            "qa_error_count": qa_summary.get("error_count", 0),
            "qa_warn_count": qa_summary.get("warn_count", 0),
            "qa_top_errors": qa_summary.get("top_errors", []),
        })
    
    return summary


def load_qa_summary(run_id: str) -> Optional[dict]:
    qa_paths = [
        Path("data/runs") / run_id / "qa" / "qa_report.json",
        RUNS_DIR / run_id / "qa" / "qa_report.json",
    ]
    for qa_path in qa_paths:
        if qa_path.exists():
            try:
                with open(qa_path, "r", encoding="utf-8") as f:
                    return json.load(f)
            except:
                return None
    return None


if FASTAPI_AVAILABLE:

    @app.get("/api/health")
    async def health():
        """Health check endpoint."""
        return {"status": "ok", "timestamp": datetime.now(timezone.utc).isoformat()}

    @app.get("/api/map/v1")
    async def get_api_map():
        """Expose the generated API map for front adapters."""
        api_map = _load_api_map()
        if not api_map:
            raise HTTPException(status_code=404, detail="api_map_v1.json not found")
        return api_map

    @app.get("/api/capabilities")
    async def get_capabilities():
        """Return feature flags and implemented endpoints."""
        api_map = _load_api_map()
        base_paths = api_map.get("base_paths", {}) if api_map else {}
        registered_paths = {
            route.path
            for route in app.router.routes
            if getattr(route, "methods", None)
        }
        features = {}
        endpoints = {}
        for key, path in base_paths.items():
            implemented = path in registered_paths
            features[key] = implemented
            if implemented:
                endpoints[key] = path
        return {
            "version": api_map.get("version", "v1"),
            "generated_at": api_map.get("generated_at"),
            "features": features,
            "endpoints": endpoints,
        }

    # === Run Management (AG-05) ===

    @app.get("/api/runs")
    async def list_runs(limit: int = 20, _: bool = Depends(verify_token)):
        """List runs from logs/runs/ (per BUNDLE_CONTRACT.md)."""
        run_dirs = _iter_run_dirs()
        run_dirs.sort(key=lambda p: p.stat().st_mtime, reverse=True)
        runs = [_build_run_response(run_dir, include_files=False) for run_dir in run_dirs[:limit]]
        return {"runs": runs, "total": len(run_dirs)}

    @app.get("/api/runs/{run_id}")
    async def get_run(run_id: str, _: bool = Depends(verify_token)):
        """Get run details."""
        run_dir = _resolve_run_dir(run_id)
        return _build_run_response(run_dir, include_files=True)

    @app.get("/api/runs/{run_id}/files")
    async def list_run_files(run_id: str, _: bool = Depends(verify_token)):
        """List files for a run."""
        run_dir = _resolve_run_dir(run_id)
        files = _list_run_files(run_dir)
        return {"files": files}

    @app.get("/api/runs/{run_id}/manifest")
    async def get_run_manifest(run_id: str, _: bool = Depends(verify_token)):
        """Get reproducibility manifest for a run."""
        manifest_path = Path("data/research") / run_id / "manifest.json"
        if not manifest_path.exists():
            raise HTTPException(status_code=404, detail="manifest not found")
        with open(manifest_path, "r", encoding="utf-8") as f:
            return json.load(f)

    @app.get("/api/runs/{run_id}/files/{path:path}")
    async def get_run_file(run_id: str, path: str, _: bool = Depends(verify_token)):
        """Get specific file from run."""
        run_dir = _resolve_run_dir(run_id)
        candidate = Path(path)
        if candidate.is_absolute() or ".." in candidate.parts:
            raise HTTPException(status_code=400, detail="Invalid path")
        filepath = (run_dir / candidate).resolve()
        run_root = run_dir.resolve()
        if not str(filepath).startswith(str(run_root)):
            raise HTTPException(status_code=400, detail="Invalid path")
        if not filepath.exists():
            raise HTTPException(status_code=404, detail=f"File {path} not found")
        return FileResponse(
            filepath,
            filename=candidate.name,
            media_type="application/octet-stream",
        )

    @app.get("/api/runs/{run_id}/events")
    async def get_run_events(run_id: str, _: bool = Depends(verify_token)):
        """Run events are not implemented."""
        raise HTTPException(status_code=501, detail="Run events not implemented")

    @app.get("/api/capabilities")
    async def get_capabilities(_: bool = Depends(verify_token)):
        """Report API capabilities."""
        return {
            "version": "v1",
            "features": {
                "runs": True,
                "events": False,
                "research_rank": True,
                "research_paper": True,
                "qa_report": False,
                "submission": False,
                "feedback": False,
                "decision": False,
                "finance": True,
            },
            "endpoints": {
                "runs_list": "/api/runs",
                "run_detail": "/api/runs/{run_id}",
                "run_files": "/api/runs/{run_id}/files",
                "run_file_get": "/api/runs/{run_id}/files/{path}",
            },
        }

    @app.get("/api/qa/report")
    async def qa_report(_: bool = Depends(verify_token)):
        """QA report not yet implemented."""
        raise HTTPException(status_code=501, detail="QA report not implemented")

    @app.post("/api/submission/build")
    async def build_submission(_: bool = Depends(verify_token)):
        """Submission build not yet implemented."""
        raise HTTPException(status_code=501, detail="Submission build not implemented")

    @app.get("/api/submission/run/{run_id}/latest")
    async def submission_latest(run_id: str, _: bool = Depends(verify_token)):
        """Submission latest not yet implemented."""
        raise HTTPException(status_code=501, detail="Submission latest not implemented")

    @app.get("/api/submission/run/{run_id}/changelog")
    async def submission_changelog(run_id: str, version: str, _: bool = Depends(verify_token)):
        """Submission changelog not yet implemented."""
        raise HTTPException(status_code=501, detail="Submission changelog not implemented")

    @app.get("/api/submission/run/{run_id}/email")
    async def submission_email(
        run_id: str,
        version: str,
        recipient_type: str,
        _: bool = Depends(verify_token),
    ):
        """Submission email not yet implemented."""
        raise HTTPException(status_code=501, detail="Submission email not implemented")

    @app.get("/api/feedback/risk")
    async def feedback_risk(run_id: str, _: bool = Depends(verify_token)):
        """Feedback risk not yet implemented."""
        raise HTTPException(status_code=501, detail="Feedback risk not implemented")

    @app.post("/api/feedback/import")
    async def feedback_import(_: bool = Depends(verify_token)):
        """Feedback import not yet implemented."""
        raise HTTPException(status_code=501, detail="Feedback import not implemented")

    @app.post("/api/decision/simulate")
    async def decision_simulate(_: bool = Depends(verify_token)):
        """Decision simulate not yet implemented."""
        raise HTTPException(status_code=501, detail="Decision simulate not implemented")

    def _start_run(request: RunRequest) -> RunResponse:
        """Start a new paper survey run."""
        import uuid
        from jarvis_core.app import run_task
        from jarvis_core.export.package_builder import build_run_package

        run_id = str(uuid.uuid4())

        try:
            result = run_task(
                task_dict={
                    "goal": request.query,
                    "category": "paper_survey",
                    "inputs": {"query": request.query},
                },
                run_config_dict={
                    "seed": request.seed,
                    **request.config,
                },
            )

            return RunResponse(
                run_id=result.run_id,
                status=result.status,
                message=f"Run completed: {result.status}",
            )
        except Exception as e:
            return RunResponse(
                run_id=run_id,
                status="error",
                message=str(e),
            )

    @app.post("/api/runs", response_model=RunResponse)
    async def start_run(request: RunRequest, _: bool = Depends(verify_token)):
        """Start a new paper survey run."""
        return _start_run(request)

    @app.post("/api/run", response_model=RunResponse)
    async def start_run_legacy(request: RunRequest, _: bool = Depends(verify_token)):
        """Legacy start run endpoint."""
        return _start_run(request)

    # === File Upload (AG-07) ===

    @app.post("/api/upload/pdf", response_model=UploadResponse)
    async def upload_pdf(
        files: List[UploadFile] = File(...),
        _: bool = Depends(verify_token),
    ):
        """Upload PDF files (max 100)."""
        return await _handle_upload(files, "pdf")

    @app.post("/api/upload/bibtex", response_model=UploadResponse)
    async def upload_bibtex(
        files: List[UploadFile] = File(...),
        _: bool = Depends(verify_token),
    ):
        """Upload BibTeX files."""
        return await _handle_upload(files, "bibtex")

    @app.post("/api/upload/zip", response_model=UploadResponse)
    async def upload_zip(
        file: UploadFile = File(...),
        _: bool = Depends(verify_token),
    ):
        """Upload ZIP file containing PDFs."""
        batch_id = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
        batch_dir = UPLOADS_DIR / batch_id
        batch_dir.mkdir(parents=True, exist_ok=True)
        
        accepted = 0
        rejected = 0
        duplicates = 0
        file_info = []
        
        # Save and extract ZIP
        with tempfile.NamedTemporaryFile(delete=False, suffix=".zip") as tmp:
            content = await file.read()
            tmp.write(content)
            tmp_path = tmp.name
        
        try:
            with zipfile.ZipFile(tmp_path, "r") as zf:
                for name in zf.namelist():
                    if name.lower().endswith(".pdf"):
                        # Extract to batch dir
                        extracted = zf.extract(name, batch_dir)
                        extracted_path = Path(extracted)
                        
                        # Check for duplicates
                        file_hash = get_file_hash(extracted_path)
                        hash_file = UPLOADS_DIR / "hashes.json"
                        hashes = {}
                        if hash_file.exists():
                            with open(hash_file, "r") as f:
                                hashes = json.load(f)
                        
                        if file_hash in hashes:
                            duplicates += 1
                            extracted_path.unlink()
                        else:
                            hashes[file_hash] = str(extracted_path)
                            with open(hash_file, "w") as f:
                                json.dump(hashes, f)
                            accepted += 1
                            file_info.append({
                                "name": name,
                                "size": extracted_path.stat().st_size,
                                "hash": file_hash[:16],
                            })
        finally:
            os.unlink(tmp_path)
        
        return UploadResponse(
            batch_id=batch_id,
            accepted=accepted,
            rejected=rejected,
            duplicates=duplicates,
            files=file_info,
        )


async def _handle_upload(files: List[UploadFile], file_type: str) -> UploadResponse:
    """Handle file upload with deduplication."""
    if len(files) > MAX_BATCH_FILES:
        raise HTTPException(
            status_code=400,
            detail=f"Too many files. Max {MAX_BATCH_FILES} per batch.",
        )
    
    batch_id = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
    batch_dir = UPLOADS_DIR / batch_id
    batch_dir.mkdir(parents=True, exist_ok=True)
    
    accepted = 0
    rejected = 0
    duplicates = 0
    file_info = []
    
    # Load existing hashes
    hash_file = UPLOADS_DIR / "hashes.json"
    hashes = {}
    if hash_file.exists():
        try:
            with open(hash_file, "r") as f:
                hashes = json.load(f)
        except:
            pass
    
    for upload_file in files:
        try:
            # Read content
            content = await upload_file.read()
            
            # Check size
            if len(content) > MAX_UPLOAD_SIZE:
                rejected += 1
                continue
            
            # Calculate hash
            file_hash = hashlib.sha256(content).hexdigest()
            
            # Check duplicate
            if file_hash in hashes:
                duplicates += 1
                continue
            
            # Save file
            safe_name = upload_file.filename or f"file_{accepted}.{file_type}"
            filepath = batch_dir / safe_name
            with open(filepath, "wb") as f:
                f.write(content)
            
            # Update hash registry
            hashes[file_hash] = str(filepath)
            
            accepted += 1
            file_info.append({
                "name": safe_name,
                "size": len(content),
                "hash": file_hash[:16],
            })
            
        except Exception as e:
            rejected += 1
    
    # Save updated hashes
    with open(hash_file, "w") as f:
        json.dump(hashes, f)
    
    return UploadResponse(
        batch_id=batch_id,
        accepted=accepted,
        rejected=rejected,
        duplicates=duplicates,
        files=file_info,
    )


# === Search API (S-01/AG-09) ===
if FASTAPI_AVAILABLE:

    class SearchRequest(BaseModel):
        """Search request."""
        query: str
        top_k: int = 20
        paper_id: Optional[str] = None

    @app.get("/api/search")
    async def search_corpus(
        q: str,
        top_k: int = 20,
        paper_id: Optional[str] = None,
        _: bool = Depends(verify_token),
    ):
        """Search the corpus using BM25."""
        try:
            from jarvis_core.search import get_search_engine
            
            engine = get_search_engine()
            
            # Load chunks if not loaded
            chunks_file = Path("data/chunks.jsonl")
            if chunks_file.exists() and not engine._loaded:
                engine.load_chunks(chunks_file)
            
            filters = {"paper_id": paper_id} if paper_id else None
            results = engine.search(q, top_k=top_k, filters=filters)
            
            return results.to_dict()
        except Exception as e:
            return {"results": [], "total": 0, "query": q, "error": str(e)}


# === Collect API (S-01/AG-10) ===
if FASTAPI_AVAILABLE:

    class CollectRequest(BaseModel):
        """Collect request."""
        query: str
        max_results: int = 50
        oa_only: bool = False
        domain: Optional[str] = None

    class JobRequest(BaseModel):
        """Job request."""
        type: str
        payload: dict = {}
        dedupe_key: Optional[str] = None

    @app.post("/api/jobs")
    async def create_job(request: JobRequest, _: bool = Depends(verify_api_token)):
        """Create a new job and run in background."""
        from jarvis_web import dedup
        from jarvis_web import jobs
        from jarvis_web.job_runner import run_job

        dedupe_key = request.dedupe_key or request.payload.get("dedupe_key")
        if not dedupe_key:
            raise HTTPException(status_code=400, detail="dedupe_key is required")

        job_id = jobs.generate_job_id()
        try:
            redis_client = dedup.get_redis()
            claimed, existing_job_id = dedup.claim_dedupe_key(
                redis_client,
                dedupe_key=dedupe_key,
                job_id=job_id,
                ttl_sec=None,
            )
        except Exception as exc:
            raise HTTPException(status_code=500, detail=f"dedupe failed: {exc}")

        if not claimed:
            status = "duplicate"
            if existing_job_id:
                try:
                    existing_job = jobs.read_job(existing_job_id)
                    status = existing_job.get("status", status)
                except FileNotFoundError:
                    pass
            return {"job_id": existing_job_id or job_id, "status": status}

        payload = dict(request.payload)
        payload.setdefault("dedupe_key", dedupe_key)
        job = jobs.create_job(request.type, payload, job_id=job_id)
        jobs.run_in_background(job["job_id"], lambda: run_job(job["job_id"]))
        return {"job_id": job["job_id"], "status": job["status"]}

    @app.get("/api/jobs/{job_id}")
    async def get_job(job_id: str, _: bool = Depends(verify_token)):
        """Get job status."""
        from jarvis_web import jobs

        try:
            return jobs.read_job(job_id)
        except FileNotFoundError:
            raise HTTPException(status_code=404, detail=f"Job {job_id} not found")

    @app.get("/api/jobs/{job_id}/events")
    async def get_job_events(job_id: str, tail: int = 200, _: bool = Depends(verify_token)):
        """Get job events (tail)."""
        from jarvis_web import jobs

        try:
            jobs.read_job(job_id)
            return {"events": jobs.tail_events(job_id, tail=tail)}
        except FileNotFoundError:
            raise HTTPException(status_code=404, detail=f"Job {job_id} not found")

    @app.get("/api/health/cron")
    async def health_cron(_: bool = Depends(verify_token)):
        """Cron/worker/index health check."""
        from jarvis_web.health import get_health_snapshot

        return get_health_snapshot()

    @app.post("/api/collect/pubmed")
    async def collect_pubmed(request: CollectRequest, _: bool = Depends(verify_token)):
        """Collect papers from PubMed (compat: create job)."""
        from jarvis_web import jobs
        from jarvis_web.job_runner import run_job

        payload = {
            "query": request.query,
            "max_results": request.max_results,
            "oa_only": request.oa_only,
            "domain": request.domain,
        }
        job = jobs.create_job("collect_and_ingest", payload)
        jobs.run_in_background(job["job_id"], lambda: run_job(job["job_id"]))
        return {"job_id": job["job_id"], "status": job["status"]}


# === KPI API (S-02) ===
if FASTAPI_AVAILABLE:

    @app.get("/api/kpi")
    async def get_kpis(_: bool = Depends(verify_token)):
        """Get fixed KPI definitions and current values."""
        # Fixed KPI definitions (S-02)
        kpi_definitions = {
            "evidence_coverage": {
                "label": "Evidence Coverage",
                "description": "Percentage of claims with supporting evidence",
                "threshold": 0.95,
                "unit": "%",
            },
            "locator_rate": {
                "label": "Locator Rate", 
                "description": "Percentage of evidence with valid locators",
                "threshold": 0.98,
                "unit": "%",
            },
            "provenance_rate": {
                "label": "Provenance Rate",
                "description": "Percentage of facts with traceable source",
                "threshold": 0.95,
                "unit": "%",
            },
            "citation_precision": {
                "label": "Citation Precision",
                "description": "Accuracy of paper citations",
                "threshold": 0.90,
                "unit": "%",
            },
            "contract_compliance": {
                "label": "Contract Compliance",
                "description": "10-file bundle contract adherence",
                "threshold": 1.0,
                "unit": "rate",
            },
            "gate_pass_rate": {
                "label": "Gate Pass Rate",
                "description": "Runs passing quality gates",
                "threshold": 0.95,
                "unit": "%",
            },
        }
        
        # Compute current values from runs
        runs = []
        if RUNS_DIR.exists():
            for run_dir in sorted(RUNS_DIR.iterdir(), reverse=True)[:50]:
                if run_dir.is_dir():
                    summary = load_run_summary(run_dir)
                    if summary:
                        runs.append(summary)
        
        current_values = {}
        if runs:
            current_values["evidence_coverage"] = sum(r.get("metrics", {}).get("evidence_coverage", 0) for r in runs) / len(runs)
            current_values["locator_rate"] = sum(r.get("metrics", {}).get("locator_rate", 0) for r in runs) / len(runs)
            current_values["provenance_rate"] = sum(r.get("metrics", {}).get("provenance_rate", 0) for r in runs) / len(runs)
            current_values["citation_precision"] = sum(r.get("metrics", {}).get("citation_precision", 0) for r in runs) / len(runs)
            current_values["contract_compliance"] = sum(1 for r in runs if r.get("contract_valid", False)) / len(runs)
            current_values["gate_pass_rate"] = sum(1 for r in runs if r.get("gate_passed", False)) / len(runs)
        
        return {
            "definitions": kpi_definitions,
            "current_values": current_values,
            "sample_size": len(runs),
        }

    @app.middleware("http")
    async def map_unimplemented_endpoints(request, call_next):
        api_map = _load_api_map()
        base_paths = api_map.get("base_paths", {}) if api_map else {}
        if base_paths:
            registered_paths = {
                route.path
                for route in app.router.routes
                if getattr(route, "methods", None)
            }
            unimplemented = [
                path for path in base_paths.values() if path not in registered_paths
            ]
            if unimplemented:
                patterns = [
                    re.compile(pattern)
                    for pattern in _compiled_path_patterns(unimplemented)
                ]
                if any(pattern.match(request.url.path) for pattern in patterns):
                    return JSONResponse(
                        {"detail": "Not Implemented"},
                        status_code=501,
                    )
        return await call_next(request)


# === Feedback API (P8) ===
if FASTAPI_AVAILABLE:
    from jarvis_web.routes.feedback import router as feedback_router

    app.include_router(feedback_router)


# Legacy compatibility endpoints
if FASTAPI_AVAILABLE:

    @app.get("/health")
    async def health_legacy():
        """Legacy health check."""
        return await health()

    @app.get("/runs")
    async def list_runs_legacy(limit: int = 10, _: bool = Depends(verify_token)):
        """Legacy runs endpoint."""
        return await list_runs(limit, _)

    @app.get("/run/{run_id}")
    async def get_run_legacy(run_id: str, _: bool = Depends(verify_token)):
        """Legacy run endpoint."""
        return await get_run(run_id, _)

    @app.get("/api/run")
    async def list_runs_api_legacy(limit: int = 20, _: bool = Depends(verify_token)):
        """Legacy API runs endpoint."""
        return await list_runs(limit, _)

    @app.get("/api/run/{run_id}")
    async def get_run_api_legacy(run_id: str, _: bool = Depends(verify_token)):
        """Legacy API run endpoint."""
        return await get_run(run_id, _)


def create_app() -> Optional[FastAPI]:
    """Create and return the FastAPI app."""
    if not FASTAPI_AVAILABLE:
        raise ImportError("FastAPI not installed. Run: pip install fastapi uvicorn")
    return app


def run_server(host: str = "127.0.0.1", port: int = 8000):
    """Run the development server."""
    if not FASTAPI_AVAILABLE:
        print("FastAPI not installed. Run: pip install fastapi uvicorn")
        return

    import uvicorn

    uvicorn.run(app, host=host, port=port)


if __name__ == "__main__":
    run_server()
