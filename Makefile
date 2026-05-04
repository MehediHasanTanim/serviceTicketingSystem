PYTHON ?= python3

BACKEND_DIR := backend/services/identity_service
FRONTEND_DIR := fronend

.PHONY: test test-backend test-frontend test-coverage test-backend-coverage test-frontend-coverage test-service-order-audit
.PHONY: lint lint-backend lint-frontend quality

test: test-backend test-frontend

test-backend:
	@cd $(BACKEND_DIR) && $(PYTHON) -c "import pytest" >/dev/null 2>&1 || { \
		echo "pytest is not installed for $(PYTHON)."; \
		echo "Install backend deps with: cd $(BACKEND_DIR) && $(PYTHON) -m pip install -r requirements.txt"; \
		exit 1; \
	}
	@cd $(BACKEND_DIR) && $(PYTHON) -m pytest; \
	status=$$?; \
	if [ $$status -eq 5 ]; then \
		echo "No backend tests collected yet."; \
		exit 0; \
	fi; \
	exit $$status

test-frontend:
	cd $(FRONTEND_DIR) && npm run test:run

test-coverage: test-backend-coverage test-frontend-coverage

test-backend-coverage:
	@cd $(BACKEND_DIR) && $(PYTHON) -c "import pytest" >/dev/null 2>&1 || { \
		echo "pytest is not installed for $(PYTHON)."; \
		echo "Install backend deps with: cd $(BACKEND_DIR) && $(PYTHON) -m pip install -r requirements.txt"; \
		exit 1; \
	}
	@cd $(BACKEND_DIR) && $(PYTHON) -m pytest; \
	status=$$?; \
	if [ $$status -eq 5 ]; then \
		echo "No backend tests collected yet."; \
		exit 0; \
	fi; \
	exit $$status

test-frontend-coverage:
	cd $(FRONTEND_DIR) && npm run test:coverage

lint: lint-backend lint-frontend

lint-backend:
	cd $(BACKEND_DIR) && $(PYTHON) -m compileall -q .

lint-frontend:
	cd $(FRONTEND_DIR) && npm run lint

quality: lint test-coverage

test-service-order-audit:
	docker compose run --rm --build identity_service python -m pytest tests/unit/test_api_service_orders.py::test_service_order_actions_are_recorded_in_audit_logs -q --no-cov
