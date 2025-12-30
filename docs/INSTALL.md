# JARVIS Research OS Installation Guide

## Quick Start

```bash
# Clone
git clone https://github.com/your-org/jarvis-ml-pipeline.git
cd jarvis-ml-pipeline

# Create virtual environment
python -m venv .venv

# Activate (Windows)
.venv\Scripts\activate

# Activate (Linux/Mac)
source .venv/bin/activate

# Install locked dependencies
pip install -r requirements.lock
```

## Verify Installation

```bash
# Run core tests
python -m pytest -m core -v --tb=short

# Check imports
python -c "from jarvis_core import run_jarvis; print('OK')"
```

## Windows Specific

```powershell
# PowerShell execution policy
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser

# Run tests
.\scripts\run_core_tests.ps1
```

## Optional Dependencies

### PDF Processing (recommended)
```bash
pip install PyMuPDF PyPDF2 pdfminer.six
```

### LLM Integration
```bash
pip install google-generativeai
# Set: GOOGLE_API_KEY=your_key
```

### Web API
```bash
pip install fastapi uvicorn

# Run the API locally
uvicorn jarvis_web.app:create_app --factory --host 0.0.0.0 --port 8000
```

### Embeddings
```bash
pip install sentence-transformers
```

## Environment Variables

```bash
# Optional: PubMed API (higher rate limits)
NCBI_API_KEY=your_key

# Optional: Unpaywall
UNPAYWALL_EMAIL=your@email.com

# LLM Provider
LLM_PROVIDER=gemini  # or ollama
OLLAMA_MODEL=llama3  # if using ollama
```

## Troubleshooting

### PyMuPDF on Windows
If `pip install PyMuPDF` fails, try:
```bash
pip install --upgrade pip wheel
pip install PyMuPDF
```

### Network Tests
If tests fail due to network issues:
```bash
# Run without network-dependent tests
python -m pytest -m "core and not network"
```

## Development

```bash
# Install dev dependencies
pip install -e ".[dev]"

# Run all tests
python -m pytest -v

# Run specific test file
python -m pytest tests/test_v4_roads.py -v
```
