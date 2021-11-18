SHELL := bash
.ONESHELL:
.SHELLFLAGS := -eu -o pipefail -c
.DELETE_ON_ERROR:
MAKEFLAGS += --warn-undefined-variables
MAKEFLAGS += --no-builtin-rules

PYTEST_K ?= ""
PYTEST_MARKERS ?= "not gcs"
S3DIR := $(CURDIR)/tmp-data


first: help


all: pkg  ## Build package


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
	pytest -k $(PYTEST_K) -m $(subst test-,,$@)


test-all:  ## Run all tests
	pytest -k $(PYTEST_K) -m $(PYTEST_MARKERS)


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


reset: clean  ## Reset Python
	rm -rf .venv


minio:  ## Run minio server
	mkdir -p ${S3DIR}/notebooks
	docker run -p 9000:9000 -p 9001:9001 -v ${S3DIR}:/data \
		-e MINIO_ROOT_USER=access-key -e MINIO_ROOT_PASSWORD=secret-key \
		minio/minio:RELEASE.2021-11-09T03-21-45Z server /data --console-address ":9001"

# from https://docs.min.io/minio/baremetal/installation/deploy-minio-distributed.html?ref=con#deploy-distributed-minio
minio-distributed:  ## Run minio server in distributed mode (necessary for versioning)
	echo "Once running, manually create a versioned 'notebooks' bucket in Minio-console"
# mkdir -p "${S3DIR}/mnt/disk1/notebooks"
# mkdir -p "${S3DIR}/mnt/disk2/notebooks"
# mkdir -p "${S3DIR}/mnt/disk3/notebooks"
# mkdir -p "${S3DIR}/mnt/disk4/notebooks"
	docker run \
		-p 9000:9000 -p 9001:9001 \
		-v "${s3DIR}/mnt/disk1:/data1" \
		-v "${s3DIR}/mnt/disk2:/data2" \
		-v "${s3DIR}/mnt/disk3:/data3" \
		-v "${s3DIR}/mnt/disk4:/data4" \
		-e MINIO_ROOT_USER=access-key -e MINIO_ROOT_PASSWORD=secret-key \
		minio/minio:RELEASE.2021-11-09T03-21-45Z server \
		"/data1" \
		"/data2" \
		"/data3" \
		"/data4" \
		--console-address ":9001"


help:  ## Show this help menu
	@grep -E '^[0-9a-zA-Z_-]+:.*?##.*$$' $(MAKEFILE_LIST) | sort \
		| awk 'BEGIN {FS = ":.*?##"; OFS="\t\t"}; {printf "\033[36m%-30s\033[0m %s\n", $$1, ($$2==""?"":$$2)}'
