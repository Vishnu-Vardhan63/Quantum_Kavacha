.PHONY: setup data train test dev-backend dev-frontend clean

setup:
	bash scripts/setup.sh

data:
	python scripts/generate_demo_data.py

train:
	python scripts/train_all.py

test:
	python -m pytest -v

dev-backend:
	python -m uvicorn backend.app.main:app --reload --port 8000

dev-frontend:
	cd frontend && npm run dev

clean:
	rm -rf data/sample/demo_transactions.csv model_artifacts/* cache/ .pytest_cache/
