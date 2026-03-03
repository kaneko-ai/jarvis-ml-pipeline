"""LightRAG engine for JARVIS Research OS.

LLM backend: Codex CLI -> Copilot CLI -> Gemini API (fallback chain).
Embedding: sentence-transformers (local, no API).
"""
from __future__ import annotations

import asyncio
import json
import os
import subprocess
import time
from pathlib import Path
from typing import Optional

import numpy as np
from dotenv import load_dotenv

load_dotenv()

DEFAULT_WORKING_DIR = str(
    Path.home()
    / "Documents"
    / "jarvis-work"
    / "jarvis-ml-pipeline"
    / ".lightrag"
)

PROJECT_DIR = str(
    Path.home()
    / "Documents"
    / "jarvis-work"
    / "jarvis-ml-pipeline"
)

_last_llm_call = 0.0
_LLM_CALL_INTERVAL = 3.0


def _call_codex(prompt: str, timeout: int = 180) -> Optional[str]:
    """Call Codex CLI via stdin pipe."""
    try:
        result = subprocess.run(
            ["codex", "exec", "-"],
            input=prompt,
            capture_output=True,
            text=True,
            timeout=timeout,
            cwd=PROJECT_DIR,
        )
        output = result.stdout.strip()
        if output and result.returncode == 0:
            return output
    except (subprocess.TimeoutExpired, FileNotFoundError, OSError):
        pass
    return None


def _call_copilot(prompt: str, timeout: int = 180) -> Optional[str]:
    """Call Copilot CLI in programmatic mode."""
    try:
        result = subprocess.run(
            ["copilot", "-p", prompt],
            capture_output=True,
            text=True,
            timeout=timeout,
            cwd=PROJECT_DIR,
        )
        output = result.stdout.strip()
        if output and result.returncode == 0:
            return output
    except (subprocess.TimeoutExpired, FileNotFoundError, OSError):
        pass
    return None


async def _gemini_complete_simple(prompt: str, system_prompt: str = "") -> str:
    """Gemini API fallback via LiteLLM with retry."""
    import litellm

    model = os.getenv("LLM_MODEL", "gemini/gemini-2.0-flash")
    messages = []
    if system_prompt:
        messages.append({"role": "system", "content": system_prompt})
    messages.append({"role": "user", "content": prompt})

    for attempt in range(3):
        try:
            response = await litellm.acompletion(
                model=model, messages=messages,
                temperature=0.1, max_tokens=4000,
            )
            return response.choices[0].message.content
        except Exception as e:
            if "429" in str(e) or "RESOURCE_EXHAUSTED" in str(e):
                wait = 30 * (attempt + 1)
                print(f" 429-wait{wait}s", end="", flush=True)
                await asyncio.sleep(wait)
            else:
                return ""
    return ""


async def _llm_complete(
    prompt: str,
    system_prompt: Optional[str] = None,
    history_messages: Optional[list] = None,
    keyword_extraction: bool = False,
    **kwargs,
) -> str:
    """LLM fallback chain: Codex CLI -> Copilot CLI -> Gemini API."""
    global _last_llm_call

    now = time.time()
    elapsed = now - _last_llm_call
    if elapsed < _LLM_CALL_INTERVAL:
        await asyncio.sleep(_LLM_CALL_INTERVAL - elapsed)
    _last_llm_call = time.time()

    full_prompt = prompt
    if system_prompt:
        full_prompt = f"{system_prompt}\n\n{prompt}"

    # Try 1: Codex CLI
    print("  [LLM] Codex...", end="", flush=True)
    result = await asyncio.get_event_loop().run_in_executor(
        None, _call_codex, full_prompt
    )
    if result:
        print(" OK")
        return result
    print(" skip", end="")

    # Try 2: Copilot CLI
    print(" -> Copilot...", end="", flush=True)
    result = await asyncio.get_event_loop().run_in_executor(
        None, _call_copilot, full_prompt
    )
    if result:
        print(" OK")
        return result
    print(" skip", end="")

    # Try 3: Gemini
    print(" -> Gemini...", end="", flush=True)
    result = await _gemini_complete_simple(prompt, system_prompt or "")
    if result:
        print(" OK")
        return result
    print(" FAIL")

    return ""


