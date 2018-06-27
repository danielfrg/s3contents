PWD := $(shell pwd)
S3DIR := ${PWD}/s3-data

.PHONY: minio
minio:  ## Run minio server
	mkdir -p ${S3DIR}/notebooks; docker run -p 9000:9000 -v ${S3DIR}:/export -e MINIO_ACCESS_KEY=access-key -e MINIO_SECRET_KEY=secret-key minio/minio server /export

.PHONY: test
test:  ## Run tests
	py.test -s -vv s3contents/tests

.PHONY: build
build:  ## BUild package
	python setup.py sdist

.PHONY: upload
upload:  ## Uplaod package to pypi
	twine upload dist/*.tar.gz

.PHONY: env
env:  ## Create dev environment
	conda env create

.PHONY: clean
clean:  ##
	rm -rf ${S3DIR} ; source deactivate; conda env remove -y -n s3-contents-dev

.PHONY: help
help:
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-30s\033[0m %s\n", $$1, $$2}'
