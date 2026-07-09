.PHONY: install dev test
install:
	pip install -r requirements.txt
dev:
	uvicorn app.main:app --reload --port 8000
worker:
	celery -A app.workers.celery_app.celery_app worker --loglevel=info
test:
	pytest -q
