SHELL := bash
.ONESHELL:
.SHELLFLAGS := -eu -o pipefail -c
.DELETE_ON_ERROR:
MAKEFLAGS += --warn-undefined-variables
MAKEFLAGS += --no-builtin-rules

PYTEST_K ?= ""
PYTEST_MARKERS ?= ""
S3DIR := $(CURDIR)/tmp-data


first: help


all: pkg  ## Build package


# ------------------------------------------------------------------------------
# Python

env:  ## Create Python env
	poetry install --with dev --with test


pkg:  ## Build package
	poetry build


check:  ## Check linting
	isort --check-only --diff .
	black --check --diff .
	flake8


fmt:  ## Format source
	isort .
	black .


test-%:  ## Run tests
	pytest -k "$(PYTEST_K)" -m $(subst test-,,$@)


test-all:  ## Run all tests
	pytest -k "$(TEST_FILTER)" -m "not gcs"


report:  ## Generate coverage reports
	coverage xml
	coverage html


upload-pypi:  ## Upload package to PyPI
	twine upload dist/*.tar.gz


clean:  ## Clean Python build files
	rm -rf .eggs .pytest_cache dist htmlcov test-results
	rm -f .coverage coverage.xml
	find . -type f -name '*.py[co]' -delete
	find . -type d -name __pycache__ -exec rm -rf {} +
	find . -type d -name .ipynb_checkpoints -exec rm -rf {} +


reset: clean  ## Reset
	rm -rf .venv


minio:  ## Run minio server
	mkdir -p ${S3DIR}/notebooks
	docker run -p 9000:9000 -p 9001:9001 -v ${S3DIR}:/data -e MINIO_ROOT_USER=access-key -e MINIO_ROOT_PASSWORD=secret-key minio/minio:RELEASE.2021-08-05T22-01-19Z server /data --console-address ":9001"


# ------------------------------------------------------------------------------
# Other

help:  ## Show this help menu
	@grep -E '^[0-9a-zA-Z_-]+:.*?##.*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?##"; OFS="\t\t"}; {printf "\033[36m%-30s\033[0m %s\n", $$1, ($$2==""?"":$$2)}'
