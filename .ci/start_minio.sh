#!/usr/bin/env bash

go get -u github.com/minio/minio

export MINIO_ACCESS_KEY=Q3AM3UQ867SPQQA43P2F
export MINIO_SECRET_KEY=zuf+tfteSlswRu7BJ86wekitnifILbZam1KYY3TG

mkdir -p ~/s3/notebooks
minio server ~/s3 > /tmp/minio.log 2>&1 &
