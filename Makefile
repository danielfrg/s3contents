SHELL := bash
.ONESHELL:
.SHELLFLAGS := -eu -o pipefail -c
.DELETE_ON_ERROR:
MAKEFLAGS += --warn-undefined-variables
MAKEFLAGS += --no-builtin-rules

PWD := $(shell pwd)
TEST_FILTER ?= ""

S3DIR := ${PWD}/tmp-data


first: help

.PHONY: clean
clean:  ## Clean build files
	@rm -rf build dist site htmlcov .pytest_cache .eggs
	@rm -f .coverage coverage.xml s3contents/_generated_version.py
	@find . -type f -name '*.py[co]' -delete
	@find . -type d -name __pycache__ -exec rm -rf {} +
	@find . -type d -name .ipynb_checkpoints -exec rm -rf {} +
	@rm -rf ${S3DIR} foo


.PHONY: cleanall
cleanall: clean  ## Clean everything
	@rm -rf *.egg-info


.PHONY: help
help:  ## Show this help menu
	@grep -E '^[0-9a-zA-Z_-]+:.*?##.*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?##"; OFS="\t\t"}; {printf "\033[36m%-30s\033[0m %s\n", $$1, ($$2==""?"":$$2)}'


# ------------------------------------------------------------------------------
# Package build, test and docs

.PHONY: env  ## Create dev environment
env:
	conda env create


.PHONY: develop
develop:  ## Install package for development
	python -m pip install --no-build-isolation -e .


.PHONY: build
build: package  ## Build everything


.PHONY: package
package:  ## Build Python package (sdist)
	python setup.py sdist


.PHONY: check
check:  ## Check linting
	@flake8
	@isort --check-only --diff --recursive --project s3contents --section-default THIRDPARTY s3contents .
	@black --check s3contents .


.PHONY: fmt
fmt:  ## Format source
	@isort --recursive --project s3contents --section-default THIRDPARTY s3contents .
	@black s3contents .


.PHONY: upload-pypi
upload-pypi:  ## Upload package to PyPI
	twine upload dist/*.tar.gz


.PHONY: upload-test
upload-test:  ## Upload package to test PyPI
	twine upload --repository testpypi dist/*.tar.gz


.PHONY: test
test:  ## Run tests
	pytest -s -vv s3contents/tests -k $(TEST_FILTER)


# ------------------------------------------------------------------------------
# Project specific

.PHONY: minio
minio:  ## Run minio server
	@mkdir -p ${S3DIR}/notebooks
	docker run -p 9000:9000 -v ${S3DIR}:/data -e MINIO_ACCESS_KEY=access-key -e MINIO_SECRET_KEY=secret-key minio/minio:RELEASE.2018-06-29T02-11-29Z server /data
