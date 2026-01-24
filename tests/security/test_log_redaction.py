import logging
import io
from jarvis_core.redact_logging import RedactionFilter, setup_logging

def test_redaction_filter_basic():
    # Setup a stream to capture log output
    stream = io.StringIO()
    handler = logging.StreamHandler(stream)
    handler.setFormatter(logging.Formatter("%(message)s"))
    handler.addFilter(RedactionFilter())
    
    logger = logging.getLogger("test_redaction")
    logger.addHandler(handler)
    logger.setLevel(logging.INFO)
    
    # Test cases: (Input string, Expected keyword in output, Should be redacted)
    cases = [
        ("Using api_key: 123", "123", False),  # Too short
        ("Using api_key='secret-key-12345'", "[REDACTED]", True),
        ("Authorization: Bearer my-token-999-long", "[REDACTED]", True),
        ("Nothing sensitive here", "Nothing sensitive here", False),
        ("token: 'xyz-123-abc-def'", "[REDACTED]", True),
        ("github_token: abcdef1234567890", "[REDACTED]", True),
    ]
    
    for input_str, expected, should_redact in cases:
        stream.truncate(0)
        stream.seek(0)
        logger.info(input_str)
        output = stream.getvalue().strip()
        
        if should_redact:
            assert "[REDACTED]" in output, f"Failed to redact: {input_str}"
        else:
            assert expected in output, f"Should NOT have redacted: {input_str}"

def test_redaction_filter_args():
    stream = io.StringIO()
    handler = logging.StreamHandler(stream)
    handler.setFormatter(logging.Formatter("%(message)s"))
    handler.addFilter(RedactionFilter())
    
    logger = logging.getLogger("test_redaction_args")
    logger.addHandler(handler)
    logger.setLevel(logging.INFO)
    
    # Test logging with arguments
    logger.info("Setting key %s", "api_key='my-actual-key'")
    output = stream.getvalue()
    assert "[REDACTED]" in output
    assert "my-actual-key" not in output

def test_setup_logging_integration():
    # Verify setup_logging actually attaches the filter
    logger = setup_logging("DEBUG")
    
    found_filter = False
    for handler in logger.handlers:
        for f in handler.filters:
            if isinstance(f, RedactionFilter):
                found_filter = True
                break
    
    assert found_filter, "RedactionFilter was not found in root logger handlers"
