from jarvis_core.summarization.iterative import ChainOfDensitySummarizer


def test_cod_initial_summary():
    summarizer = ChainOfDensitySummarizer(max_iterations=0)
    text = "The quick Brown Fox jumps over the Lazy Dog."

    # Initial summary should be first sentence prefix
    summary = summarizer.summarize(text)
    assert "Initial summary" in summary
    assert "The quick" in summary


def test_cod_refinement():
    summarizer = ChainOfDensitySummarizer(max_iterations=1)
    text = "Apple released the iPhone in 2007. Steve Jobs announced it."

    # Mock logic:
    # Initial: "Initial summary: Apple released the iPhone in 2007."
    # Missing entities from original (Capitalized): Apple, iPhone, Steve, Jobs.
    # (Apple, iPhone are in initial). Missing: Steve, Jobs.
    # Refined: "Initial... (Added: Steve, Jobs)"

    summary = summarizer.summarize(text)
    assert "Added:" in summary
    assert "Steve" in summary or "Jobs" in summary


def test_cod_convergence():
    # Test that it stops even if max_iterations is high, if no new entities found
    summarizer = ChainOfDensitySummarizer(max_iterations=10)
    text = "Simple text."

    summary = summarizer.summarize(text)
    # Should not crash or loop infinitely
    assert len(summary) > 0