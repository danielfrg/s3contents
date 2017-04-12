
minio:
	docker run -p 9000:9000 -e MINIO_ACCESS_KEY=Q3AM3UQ867SPQQA43P2F -e MINIO_SECRET_KEY=zuf+tfteSlswRu7BJ86wekitnifILbZam1KYY3TG minio/minio server /export

.PHONY: minio
