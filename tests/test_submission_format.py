"""
Tabular Submission Format Tests

提出CSVの形式検証
"""

import pytest
import tempfile
from pathlib import Path

np = pytest.importorskip("numpy")
pd = pytest.importorskip("pandas")

from pipelines.tabular.submission import make_submission, validate_submission


class TestMakeSubmission:
    """make_submission テスト."""
    
    def test_basic_submission(self):
        """基本的な提出CSVが作成できること."""
        with tempfile.TemporaryDirectory() as tmpdir:
            predictions = [0, 1, 2, 1, 0]
            out_path = Path(tmpdir) / "submission.csv"
            
            result_path = make_submission(
                predictions,
                str(out_path),
                target_col="class",
            )
            
            assert result_path.exists()
            
            # 再読み込み確認
            df = pd.read_csv(result_path)
            assert list(df.columns) == ["class"]
            assert len(df) == 5
    
    def test_label_offset(self):
        """ラベルオフセットが適用されること."""
        with tempfile.TemporaryDirectory() as tmpdir:
            predictions = [0, 1, 2]  # 0始まり
            out_path = Path(tmpdir) / "submission.csv"
            
            make_submission(
                predictions,
                str(out_path),
                target_col="class",
                label_offset=1,  # 1始まりに変換
            )
            
            df = pd.read_csv(out_path)
            assert list(df["class"]) == [1, 2, 3]


class TestValidateSubmission:
    """validate_submission テスト."""
    
    def test_valid_submission(self):
        """有効な提出CSVが検証できること."""
        with tempfile.TemporaryDirectory() as tmpdir:
            df = pd.DataFrame({"class": [0, 1, 2]})
            path = Path(tmpdir) / "submission.csv"
            df.to_csv(path, index=False, lineterminator='\n')
            
            assert validate_submission(str(path), "class", expected_rows=3) is True
    
    def test_wrong_column_raises(self):
        """列名が違う場合エラーになること."""
        with tempfile.TemporaryDirectory() as tmpdir:
            df = pd.DataFrame({"prediction": [0, 1, 2]})  # 間違った列名
            path = Path(tmpdir) / "submission.csv"
            df.to_csv(path, index=False)
            
            with pytest.raises(ValueError, match="Column name mismatch"):
                validate_submission(str(path), "class")
    
    def test_wrong_row_count_raises(self):
        """行数が違う場合エラーになること."""
        with tempfile.TemporaryDirectory() as tmpdir:
            df = pd.DataFrame({"class": [0, 1]})
            path = Path(tmpdir) / "submission.csv"
            df.to_csv(path, index=False)
            
            with pytest.raises(ValueError, match="Row count mismatch"):
                validate_submission(str(path), "class", expected_rows=5)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
