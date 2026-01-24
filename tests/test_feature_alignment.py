"""
Tabular Feature Alignment Tests

列順固定、特徴量整合のテスト
"""

from pipelines.tabular.io import load_train_test
from pipelines.tabular.preprocess import fit_transform, transform
import tempfile
from pathlib import Path

import pytest

np = pytest.importorskip("numpy")
pd = pytest.importorskip("pandas")
pytest.importorskip("sklearn")


class TestFeatureAlignment:
    """特徴量整合テスト."""

    def test_column_order_preserved(self):
        """列順が保持されること."""
        with tempfile.TemporaryDirectory() as tmpdir:
            # 訓練データ
            train_df = pd.DataFrame(
                {
                    "a": [1, 2],
                    "b": [3, 4],
                    "c": [5, 6],
                    "label": [0, 1],
                }
            )
            train_path = Path(tmpdir) / "train.csv"
            train_df.to_csv(train_path, index=False)

            # テストデータ（列順が異なる）
            test_df = pd.DataFrame(
                {
                    "c": [7],
                    "a": [8],
                    "b": [9],
                }
            )
            test_path = Path(tmpdir) / "test.csv"
            test_df.to_csv(test_path, index=False)

            X_train, X_test, y_train, schema = load_train_test(
                str(train_path),
                str(test_path),
                "label",
            )

            # 列順がtrainと同じになっていること
            assert list(X_train.columns) == list(X_test.columns)
            assert list(X_test.columns) == ["a", "b", "c"]

    def test_scaler_alignment(self):
        """Scalerでも整合性が保たれること."""
        X_train = pd.DataFrame(
            {
                "f1": [1.0, 2.0, 3.0],
                "f2": [10.0, 20.0, 30.0],
            }
        )
        X_test = pd.DataFrame(
            {
                "f1": [4.0],
                "f2": [40.0],
            }
        )

        from sklearn.preprocessing import StandardScaler

        scaler = StandardScaler()

        X_train_scaled, scaler = fit_transform(X_train, scaler)
        X_test_scaled = transform(X_test, scaler)

        # 形状が正しいこと
        assert X_train_scaled.shape == (3, 2)
        assert X_test_scaled.shape == (1, 2)

        # dtypeがfloat32であること
        assert X_train_scaled.dtype == np.float32
        assert X_test_scaled.dtype == np.float32

if __name__ == "__main__":
    pytest.main([__file__, "-v"])
