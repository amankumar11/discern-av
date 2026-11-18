.PHONY: check config doctor format lint test tracking

check: lint test

lint:
	ruff check .
	ruff format --check .

format:
	ruff check --fix .
	ruff format .

test:
	pytest

config:
	python -m discern.cli config

doctor:
	python -m discern.cli doctor

tracking:
	python -m discern.cli init-tracking

