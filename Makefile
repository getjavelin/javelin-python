.PHONY: all format lint test coverage build clean install install-wheel

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
	poetry run black .
	poetry run flake8 . --config=.flake8 --output-file=lint-report.json

test:
	poetry run pytest tests

build:
	poetry build

clean:
	rm -rf dist/
	rm -rf build/
	rm -rf *.egg-info/

install:
	poetry install

install-wheel:
	pip install dist/javelin_sdk-0.2.6-py3-none-any.whl --force-reinstall
