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
import shutil
import tempfile
import zipfile
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, List, Optional

try:
    from fastapi import FastAPI, HTTPException, Depends, Header, UploadFile, File
    from fastapi.responses import JSONResponse, FileResponse
    from fastapi.staticfiles import StaticFiles
    from fastapi.middleware.cors import CORSMiddleware
    from pydantic import BaseModel

    FASTAPI_AVAILABLE = True
except ImportError:
    FASTAPI_AVAILABLE = False
    FastAPI = None
    HTTPException = None
    BaseModel = object


# Constants
RUNS_DIR = Path("logs/runs")
UPLOADS_DIR = Path("data/uploads")
MAX_UPLOAD_SIZE = 100 * 1024 * 1024  # 100MB per file
MAX_BATCH_FILES = 100
API_TOKEN = os.getenv("API_TOKEN")


# Create app if FastAPI available
if FASTAPI_AVAILABLE:
    from jarvis_web.routes.research import router as research_router
    from jarvis_web.routes.finance import router as finance_router

    app = FastAPI(
        title="JARVIS Research OS",
        description="API for paper survey and knowledge synthesis",
        version="4.3.0",
    )
    
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


class UploadResponse(BaseModel):
    """Response from file upload."""
    batch_id: str
    accepted: int
    rejected: int
    duplicates: int
    files: List[dict]


# Authentication (RP-168)
def verify_token(authorization: Optional[str] = Header(None)) -> bool:
    """Verify authorization token."""
    expected = os.environ.get("JARVIS_WEB_TOKEN", "")
    if not expected:
        return True  # No auth required

    if authorization is None:
        raise HTTPException(status_code=401, detail="Authorization header required")

    token = authorization.replace("Bearer ", "")
    if token != expected:
        raise HTTPException(status_code=403, detail="Invalid token")

    return True


def verify_api_token(authorization: Optional[str] = Header(None)) -> bool:
    """Verify API token for job creation."""
    if not API_TOKEN:
        return True

    if authorization is None or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Unauthorized")

    token = authorization.replace("Bearer ", "")
    if token != API_TOKEN:
        raise HTTPException(status_code=401, detail="Unauthorized")

    return True


def get_file_hash(filepath: Path) -> str:
    """Calculate SHA256 hash of file."""
    sha256 = hashlib.sha256()
    with open(filepath, "rb") as f:
        for chunk in iter(lambda: f.read(8192), b""):
            sha256.update(chunk)
    return sha256.hexdigest()


def load_run_summary(run_dir: Path) -> dict:
    """Load run summary from directory."""
    summary = {
        "run_id": run_dir.name,
        "status": "unknown",
        "timestamp": "",
        "gate_passed": False,
        "contract_valid": False,
        "metrics": {},
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
    
    return summary


if FASTAPI_AVAILABLE:

    @app.get("/api/health")
    async def health():
        """Health check endpoint."""
        return {"status": "ok", "timestamp": datetime.now(timezone.utc).isoformat()}

    # === Run Management (AG-05) ===

    @app.get("/api/runs")
    async def list_runs(limit: int = 20, _: bool = Depends(verify_token)):
        """List runs from logs/runs/ (per BUNDLE_CONTRACT.md)."""
        RUNS_DIR.mkdir(parents=True, exist_ok=True)
        
        runs = []
        run_dirs = [d for d in RUNS_DIR.iterdir() if d.is_dir() and not d.name.startswith(".")]
        run_dirs.sort(key=lambda p: p.stat().st_mtime, reverse=True)
        
        for run_dir in run_dirs[:limit]:
            runs.append(load_run_summary(run_dir))
        
        return {"runs": runs, "total": len(run_dirs)}

    @app.get("/api/runs/{run_id}")
    async def get_run(run_id: str, _: bool = Depends(verify_token)):
        """Get run details."""
        run_dir = RUNS_DIR / run_id
        
        if not run_dir.exists():
            raise HTTPException(status_code=404, detail=f"Run {run_id} not found")
        
        summary = load_run_summary(run_dir)
        
        # Add file list
        files = {}
        for f in run_dir.iterdir():
            if f.is_file():
                files[f.name] = {
                    "exists": True,
                    "size": f.stat().st_size,
                }
        summary["files"] = files
        
        # Load report.md if exists
        report_file = run_dir / "report.md"
        if report_file.exists():
            try:
                with open(report_file, "r", encoding="utf-8") as f:
                    summary["report"] = f.read()
            except:
                summary["report"] = ""
        
        return summary

    @app.get("/api/runs/{run_id}/manifest")
    async def get_run_manifest(run_id: str, _: bool = Depends(verify_token)):
        """Get reproducibility manifest for a run."""
        manifest_path = Path("data/research") / run_id / "manifest.json"
        if not manifest_path.exists():
            raise HTTPException(status_code=404, detail="manifest not found")
        with open(manifest_path, "r", encoding="utf-8") as f:
            return json.load(f)

    @app.get("/api/runs/{run_id}/files/{filename}")
    async def get_run_file(run_id: str, filename: str, _: bool = Depends(verify_token)):
        """Get specific file from run."""
        run_dir = RUNS_DIR / run_id
        filepath = run_dir / filename
        
        if not filepath.exists():
            raise HTTPException(status_code=404, detail=f"File {filename} not found")
        
        # Return JSON content directly for JSON files
        if filename.endswith(".json"):
            try:
                with open(filepath, "r", encoding="utf-8") as f:
                    return json.load(f)
            except:
                pass
        
        # Return JSONL as array
        if filename.endswith(".jsonl"):
            try:
                with open(filepath, "r", encoding="utf-8") as f:
                    return [json.loads(line) for line in f if line.strip()]
            except:
                pass
        
        # Return as file
        return FileResponse(filepath)

    @app.post("/api/run", response_model=RunResponse)
    async def start_run(request: RunRequest, _: bool = Depends(verify_token)):
        """Start a new paper survey run."""
        import uuid
        from jarvis_core.app import run_task

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

    @app.post("/api/jobs")
    async def create_job(request: JobRequest, _: bool = Depends(verify_api_token)):
        """Create a new job and run in background."""
        from jarvis_web import jobs
        from jarvis_web.job_runner import run_job

        job = jobs.create_job(request.type, request.payload)
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
