"""Tests for validation module."""

from pathlib import Path

from jarvis_core.validation import (
    EvaluationResult,
    validate_json_schema,
    validate_file_exists,
    combine_evaluations,
)


class TestEvaluationResult:
    def test_creation_ok(self):
        result = EvaluationResult(ok=True)
        
        assert result.ok is True
        assert result.errors == []
        assert result.warnings == []

    def test_creation_with_errors(self):
        result = EvaluationResult(
            ok=False,
            errors=["Error 1", "Error 2"],
        )
        
        assert result.ok is False
        assert len(result.errors) == 2

    def test_post_init_none_handling(self):
        result = EvaluationResult(ok=True, warnings=None, meta=None)
        
        assert result.warnings == []
        assert result.meta == {}


class TestValidateJsonSchema:
    def test_valid_data(self):
        data = {"name": "Alice", "age": 30}
        schema = {"name": str, "age": int}
        
        result = validate_json_schema(data, schema)
        
        assert result.ok is True
        assert result.errors == []

    def test_missing_key(self):
        data = {"name": "Alice"}
        schema = {"name": str, "age": int}
        
        result = validate_json_schema(data, schema)
        
        assert result.ok is False
        assert any("Missing key" in e for e in result.errors)

    def test_wrong_type(self):
        data = {"name": "Alice", "age": "thirty"}
        schema = {"name": str, "age": int}
        
        result = validate_json_schema(data, schema)
        
        assert result.ok is False
        assert any("expected type" in e for e in result.errors)

    def test_invalid_schema(self):
        data = {"key": "value"}
        schema = "not a dict"
        
        result = validate_json_schema(data, schema)
        
        assert result.ok is False

    def test_invalid_data(self):
        data = "not a dict"
        schema = {"key": str}
        
        result = validate_json_schema(data, schema)
        
        assert result.ok is False


class TestValidateFileExists:
    def test_existing_file(self, tmp_path):
        file = tmp_path / "test.txt"
        file.write_text("content")
        
        result = validate_file_exists(str(file))
        
        assert result.ok is True

    def test_nonexistent_file(self, tmp_path):
        result = validate_file_exists(str(tmp_path / "nonexistent.txt"))
        
        assert result.ok is False
        assert any("does not exist" in e for e in result.errors)


class TestCombineEvaluations:
    def test_all_ok(self):
        r1 = EvaluationResult(ok=True)
        r2 = EvaluationResult(ok=True)
        
        combined = combine_evaluations(r1, r2)
        
        assert combined.ok is True

    def test_any_failure(self):
        r1 = EvaluationResult(ok=True)
        r2 = EvaluationResult(ok=False, errors=["Error"])
        
        combined = combine_evaluations(r1, r2)
        
        assert combined.ok is False
        assert "Error" in combined.errors

    def test_merges_errors_and_warnings(self):
        r1 = EvaluationResult(ok=False, errors=["E1"], warnings=["W1"])
        r2 = EvaluationResult(ok=False, errors=["E2"], warnings=["W2"])
        
        combined = combine_evaluations(r1, r2)
        
        assert len(combined.errors) == 2
        assert len(combined.warnings) == 2

    def test_merges_meta(self):
        r1 = EvaluationResult(ok=True, meta={"key1": "value1"})
        r2 = EvaluationResult(ok=True, meta={"key2": "value2"})
        
        combined = combine_evaluations(r1, r2)
        
        assert combined.meta["key1"] == "value1"
        assert combined.meta["key2"] == "value2"
