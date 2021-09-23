SHELL := bash
.ONESHELL:
.SHELLFLAGS := -eu -o pipefail -c
.DELETE_ON_ERROR:
MAKEFLAGS += --warn-undefined-variables
MAKEFLAGS += --no-builtin-rules

TEST_FILTER ?= ""
TEST_MARKERS ?= "not minio and not gcs"
S3DIR := $(CURDIR)/tmp-data


first: help


# ------------------------------------------------------------------------------
# Build

env:  ## Create Python env
	poetry install


build:  ## Build package
	poetry build


upload-pypi:  ## Upload package to PyPI
	twine upload dist/*.tar.gz


upload-test:  ## Upload package to test PyPI
	twine upload --repository test dist/*.tar.gz


# ------------------------------------------------------------------------------
# Testing

check:  ## Check linting
	isort --check-only --diff .
	black --check --diff .
	flake8


fmt:  ## Format source
	isort .
	black .


test:  ## Run tests
	pytest -k $(TEST_FILTER) -m $(TEST_MARKERS)


test-all:  ## Run all tests
	pytest -k $(TEST_FILTER) -m "not gcs"


report:  ## Generate coverage reports
	coverage xml
	coverage html


minio:  ## Run minio server
	mkdir -p ${S3DIR}/notebooks
	docker run -p 9000:9000 -p 9001:9001 -v ${S3DIR}:/data -e MINIO_ROOT_USER=access-key -e MINIO_ROOT_PASSWORD=secret-key minio/minio:RELEASE.2021-08-05T22-01-19Z server /data --console-address ":9001"


# ------------------------------------------------------------------------------
# Other

clean:  ## Clean build files
	rm -rf build dist site htmlcov .pytest_cache .eggs
	rm -f .coverage coverage.xml s3contents/_generated_version.py
	find . -type f -name '*.py[co]' -delete
	find . -type d -name __pycache__ -exec rm -rf {} +
	find . -type d -name .ipynb_checkpoints -exec rm -rf {} +
	rm -rf ${S3DIR} foo


cleanall: clean  ## Clean everything
	rm -rf *.egg-info


help:  ## Show this help menu
	@grep -E '^[0-9a-zA-Z_-]+:.*?##.*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?##"; OFS="\t\t"}; {printf "\033[36m%-30s\033[0m %s\n", $$1, ($$2==""?"":$$2)}'
