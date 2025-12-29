.PHONY: api-map test-contract test-smoke test-e2e-mock test-all

api-map:
	python scripts/generate_api_map.py

test-contract:
	pytest -q tests/test_api_map_vs_capabilities.py tests/test_front_adapter_contract.py

test-smoke:
	pytest -q tests/smoke_api_v1.py

test-e2e-mock:
	npm install
	./scripts/run_e2e_mock.sh

test-all: test-contract test-smoke test-e2e-mock
