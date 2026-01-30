import logging
import io
from jarvis_core.security.redaction import RedactingFilter


def test_logging_redaction():
    # Setup logger with RedactingFilter
    logger = logging.getLogger("test_redact")
    logger.setLevel(logging.DEBUG)

    log_capture = io.StringIO()
    handler = logging.StreamHandler(log_capture)
    handler.setFormatter(logging.Formatter("%(message)s"))

    # Add our redacting filter
    redact_filter = RedactingFilter(patterns=[r"SECRET_VAL:(\d+)"])
    handler.addFilter(redact_filter)
    logger.addHandler(handler)

    try:
        # 1. Test explicit pattern
        logger.info("The value is SECRET_VAL:12345")

        # 2. Test common pattern (Bearer token)
        logger.info("Using token Bearer abc-123-def")

        # 3. Test args redaction
        logger.info("Checking key %s", "API_KEY='secret-key-123'")

        log_output = log_capture.getvalue()
        print(f"\nDEBUG LOG OUTPUT:\n{log_output}")

        # Check explicit pattern
        assert "SECRET_VAL:********" in log_output
        assert "12345" not in log_output

        # Check Bearer token
        assert "Using token Bearer ********" in log_output
        assert "abc-123-def" not in log_output

        # Check pattern in arguments
        # If API_KEY is in args, RedactingFilter should catch it even if not in the main format string
        # depending on how it's handled. But if it's passed as %s, it's in record.args.
        assert "secret-key-123" not in log_output
        assert "********" in log_output or "█" in log_output

    finally:
        logger.removeHandler(handler)


def test_setup_convenience():
    # Verify that setup_logging_redaction adds filter to specified loggers
    from jarvis_core.security.redaction import setup_logging_redaction

    # We'll just check if it runs without error and attaches filters
    setup_logging_redaction()

    for name in ["jarvis_core", "jarvis_web"]:
        l = logging.getLogger(name)
        assert any(isinstance(f, RedactingFilter) for f in l.filters)