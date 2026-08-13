.RECIPEPREFIX = >
PROJECT ?= fastapi-ai-scaffold
PY ?= python
PIP ?= pip

.PHONY: install dev test lint db-upgrade build up down

install:
> $(PIP) install -r requirements.txt -r requirements-dev.txt

dev:
> $(PY) main.py

test:
> $(PY) -m pytest tests -q

lint:
> $(PY) -m ruff check .

db-upgrade:
> $(PY) -m alembic upgrade head

build:
> docker build -t $(PROJECT):latest .

up:
> docker compose up -d

down:
> docker compose down
