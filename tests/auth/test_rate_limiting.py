import time
from unittest.mock import patch
from jarvis_core.auth.api_key import APIKeyManager

def test_sliding_window_rate_limiting():
    # Start at a fixed minute start
    start_time = 1000000.0
    
    with patch('jarvis_core.auth.api_key.time.time') as mock_t:
        mock_t.return_value = start_time
        manager = APIKeyManager(secret="test-secret")
        
        # 1. Generate a key with low rate limit for testing
        key = manager.generate_key(name="test", rate_limit=5)
        
        # 2. Consume limit (5 requests)
        print("\nSending 5 requests...")
        for i in range(5):
            result = manager.validate(key)
            assert result.success is True, f"Request {i+1} should succeed"
            
        # 3. Next one (6th) should fail
        print("Sending 6th request...")
        result = manager.validate(key)
        assert result.success is False, f"Request 6 should fail, but got success={result.success}"
        assert result.error == "Rate limit exceeded"
        
        # 4. Forward time by 61 minutes
        mock_t.return_value = start_time + 3660
        print("Forwarding time by 61 minutes...")
        
        # Should be allowed again
        result = manager.validate(key)
        assert result.success is True, f"Should be allowed after time pass, but got error={result.error}"

def test_bucket_accumulation():
    # Start at a fixed time
    start_time = 2000000.0
    
    with patch('jarvis_core.auth.api_key.time.time') as mock_t:
        mock_t.return_value = start_time
        manager = APIKeyManager(secret="test-secret")
        key = manager.generate_key(name="test", rate_limit=10)
        
        # Minute 1: 4 requests
        mock_t.return_value = start_time
        for _ in range(4): manager.validate(key)
        
        # Minute 30: 4 requests
        mock_t.return_value = start_time + 1800
        for _ in range(4): manager.validate(key)
        
        # Total is 8/10, so should still be OK
        assert manager.validate(key).success is True  # 9th
        assert manager.validate(key).success is True  # 10th
        assert manager.validate(key).success is False # 11th (Exceeded)
        
        # Minute 62: Minute 1 should be out of window
        # Window start = (2000000 + 3720 - 3600) = 2000120. 
        # Minute 1 (2000000) is now excluded.
        mock_t.return_value = start_time + 3720
        assert manager.validate(key).success is True, "Minute 1 should be expired now"
