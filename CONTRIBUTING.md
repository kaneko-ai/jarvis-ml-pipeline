# Contributing to JARVIS Research OS

Thank you for your interest in contributing to JARVIS Research OS!

## Development Setup

### Prerequisites

- Python 3.10+
- uv (recommended) or pip
- Node.js 20+ (for dashboard development)

### Installation

```bash
# Clone the repository
git clone https://github.com/kaneko-ai/jarvis-ml-pipeline.git
cd jarvis-ml-pipeline

# Install with uv (recommended)
uv sync

# Or with pip
pip install -e ".[dev]"
```

### Environment Variables

環境変数は `.env.example` をコピーして `.env` を作成してください。
`.env` は絶対にコミットしないでください。

### Running Tests

```bash
# All tests
uv run pytest

# With coverage
uv run pytest --cov=jarvis_core --cov-report=html

# Specific module
uv run pytest tests/test_evidence_grading.py -v
```

### Code Style

We use `black` for formatting and `ruff` for linting:

```bash
# Format
uv run black jarvis_core tests

# Lint
uv run ruff check jarvis_core tests

# Fix lint issues
uv run ruff check --fix jarvis_core tests
```

## Pull Request Process

1. **Fork** the repository
2. **Create a branch** from `main`:
   ```bash
   git checkout -b feature/your-feature-name
   ```
3. **Make changes** and add tests
4. **Run tests** and ensure all pass
5. **Format code** with black
6. **Commit** with clear message:
   ```
   feat(module): Add new feature X
   
   - Detailed description
   - Closes #123
   ```
7. **Push** and create Pull Request

## Commit Message Convention

We follow [Conventional Commits](https://www.conventionalcommits.org/):

| Type | Description |
|------|-------------|
| `feat` | New feature |
| `fix` | Bug fix |
| `docs` | Documentation only |
| `style` | Code style (formatting, etc.) |
| `refactor` | Code refactoring |
| `test` | Adding/updating tests |
| `chore` | Maintenance tasks |
| `perf` | Performance improvements |
| `ci` | CI/CD changes |

### Examples

```
feat(evidence): Add ensemble grading with confidence scores
fix(prisma): Correct PRISMA 2020 flow calculation
docs(api): Update REST API documentation
test(active-learning): Add stopping criterion tests
```

## Code Standards

### Python

- Type hints required for all public functions
- Docstrings in Google style
- Maximum line length: 100 characters
- Test coverage minimum: 80%

```python
def grade_evidence(
    title: str,
    abstract: str,
    use_llm: bool = False,
) -> EvidenceGrade:
    """Grade the evidence level of a paper.
    
    Args:
        title: Paper title
        abstract: Paper abstract
        use_llm: Whether to use LLM for classification
        
    Returns:
        EvidenceGrade with level, study type, and confidence
        
    Raises:
        ValueError: If title and abstract are both empty
    """
    ...
```

### Tests

- One test file per module: `test_{module}.py`
- Use pytest fixtures
- Mock external dependencies
- Include both positive and negative test cases

```python
class TestEvidenceGrading:
    """Tests for evidence grading module."""
    
    def test_grade_rct_paper(self):
        """Test grading a randomized controlled trial."""
        ...
    
    def test_grade_empty_input_raises(self):
        """Test that empty input raises ValueError."""
        with pytest.raises(ValueError):
            grade_evidence("", "")
```

## Adding New Modules

1. Create module in `jarvis_core/{module_name}/`
2. Add `__init__.py` with public exports
3. Create test file `tests/test_{module_name}.py`
4. Update `pyproject.toml` if new dependencies needed
5. Add documentation in `docs/`

### Module Structure

```
jarvis_core/
└── new_module/
    ├── __init__.py      # Public API exports
    ├── schema.py        # Data classes and types
    ├── core.py          # Main logic
    └── utils.py         # Helper functions
```

## Reporting Issues

Please include:

- Python version
- OS (Windows/macOS/Linux)
- Steps to reproduce
- Expected vs actual behavior
- Error messages/stack traces

### Issue Template

```markdown
## Description
[Clear description of the issue]

## Steps to Reproduce
1. ...
2. ...

## Expected Behavior
[What should happen]

## Actual Behavior
[What actually happens]

## Environment
- OS: Windows 11
- Python: 3.11.5
- JARVIS version: 1.0.0
```

## Feature Requests

When proposing new features:

1. Check existing issues first
2. Describe the use case
3. Propose API design if applicable
4. Consider backward compatibility

## Code of Conduct

- Be respectful and inclusive
- Provide constructive feedback
- Help newcomers
- Focus on the problem, not the person

## Security

Found a security issue? Please email security@kaneko-ai.dev instead of opening a public issue.

## License

By contributing, you agree that your contributions will be licensed under the MIT License.

## Questions?

- Open a GitHub Discussion
- Check the documentation at `docs/`
- Review existing issues and PRs

Thank you for contributing to JARVIS Research OS! 🎉
