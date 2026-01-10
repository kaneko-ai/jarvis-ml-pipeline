"""Tests for telemetry.redact module."""

from jarvis_core.telemetry.redact import redact_string, redact_dict


class TestRedactString:
    def test_redact_email(self):
        text = "Contact: user@example.com for info"
        result = redact_string(text)
        
        assert "user@example.com" not in result
        assert "***EMAIL***" in result

    def test_redact_openai_key(self):
        text = "Key: sk-abcdefghijklmnopqrstuvwxyz123456"
        result = redact_string(text)
        
        assert "sk-" not in result

    def test_redact_password(self):
        text = "password=mysecretpass123"
        result = redact_string(text)
        
        assert "mysecretpass" not in result
        assert "***PASSWORD***" in result

    def test_redact_token(self):
        text = "token=abcd1234secret"
        result = redact_string(text)
        
        assert "abcd1234secret" not in result

    def test_no_sensitive_data(self):
        text = "This is a normal message"
        result = redact_string(text)
        
        assert result == text or "normal" in result


class TestRedactDict:
    def test_redact_password_key(self):
        data = {"username": "admin", "password": "secret123"}
        result = redact_dict(data)
        
        assert result["username"] == "admin"
        assert result["password"] == "***REDACTED***"

    def test_redact_secret_key(self):
        data = {"api_key": "my_secret_key", "name": "test"}
        result = redact_dict(data)
        
        assert result["api_key"] == "***REDACTED***"
        assert result["name"] == "test"

    def test_redact_nested_dict(self):
        data = {
            "config": {
                "password": "nested_secret",
                "debug": True
            }
        }
        result = redact_dict(data)
        
        assert result["config"]["password"] == "***REDACTED***"
        assert result["config"]["debug"] is True

    def test_redact_list_values(self):
        data = {
            "emails": ["user1@example.com", "user2@example.com"],
            "items": ["normal", "data"]
        }
        result = redact_dict(data)
        
        # Emails should be redacted
        assert "***EMAIL***" in result["emails"][0]

    def test_max_depth_protection(self):
        # Deeply nested structure
        data = {"level1": {"level2": {"level3": {"level4": {"level5": {"level6": "value"}}}}}}
        result = redact_dict(data, max_depth=3)
        
        # Should not crash, just return data at depth limit
        assert result is not None
