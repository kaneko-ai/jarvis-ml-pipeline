"""
JARVIS Spec Lint Tests

spec_lint.py の回帰テスト
"""

# spec_lint をインポート（相対パスで）
import sys
from pathlib import Path

# Ensure tools directory is in path for importing spec_lint
# paths
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))

from spec_lint import check_file, extract_authority  # noqa: E402


class TestExtractAuthority:
    """Authority抽出テスト."""

    def test_reference_level(self):
        content = "> Authority: REFERENCE (Level 4, Non-binding)\n\n# Title"
        assert extract_authority(content) == "REFERENCE"

    def test_spec_level(self):
        content = "> Authority: SPEC (Level 1, Binding)\n\n# Title"
        assert extract_authority(content) == "SPEC"

    def test_no_header(self):
        content = "# Title\n\nNo authority header"
        assert extract_authority(content) is None


class TestCheckFile:
    """ファイルチェックテスト."""

    def test_reference_with_must_fails(self, tmp_path):
        """REFERENCE文書でMUSTを使うと違反."""
        md = tmp_path / "test.md"
        md.write_text("> Authority: REFERENCE (Level 4, Non-binding)\n\nYou MUST do this.")

        violations = check_file(md)
        assert len(violations) == 1
        assert violations[0].word == "MUST"

    def test_spec_with_must_passes(self, tmp_path):
        """SPEC文書でMUSTを使っても違反なし."""
        md = tmp_path / "test.md"
        md.write_text("> Authority: SPEC (Level 1, Binding)\n\nYou MUST do this.")

        violations = check_file(md)
        assert len(violations) == 0

    def test_roadmap_with_required_fails(self, tmp_path):
        """ROADMAP文書でREQUIREDを使うと違反."""
        md = tmp_path / "test.md"
        md.write_text("> Authority: ROADMAP (Level 5, Non-binding)\n\nThis is REQUIRED.")

        violations = check_file(md)
        assert len(violations) == 1

    def test_japanese_force_word(self, tmp_path):
        """日本語の強制語彙も検出."""
        md = tmp_path / "test.md"
        md.write_text(
            "> Authority: REFERENCE (Level 4, Non-binding)\n\nこれは必須です。", encoding="utf-8"
        )

        violations = check_file(md)
        assert len(violations) == 1
        assert "必須" in violations[0].word
