"""D3-2 Test: LightRAG engine with Codex/Copilot/Gemini fallback."""
import sys
import time
sys.path.insert(0, ".")

from jarvis_core.rag.lightrag_engine import JarvisLightRAG

# Only 1 paper to minimize LLM calls
SAMPLE_PAPERS = [
    {
        "title": "PD-1 blockade in tumors with mismatch-repair deficiency",
        "abstract": "Immune checkpoint inhibitors targeting PD-1 have shown "
                    "remarkable efficacy in various cancers. Mismatch-repair "
                    "deficient tumors respond exceptionally well to pembrolizumab "
                    "due to high mutation burden and neoantigen load.",
        "doi": "10.1056/NEJMoa1500596",
        "year": "2015",
    },
]


def main():
    print("=" * 60)
    print("D3-2 Test: LightRAG (Codex/Copilot/Gemini fallback)")
    print("=" * 60)
    passed = 0
    total = 3

    # Test 1: Initialize
    print("\n[Test 1] Initialize JarvisLightRAG...")
    try:
        engine = JarvisLightRAG()
        print(f"  OK: working_dir = {engine.working_dir}")
        passed += 1
    except Exception as e:
        print(f"  FAIL: {e}")
        return

    # Test 2: Insert 1 paper
    print("\n[Test 2] Insert 1 paper (Codex -> Copilot -> Gemini)...")
    print("  This may take 1-5 minutes...")
    try:
        start = time.time()
        count = engine.insert_papers(SAMPLE_PAPERS)
        elapsed = time.time() - start
        print(f"  OK: Inserted {count} paper(s) in {elapsed:.1f}s")
        passed += 1
    except Exception as e:
        print(f"  FAIL: {e}")

    # Test 3: Graph stats
    print("\n[Test 3] Knowledge graph stats...")
    try:
        stats = engine.get_graph_stats()
        print(f"  Status: {stats.get('status')}")
        print(f"  Nodes:  {stats.get('nodes', 0)}")
        print(f"  Edges:  {stats.get('edges', 0)}")
        if stats.get("nodes", 0) > 0:
            print("  OK: Knowledge graph constructed!")
            passed += 1
        else:
            print("  WARN: Graph is empty")
    except Exception as e:
        print(f"  FAIL: {e}")

    print("\n" + "=" * 60)
    print(f"Results: {passed}/{total} PASSED")
    print("=" * 60)


if __name__ == "__main__":
    main()
