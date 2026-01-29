import pytest
from pathlib import Path
from scripts.detect_garbage_code import scan_file


def test_detect_pass_only(tmp_path):
    """passのみの関数を検出できるかテスト"""
    p = tmp_path / "test_pass.py"
    p.write_text("def dummy():\n    pass", encoding="utf-8")
    issues = scan_file(p)
    assert len(issues) == 1
    assert "ダミー実装（passのみ）" in issues[0]


def test_detect_return_none(tmp_path):
    """return Noneのみの関数を検出できるかテスト"""
    p = tmp_path / "test_none.py"
    p.write_text("def dummy():\n    return None", encoding="utf-8")
    issues = scan_file(p)
    assert len(issues) == 1
    assert "ダミー実装（return Noneのみ）" in issues[0]


def test_detect_return_constant(tmp_path):
    """return Constantのみの関数を検出できるかテスト"""
    p = tmp_path / "test_const.py"
    p.write_text("def dummy():\n    return True", encoding="utf-8")
    issues = scan_file(p)
    assert len(issues) == 1
    assert "ダミー実装（return Trueのみ）" in issues[0]


def test_detect_except_pass(tmp_path):
    """except: passを検出できるかテスト"""
    p = tmp_path / "test_except.py"
    p.write_text("try:\n    1/0\nexcept:\n    pass", encoding="utf-8")
    issues = scan_file(p)
    assert len(issues) == 1
    assert "握りつぶしexcept（except: pass）" in issues[0]


def test_normal_code_no_issue(tmp_path):
    """正常なコードが検出されないことを確認"""
    content = """
def normal_func(x):
    if x > 0:
        return x * 2
    return 0

try:
    result = 10 / 2
except ZeroDivisionError:
    print("Error")
    raise
"""
    p = tmp_path / "test_normal.py"
    p.write_text(content, encoding="utf-8")
    issues = scan_file(p)
    assert len(issues) == 0
