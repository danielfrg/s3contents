PWD := $(shell pwd)
S3DIR := ${PWD}/s3-data

minio:
	mkdir -p ${S3DIR}/notebooks; docker run -p 9000:9000 -v ${S3DIR}:/export -e MINIO_ACCESS_KEY=access-key -e MINIO_SECRET_KEY=secret-key minio/minio server /export
.PHONY: minio

test:
	py.test -s -vv s3contents/tests
.PHONY: test

build:
	python setup.py sdist
.PHONY: build

upload:
	twine upload dist/*.tar.gz
.PHONY: upload

env:
	conda env create
.PHONY: env

clean:
	rm -rf ${S3DIR}

#conda env remove -y -n s3-contents-dev
.PHONY: clean
