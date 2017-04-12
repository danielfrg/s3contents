
minio:
	docker run -p 9000:9000 -e MINIO_ACCESS_KEY=Q3AM3UQ867SPQQA43P2F -e MINIO_SECRET_KEY=zuf+tfteSlswRu7BJ86wekitnifILbZam1KYY3TG minio/minio server /export

test:
	py.test -s -vv s3contents/tests

build:
	python setup.py sdist

upload:
	twine upload dist/*.tar.gz

.PHONY: minio test build upload
