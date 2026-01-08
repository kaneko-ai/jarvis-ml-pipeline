"""
Tabular I/O Schema Tests

列整合、スキーマ検証のテスト
"""

from pipelines.tabular.io import load_train_test, validate_schema
import tempfile
from pathlib import Path

import pytest

pd = pytest.importorskip("pandas")
np = pytest.importorskip("numpy")


class TestLoadTrainTest:
    """load_train_test テスト."""

    def test_basic_load(self):
        """基本的な読み込みができること."""
        with tempfile.TemporaryDirectory() as tmpdir:
            # 訓練データ
            train_df = pd.DataFrame(
                {
                    "f1": [1, 2, 3],
                    "f2": [4, 5, 6],
                    "Class": [0, 1, 0],
                }
            )
            train_path = Path(tmpdir) / "train.csv"
            train_df.to_csv(train_path, index=False)

            # テストデータ
            test_df = pd.DataFrame(
                {
                    "f1": [7, 8],
                    "f2": [9, 10],
                }
            )
            test_path = Path(tmpdir) / "test.csv"
            test_df.to_csv(test_path, index=False)

            # 読み込み
            X_train, X_test, y_train, schema = load_train_test(
                str(train_path),
                str(test_path),
                "Class",
            )

            assert X_train.shape == (3, 2)
            assert X_test.shape == (2, 2)
            assert len(y_train) == 3
            assert schema.label_column == "Class"

    def test_column_mismatch_raises(self):
        """列不整合でエラーになること."""
        with tempfile.TemporaryDirectory() as tmpdir:
            train_df = pd.DataFrame(
                {
                    "f1": [1, 2],
                    "f2": [3, 4],
                    "Class": [0, 1],
                }
            )
            train_path = Path(tmpdir) / "train.csv"
            train_df.to_csv(train_path, index=False)

            # 列が異なる
            test_df = pd.DataFrame(
                {
                    "f1": [5],
                    "f3": [6],  # f2ではなくf3
                }
            )
            test_path = Path(tmpdir) / "test.csv"
            test_df.to_csv(test_path, index=False)

            with pytest.raises(ValueError, match="Column mismatch"):
                load_train_test(str(train_path), str(test_path), "Class")

    def test_missing_label_raises(self):
        """ラベル列がない場合エラーになること."""
        with tempfile.TemporaryDirectory() as tmpdir:
            train_df = pd.DataFrame({"f1": [1], "f2": [2]})
            train_path = Path(tmpdir) / "train.csv"
            train_df.to_csv(train_path, index=False)

            test_df = pd.DataFrame({"f1": [3], "f2": [4]})
            test_path = Path(tmpdir) / "test.csv"
            test_df.to_csv(test_path, index=False)

            with pytest.raises(ValueError, match="Label column"):
                load_train_test(str(train_path), str(test_path), "Class")

class TestValidateSchema:
    """validate_schema テスト."""

    def test_valid_schema(self):
        """有効なスキーマが検証できること."""
        X_train = pd.DataFrame({"f1": [1, 2], "f2": [3, 4]})
        X_test = pd.DataFrame({"f1": [5], "f2": [6]})
        y_train = pd.Series([0, 1])

        assert validate_schema(X_train, X_test, y_train) is True

if __name__ == "__main__":
    pytest.main([__file__, "-v"])
