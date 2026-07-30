.PHONY: backend-setup frontend-setup dev docker-up docker-down test lint

BACKEND_DIR = backend
FRONTEND_DIR = frontend/web_app

backend-setup:
	cd $(BACKEND_DIR) && python3 -m venv venv && . venv/bin/activate && pip install -r requirements.txt

frontend-setup:
	cd $(FRONTEND_DIR) && npm ci --legacy-peer-deps

dev:
	@echo "Start backend and frontend in separate terminals:"
	@echo "  cd $(BACKEND_DIR) && . venv/bin/activate && uvicorn main:app --reload --host 0.0.0.0 --port 8000"
	@echo "  cd $(FRONTEND_DIR) && npm run dev"

docker-up:
	docker compose up --build

docker-down:
	docker compose down

test-backend:
	cd $(BACKEND_DIR) && . venv/bin/activate && python -m pytest -x -q --timeout=30

test-frontend:
	cd $(FRONTEND_DIR) && npm test

lint-backend:
	cd $(BACKEND_DIR) && . venv/bin/activate && ruff check .

lint-frontend:
	cd $(FRONTEND_DIR) && npm run lint

typecheck:
	cd $(FRONTEND_DIR) && npx tsc --noEmit --skipLibCheck
