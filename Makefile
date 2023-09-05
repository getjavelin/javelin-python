.PHONY: all format lint test tests

all: help

coverage:
	poetry run pytest --cov \
		--cov-config=.coveragerc \
		--cov-report xml \
		--cov-report term-missing:skip-covered

format:
	poetry run black .
	poetry run ruff --select I --fix .

lint:
	poetry run mypy --exclude tests javelin_sdk/
	poetry run black . --check
	poetry run ruff javelin_sdk/

test:
	poetry run pytest tests
