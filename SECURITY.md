# Security Policy

## Supported Versions

| Version | Supported          |
| ------- | ------------------ |
| 5.1.x   | :white_check_mark: |
| 5.0.x   | :white_check_mark: |
| < 5.0   | :x:                |

## Reporting a Vulnerability

If you discover a security vulnerability in JARVIS Research OS, please report it responsibly.

### How to Report

1. **Do NOT** create a public GitHub issue for security vulnerabilities
2. Email security concerns to: security@kaneko-ai.dev
3. Include:
   - Description of the vulnerability
   - Steps to reproduce
   - Potential impact
   - Any suggested fixes

### Response Timeline

- **Acknowledgment**: Within 48 hours
- **Initial Assessment**: Within 7 days
- **Resolution**: Typically within 30 days (depending on severity)

### What to Expect

- We will acknowledge your report
- We will investigate and validate the issue
- We will work on a fix and coordinate disclosure
- We will credit you in the security advisory (if desired)

## Security Best Practices

### For Users

1. **Keep Updated**: Always use the latest version
2. **API Keys**: Never commit API keys to version control
3. **Offline Mode**: Use `--offline` when processing sensitive data
4. **Docker**: Use official images only

### For Developers

1. **Dependencies**: Regularly run `pip-audit` to check for vulnerabilities
2. **Secrets**: Use environment variables, never hardcode
3. **Input Validation**: Always validate user input
4. **Logging**: Never log sensitive data

## Known Security Considerations

### Data Privacy

JARVIS Research OS is designed with privacy in mind:

- **Local First**: All LLM inference can run locally
- **No Telemetry**: No data is sent to external servers by default
- **Free APIs Only**: External API calls go only to free, public APIs (PubMed, arXiv, etc.)

### Dependencies

We regularly audit dependencies for known vulnerabilities. High-severity issues are patched within 7 days.

---

## Contact

- **Security Email**: security@kaneko-ai.dev
- **General Issues**: https://github.com/kaneko-ai/jarvis-ml-pipeline/issues

---

© 2026 JARVIS Team
