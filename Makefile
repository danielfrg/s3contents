PWD := $(shell pwd)
S3DIR := ${PWD}/s3-data

all: tests

.PHONY: minio
minio:  ## Run minio server
	mkdir -p ${S3DIR}/notebooks; docker run -p 9000:9000 -v ${S3DIR}:/export -e MINIO_ACCESS_KEY=access-key -e MINIO_SECRET_KEY=secret-key minio/minio:RELEASE.2018-06-29T02-11-29Z server /export

.PHONY: tests
tests:  ## Run tests
	py.test -s -vv s3contents/tests

.PHONY: build
build:  ## Build package
	python setup.py sdist

.PHONY: upload
upload:  ## Upload package to pypi
	twine upload dist/*.tar.gz

.PHONY: env
env:  ## Create dev environment
	@conda create -y -n s3contents-dev python=3.7

.PHONY: deps
deps:  ## Install dev dependencies
	@pip install pytest pytest-cov python-coveralls nose mock twine
	@pip install -r requirements.txt
	@pip install -e .

.PHONY: clean
clean:  ##
	rm -rf ${S3DIR} ; source deactivate; conda env remove -y -n s3-contents-dev

PHONY: help
help:
	@grep -E '^[a-zA-Z_-]+:.*?##.*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?##"; OFS="\t\t"}; {printf "\033[36m%-30s\033[0m %s\n", $$1, ($$2==""?"":$$2)}'