async def _local_embed(texts: list[str]) -> np.ndarray:
    """Local embedding via sentence-transformers."""
    from sentence_transformers import SentenceTransformer
    model = SentenceTransformer("all-MiniLM-L6-v2")
    embeddings = model.encode(texts, show_progress_bar=False)
    if not isinstance(embeddings, np.ndarray):
        embeddings = np.array(embeddings)
    return embeddings


class JarvisLightRAG:
    """LightRAG wrapper with CLI-based LLM fallback chain."""

    def __init__(self, working_dir: Optional[str] = None):
        self.working_dir = working_dir or DEFAULT_WORKING_DIR
        Path(self.working_dir).mkdir(parents=True, exist_ok=True)
        self._rag = None

    async def _init_rag(self):
        if self._rag is not None:
            return self._rag

        from lightrag import LightRAG
        from lightrag.utils import EmbeddingFunc

        self._rag = LightRAG(
            working_dir=self.working_dir,
            llm_model_func=_llm_complete,
            llm_model_name="codex-copilot-gemini-chain",
            llm_model_max_async=1,
            embedding_func=EmbeddingFunc(
                embedding_dim=384,
                max_token_size=512,
                model_name="all-MiniLM-L6-v2",
                func=_local_embed,
            ),
            chunk_token_size=800,
            chunk_overlap_token_size=100,
            entity_extract_max_gleaning=1,
            enable_llm_cache=True,
        )
        await self._rag.initialize_storages()
        return self._rag

    async def _finalize(self):
        if self._rag is not None:
            try:
                await self._rag.finalize_storages()
            except Exception:
                pass
            self._rag = None

    async def ainsert_papers(self, papers: list[dict]) -> int:
        rag = await self._init_rag()
        count = 0
        for p in papers:
            title = p.get("title", "")
            abstract = p.get("abstract", "")
            doi = p.get("doi", "")
            year = p.get("year", "")
            if not title:
                continue
            text = f"Title: {title}\n"
            if year:
                text += f"Year: {year}\n"
            if doi:
                text += f"DOI: {doi}\n"
            if abstract:
                text += f"Abstract: {abstract}\n"
            try:
                await rag.ainsert(text)
                count += 1
            except asyncio.CancelledError:
                print(f"  [WARN] CancelledError for: {title[:40]}")
                count += 1
            except Exception as e:
                print(f"  [WARN] Error for {title[:40]}: {e}")
        return count

    def insert_papers(self, papers: list[dict]) -> int:
        async def _run():
            try:
                return await self.ainsert_papers(papers)
            finally:
                await self._finalize()
        return asyncio.run(_run())

    def insert_from_json(self, json_path: str) -> int:
        path = Path(json_path)
        if not path.exists():
            raise FileNotFoundError(f"Not found: {json_path}")
        with open(path, encoding="utf-8") as f:
            data = json.load(f)
        papers = data if isinstance(data, list) else data.get("papers", [])
        return self.insert_papers(papers)

    async def aquery(self, query: str, mode: str = "hybrid") -> str:
        from lightrag import QueryParam
        rag = await self._init_rag()
        result = await rag.aquery(query, param=QueryParam(mode=mode))
        return result

    def query(self, query: str, mode: str = "hybrid") -> str:
        async def _run():
            try:
                return await self.aquery(query, mode=mode)
            finally:
                await self._finalize()
        return asyncio.run(_run())

    def get_graph_stats(self) -> dict:
        graph_path = Path(self.working_dir) / "graph_chunk_entity_relation.graphml"
        if not graph_path.exists():
            return {"status": "no_graph", "nodes": 0, "edges": 0}
        try:
            import networkx as nx
            G = nx.read_graphml(str(graph_path))
            return {
                "status": "ok",
                "nodes": G.number_of_nodes(),
                "edges": G.number_of_edges(),
                "graph_file": str(graph_path),
            }
        except Exception as e:
            return {"status": "error", "error": str(e)}
