from jarvis_core.validation import (
    EvaluationResult,
    combine_evaluations,
    validate_file_exists,
    validate_json_schema,
)


def test_validate_json_schema_success():
    data = {"answer": "ok", "score": 0.5}
    schema = {"answer": str, "score": (int, float)}

    result = validate_json_schema(data, schema)

    assert result.ok is True
    assert result.errors == []


def test_validate_json_schema_missing_and_type_error():
    data = {"answer": 123}
    schema = {"answer": str, "score": (int, float)}

    result = validate_json_schema(data, schema)

    assert result.ok is False
    assert any("Missing key" in err for err in result.errors)
    assert any("expected type" in err for err in result.errors)


def test_validate_file_exists(tmp_path):
    file_path = tmp_path / "example.txt"
    file_path.write_text("content")

    ok_result = validate_file_exists(str(file_path))
    missing_result = validate_file_exists(str(file_path.with_name("missing.txt")))

    assert ok_result.ok is True
    assert missing_result.ok is False
    assert "does not exist" in missing_result.errors[0]


def test_combine_evaluations():
    res1 = EvaluationResult(ok=True, errors=[])
    res2 = EvaluationResult(ok=False, errors=["e1"], warnings=["w1"], meta={"k": "v"})

    combined = combine_evaluations(res1, res2)

    assert combined.ok is False
    assert combined.errors == ["e1"]
    assert combined.warnings == ["w1"]
    assert combined.meta == {"k": "v"}
