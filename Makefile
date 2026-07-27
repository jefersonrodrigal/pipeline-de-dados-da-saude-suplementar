.PHONY: install lint format type-check test test-unit test-integration coverage \
        migrate migrate-down db-security pipeline streamlit up down logs

PYTHON := .venv/Scripts/python.exe

install:
	$(PYTHON) -m pip install --upgrade pip
	$(PYTHON) -m pip install -r requirements.txt
	$(PYTHON) -m pip install -e ".[dev]"

lint:
	$(PYTHON) -m ruff check src app tests
	$(PYTHON) -m black --check src app tests

format:
	$(PYTHON) -m ruff check --fix src app tests
	$(PYTHON) -m black src app tests

type-check:
	$(PYTHON) -m mypy src app

test-unit:
	$(PYTHON) -m pytest tests/unit -v

test-integration:
	$(PYTHON) -m pytest tests/integration tests/streamlit -v -m integration

test:
	$(PYTHON) -m pytest -v

coverage:
	$(PYTHON) -m pytest --cov=src --cov=app --cov-report=term-missing --cov-report=html

migrate:
	$(PYTHON) -m alembic upgrade head

migrate-down:
	$(PYTHON) -m alembic downgrade -1

db-security:
	sqlcmd -S $${SQLSERVER_HOST:-localhost} -E -C -d $${SQLSERVER_DATABASE:-saude_suplementar} \
		-v EtlWriterPassword="$${SQLSERVER_PASSWORD}" \
		-v DashboardReaderPassword="$${SQLSERVER_READONLY_PASSWORD}" \
		-i sql/security/01_create_logins.sql
	sqlcmd -S $${SQLSERVER_HOST:-localhost} -E -C -d $${SQLSERVER_DATABASE:-saude_suplementar} \
		-i sql/security/02_grants.sql

pipeline:
	$(PYTHON) -m src.main --stage all

streamlit:
	$(PYTHON) -m streamlit run app/streamlit_app.py

up:
	docker compose up -d

down:
	docker compose down

logs:
	docker compose logs -f
