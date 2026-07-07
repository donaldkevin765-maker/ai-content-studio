.PHONY: install run dev worker beat flower docker-up docker-down lint test clean migrate

install:
	pip install -r requirements.txt

run:
	uvicorn app.main:app --host 0.0.0.0 --port 8000

dev:
	uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload

worker:
	celery -A app.workers.celery_app worker --loglevel=info

beat:
	celery -A app.workers.celery_app beat --loglevel=info

flower:
	celery -A app.workers.celery_app flower --port=5555

docker-up:
	docker compose up --build -d

docker-down:
	docker compose down

lint:
	ruff check app/

test:
	pytest tests/ -v

migrate:
	alembic upgrade head

migrate-create:
	alembic revision --autogenerate -m "$(msg)"

clean:
	find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name "*.pyc" -delete
	rm -rf .pytest_cache *.egg-info data/test.db
