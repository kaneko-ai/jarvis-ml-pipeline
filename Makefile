.PHONY: api-map test-smoke

api-map:
	python tools/generate_api_map.py

test-smoke:
	pytest tests/test_api_map_vs_capabilities.py tests/test_front_adapter_contract.py
