#!/usr/bin/env bash

# go get -u github.com/minio/minio
curl https://dl.minio.io/server/minio/release/linux-amd64/archive/minio.RELEASE.2018-06-29T02-11-29Z -o minio
chmod +x minio

export MINIO_ACCESS_KEY=access-key
export MINIO_SECRET_KEY=secret-key

mkdir -p ~/s3/notebooks
./minio version
./minio server ~/s3 > /tmp/minio.log 2>&1 &
