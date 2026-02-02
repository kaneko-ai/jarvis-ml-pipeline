.PHONY: api-map test-smoke ci-sweep

api-map:
	@echo "Generating API map..."
	uv run python -c "from jarvis_web.contracts.generator import generate_api_map; generate_api_map() if hasattr(__import__('jarvis_web.contracts.generator', fromlist=['generate_api_map']), 'generate_api_map') else print('Generator not found, using static map')"
	@echo "API map status checked/generated at jarvis_web/contracts/api_map_v1.json"

test-smoke:
	pytest tests/test_api_map_vs_capabilities.py tests/test_front_adapter_contract.py

ci-sweep:
	python scripts/ci_sweep.py
