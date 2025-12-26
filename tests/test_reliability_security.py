"""
JARVIS Long-term Reliability Tests

M6: 長期信頼性のテスト
- モデル劣化検知
- アクセス制御
- GDPR対応
"""

import pytest
from tempfile import TemporaryDirectory

from jarvis_core.ops.drift_detector import (
    GoldenTestRunner,
    GoldenTestCase,
    DriftDetector,
)
from jarvis_core.ops.security import (
    AccessControl,
    Role,
    Permission,
    GDPRCompliance,
)


class TestGoldenTestRunner:
    """Goldenテストランナーテスト."""
    
    def test_compare_outputs_identical(self):
        """同一出力の比較."""
        with TemporaryDirectory() as tmpdir:
            runner = GoldenTestRunner(golden_dir=tmpdir)
            
            expected = {"key1": "value1", "key2": 0.5}
            actual = {"key1": "value1", "key2": 0.5}
            
            similarity, differences = runner.compare_outputs(expected, actual)
            
            assert similarity == 1.0
            assert len(differences) == 0
    
    def test_compare_outputs_with_tolerance(self):
        """許容誤差内の比較."""
        with TemporaryDirectory() as tmpdir:
            runner = GoldenTestRunner(golden_dir=tmpdir)
            
            expected = {"score": 0.95}
            actual = {"score": 0.94}
            
            similarity, differences = runner.compare_outputs(expected, actual, tolerance=0.05)
            
            assert similarity == 1.0
    
    def test_run_test_pass(self):
        """テスト合格."""
        with TemporaryDirectory() as tmpdir:
            runner = GoldenTestRunner(golden_dir=tmpdir)
            
            test_case = GoldenTestCase(
                test_id="test1",
                input_data={"query": "test"},
                expected_output={"result": "success", "score": 0.9}
            )
            
            actual_output = {"result": "success", "score": 0.91}
            result = runner.run_test(test_case, actual_output)
            
            assert result.passed is True


class TestDriftDetector:
    """劣化検知テスト."""
    
    def test_check_drift_no_alert(self):
        """劣化なしの場合アラートなし."""
        detector = DriftDetector(metrics_path="nonexistent.jsonl")
        
        alert = detector.check_drift(
            metric_name="provenance_rate",
            current_value=0.95,
            baseline=0.96,
            threshold=0.1
        )
        
        assert alert is None
    
    def test_check_drift_alert(self):
        """劣化検知時にアラート生成."""
        detector = DriftDetector(metrics_path="nonexistent.jsonl")
        
        alert = detector.check_drift(
            metric_name="provenance_rate",
            current_value=0.70,
            baseline=0.95,
            threshold=0.1
        )
        
        assert alert is not None
        assert alert.severity in ["high", "critical"]
        assert "provenance_rate" in alert.message


class TestAccessControl:
    """アクセス制御テスト."""
    
    def test_role_permissions(self):
        """ロールに応じたパーミッション."""
        with TemporaryDirectory() as tmpdir:
            ac = AccessControl(audit_path=f"{tmpdir}/access.jsonl")
            
            ac.set_user_role("admin_user", Role.ADMIN)
            ac.set_user_role("readonly_user", Role.READONLY)
            
            assert ac.check_permission("admin_user", Permission.DELETE) is True
            assert ac.check_permission("readonly_user", Permission.DELETE) is False
            assert ac.check_permission("readonly_user", Permission.READ) is True
    
    def test_default_role_readonly(self):
        """デフォルトロールはREADONLY."""
        with TemporaryDirectory() as tmpdir:
            ac = AccessControl(audit_path=f"{tmpdir}/access.jsonl")
            
            role = ac.get_user_role("unknown_user")
            assert role == Role.READONLY


class TestGDPRCompliance:
    """GDPR対応テスト."""
    
    def test_detect_pii_email(self):
        """メールアドレスの検出."""
        with TemporaryDirectory() as tmpdir:
            gdpr = GDPRCompliance(requests_path=f"{tmpdir}/gdpr.jsonl")
            
            text = "Contact us at test@example.com for more info."
            findings = gdpr.detect_pii(text)
            
            assert len(findings) > 0
            assert any(f["type"] == "email" for f in findings)
    
    def test_anonymize_text(self):
        """テキストの匿名化."""
        with TemporaryDirectory() as tmpdir:
            gdpr = GDPRCompliance(requests_path=f"{tmpdir}/gdpr.jsonl")
            
            text = "Email: user@test.com"
            anonymized = gdpr.anonymize_text(text)
            
            assert "user@test.com" not in anonymized
            assert "REDACTED" in anonymized
    
    def test_deletion_request(self):
        """削除リクエストの作成."""
        with TemporaryDirectory() as tmpdir:
            gdpr = GDPRCompliance(requests_path=f"{tmpdir}/gdpr.jsonl")
            
            request = gdpr.create_deletion_request(
                requester="user1",
                target_type="document",
                target_id="doc123",
                reason="GDPR Article 17"
            )
            
            assert request.request_id.startswith("GDPR-")
            assert request.status == "pending"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
