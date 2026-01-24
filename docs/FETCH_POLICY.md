# Fetch Policy Documentation

> Authority: REFERENCE (Level 2, Non-binding)


Per RP-157, this documents the official fetch policy for paper sources.

## Policy Version

**Current Version:** 1.0
**Last Updated:** 2024-12-22

## Source Priority Order

When fetching papers, sources are tried in this order:

1. **Local** - Papers already downloaded
2. **PMC OA** - PubMed Central Open Access
3. **Unpaywall** - Open Access via Unpaywall API
4. **Publisher** - Direct from publisher (OA only by default)
5. **HTML Fallback** - Extract from web page

## Allowed Domains

### Should Allowed
- `ncbi.nlm.nih.gov` (PubMed, PMC)
- `pmc.ncbi.nlm.nih.gov`
- `pubmed.ncbi.nlm.nih.gov`

### Conditionally Allowed
- `doi.org` - DOI resolution only
- Publisher domains - When `publisher_pdf_enabled=True`

### Denied
- Sci-Hub and similar
- Paywalled content without authorization

## Configuration

```python
from jarvis_tools.papers.fetch_policy import FetchPolicy

policy = FetchPolicy(
    publisher_pdf_enabled=False,  # Only OA by default
    publisher_pdf_oa_only=True,   # Require OA flag
    html_fallback_enabled=True,   # Allow HTML extraction
)
```

## Telemetry Events

- `FETCH_CANDIDATES` - Candidate URLs enumerated
- `FETCH_POLICY_DECISION` - Allow/deny decision with reason
- `FETCH_ATTEMPT` - Fetch started
- `FETCH_RESULT` - Fetch completed (success/fail)
- `FETCH_LEGAL_META_RECORDED` - Legal metadata attached

## Audit Trail

Every fetch records:
- Source type
- Domain
- Policy version
- Allow/deny reason
- Timestamp

This enables compliance review and policy updates.

## Updating Policy

1. Update `fetch_policy.py`
2. Increment version number
3. Update this document
4. Run policy tests: `pytest tests/ -k fetch_policy`
