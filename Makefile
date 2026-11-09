.PHONY: install dev api web test eval seed demo lint

install:
	python -m pip install -e ".[dev]"
	cd apps/web && npm install

dev:
	uvicorn apps.api.main:app --reload --port 8000

web:
	cd apps/web && npm run dev

test:
	pytest -q

lint:
	ruff check agent rag mcp_servers apps/api worker tests evals

eval:
	python -m evals.runners.run_all_evals

seed:
	python scripts/generate_data.py

demo:
	cd apps/web && npm run build
	uvicorn apps.api.main:app --port 8000
