"""D3-1 Test: ChromaDB PaperStore - add, search, persist."""
import sys
import time
sys.path.insert(0, ".")

from jarvis_core.embeddings.paper_store import PaperStore

SAMPLE_PAPERS = [
    {
        "title": "PD-1 blockade in tumors with mismatch-repair deficiency",
        "abstract": "Immune checkpoint inhibitors targeting PD-1 have shown remarkable efficacy in various cancers. This study demonstrates that mismatch-repair status predicts clinical benefit of immune checkpoint blockade across tumor types.",
        "doi": "10.1056/NEJMoa1500596",
        "year": "2015",
        "source": "pubmed",
    },
    {
        "title": "Spermidine induces autophagy and extends lifespan",
        "abstract": "Administration of spermidine, a natural polyamine, extends lifespan in yeast, flies, worms, and human immune cells. The mechanism involves induction of autophagy via inhibition of acetyltransferases.",
        "doi": "10.1038/ncb2975",
        "year": "2013",
        "source": "pubmed",
    },
    {
        "title": "Immunosenescence and aging of the immune system",
        "abstract": "Aging is associated with a decline in immune function termed immunosenescence. T cell compartment changes include thymic involution, accumulation of memory cells, and reduced naive T cell output.",
        "doi": "10.1111/imr.12543",
        "year": "2017",
        "source": "openalex",
    },
    {
        "title": "Autophagy in immunity and inflammation",
        "abstract": "Autophagy is a fundamental cellular process for degradation of cytoplasmic contents. Recent studies reveal its critical roles in innate and adaptive immunity, including antigen presentation and lymphocyte development.",
        "doi": "10.1038/nature12015",
        "year": "2013",
        "source": "semantic_scholar",
    },
    {
        "title": "Deep learning for medical image analysis",
        "abstract": "Convolutional neural networks have achieved remarkable performance in medical image classification, segmentation, and detection tasks. This review covers applications in radiology, pathology, and ophthalmology.",
        "doi": "10.1038/s41591-018-0177-5",
        "year": "2018",
        "source": "arxiv",
    },
]

def main():
    print("=" * 60)
    print("D3-1 Test: ChromaDB PaperStore")
    print("=" * 60)
    passed = 0
    total = 4

    # Test 1: Initialize store
    print("\n[Test 1] Initialize PaperStore...")
    try:
        store = PaperStore()
        store.delete_all()
        print(f"  OK: Store initialized, count={store.count()}")
        passed += 1
    except Exception as e:
        print(f"  FAIL: {e}")
        return

    # Test 2: Add papers
    print("\n[Test 2] Add 5 sample papers...")
    try:
        count = store.add_papers(SAMPLE_PAPERS)
        total_count = store.count()
        print(f"  OK: Added {count} papers, total={total_count}")
        assert count == 5, f"Expected 5, got {count}"
        assert total_count == 5, f"Expected total 5, got {total_count}"
        passed += 1
    except Exception as e:
        print(f"  FAIL: {e}")

    # Test 3: Search - relevant query
    print("\n[Test 3] Search 'PD-1 immune checkpoint cancer'...")
    try:
        time.sleep(0.5)
        results = store.search("PD-1 immune checkpoint cancer", top_k=3)
        print(f"  Got {len(results)} results:")
        for i, r in enumerate(results):
            title = r["metadata"].get("title", "?")[:60]
            print(f"    {i+1}. score={r['score']:.4f} | {title}")
        assert len(results) == 3, f"Expected 3, got {len(results)}"
        top_title = results[0]["metadata"].get("title", "")
        assert "PD-1" in top_title, f"Expected PD-1 paper first, got: {top_title}"
        print("  OK: PD-1 paper ranked #1")
        passed += 1
    except Exception as e:
        print(f"  FAIL: {e}")

    # Test 4: Persistence - new instance sees same data
    print("\n[Test 4] Persistence test (new PaperStore instance)...")
    try:
        store2 = PaperStore()
        count2 = store2.count()
        print(f"  New instance count={count2}")
        assert count2 == 5, f"Expected 5, got {count2}"
        results2 = store2.search("autophagy spermidine", top_k=2)
        print(f"  Search results: {len(results2)}")
        for i, r in enumerate(results2):
            title = r["metadata"].get("title", "?")[:60]
            print(f"    {i+1}. score={r['score']:.4f} | {title}")
        print("  OK: Data persisted across instances")
        passed += 1
    except Exception as e:
        print(f"  FAIL: {e}")

    # Summary
    print("\n" + "=" * 60)
    print(f"Results: {passed}/{total} PASSED")
    if passed == total:
        print("D3-1 ChromaDB: ALL TESTS PASSED")
    else:
        print(f"D3-1 ChromaDB: {total - passed} FAILED")
    print("=" * 60)

if __name__ == "__main__":
    main()
