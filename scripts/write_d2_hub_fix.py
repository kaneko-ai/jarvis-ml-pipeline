import pathlib

target = pathlib.Path("jarvis_core/mcp/hub.py")
content = target.read_text(encoding="utf-8")

# Fix 1: OpenAlex max_results -> per_page
content = content.replace(
    'max_results = params.get("max_results", 5)\n        works = client.search(query, max_results=max_results)',
    'per_page = params.get("max_results", 5)\n        works = client.search(query, per_page=per_page)'
)

# Fix 2: S2 search - add retry with backoff for 429
old_s2 = '''    def _local_s2_search(self, params: dict) -> dict:
        query = params.get("query", "")
        limit = min(params.get("limit", 5), 100)
        url = "https://api.semanticscholar.org/graph/v1/paper/search"
        resp = requests.get(
            url,
            params={"query": query, "limit": limit, "fields": "title,authors,year,abstract,externalIds,citationCount"},
            headers={"User-Agent": "JARVIS Research OS/2.0"},
            timeout=15,
        )
        resp.raise_for_status()'''

new_s2 = '''    def _local_s2_search(self, params: dict) -> dict:
        import time as _time
        query = params.get("query", "")
        limit = min(params.get("limit", 5), 100)
        url = "https://api.semanticscholar.org/graph/v1/paper/search"
        delays = [5, 10, 30]
        resp = None
        for attempt in range(4):
            resp = requests.get(
                url,
                params={"query": query, "limit": limit, "fields": "title,authors,year,abstract,externalIds,citationCount"},
                headers={"User-Agent": "JARVIS Research OS/2.0"},
                timeout=15,
            )
            if resp.status_code != 429:
                break
            if attempt < 3:
                wait = delays[attempt]
                print(f"    S2 429 - retry in {wait}s (attempt {attempt+1}/3)")
                _time.sleep(wait)
        resp.raise_for_status()'''

content = content.replace(old_s2, new_s2)

# Fix 3: S2 paper - add retry
old_s2p = '''    def _local_s2_paper(self, params: dict) -> dict:
        paper_id = params.get("paper_id", "")
        fields = "title,authors,year,abstract,externalIds,citationCount,referenceCount,venue"
        url = f"https://api.semanticscholar.org/graph/v1/paper/{paper_id}"
        resp = requests.get(
            url,
            params={"fields": fields},
            headers={"User-Agent": "JARVIS Research OS/2.0"},
            timeout=15,
        )
        resp.raise_for_status()'''

new_s2p = '''    def _local_s2_paper(self, params: dict) -> dict:
        import time as _time
        paper_id = params.get("paper_id", "")
        fields = "title,authors,year,abstract,externalIds,citationCount,referenceCount,venue"
        url = f"https://api.semanticscholar.org/graph/v1/paper/{paper_id}"
        delays = [5, 10, 30]
        resp = None
        for attempt in range(4):
            resp = requests.get(
                url,
                params={"fields": fields},
                headers={"User-Agent": "JARVIS Research OS/2.0"},
                timeout=15,
            )
            if resp.status_code != 429:
                break
            if attempt < 3:
                wait = delays[attempt]
                print(f"    S2 429 - retry in {wait}s (attempt {attempt+1}/3)")
                _time.sleep(wait)
        resp.raise_for_status()'''

content = content.replace(old_s2p, new_s2p)

target.write_text(content, encoding="utf-8")
print(f"Updated: {target} ({target.stat().st_size} bytes)")
