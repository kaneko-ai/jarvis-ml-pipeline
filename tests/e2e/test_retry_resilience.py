import pytest
from jarvis_core.llm_utils import LLMClient
from jarvis_core.retry import RetryPolicy

def test_llm_retry_resilience():
    """Verify that LLMClient can recover from temporary failures using stateful MockLLM."""
    # 1. Setup client with mock provider
    client = LLMClient(model="mock-model", provider="mock")
    
    # Access the internal mock engine (added in PR10)
    mock = client._mock_engine
    
    # 2. Configure mock to fail twice then succeed
    # We want max_attempts=3, so 2 failures should result in a success on the 3rd try.
    mock.configure(failures=2, error_msg="Temporary Server Overload")
    
    # 3. Create a retry policy
    # base_delay=0.1 to keep tests fast
    policy = RetryPolicy(max_attempts=3, base_delay=0.1, jitter=False)
    
    # 4. Execute a chat call via the policy
    messages = [{"role": "user", "content": "Hello, resolve this scientific query."}]
    
    # We need to wrap the chat call in a lambda because execute expects a callable
    # Note: chat expecting list[Message] but we pass list[dict] here for simplicity if allowed,
    # but let's be careful with types.
    from jarvis_core.llm_utils import Message
    msgs = [Message(role="user", content="Hello")]
    
    result = policy.execute(client.chat, msgs)
    
    # 5. Assertions
    assert "Mock response (3)" in result
    assert mock.call_count == 3
    assert mock.failures_remaining == 0
    assert mock.budget_remaining == 99.0 # 100 - 1 success (failures don't consume budget in our mock)

def test_llm_retry_exhaustion():
    """Verify that it eventually raises an error if failures exceed max_attempts."""
    client = LLMClient(model="mock-model", provider="mock")
    mock = client._mock_engine
    
    # 5 failures, but only 3 attempts allowed
    mock.configure(failures=5)
    policy = RetryPolicy(max_attempts=3, base_delay=0.01)
    
    from jarvis_core.llm_utils import Message
    msgs = [Message(role="user", content="Hello")]
    
    with pytest.raises(RuntimeError, match="Simulated LLM Error"):
        policy.execute(client.chat, msgs)
        
    assert mock.call_count == 3
    assert mock.failures_remaining == 2
