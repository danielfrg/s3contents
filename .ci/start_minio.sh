#!/usr/bin/env bash

go get -u github.com/minio/minio

export MINIO_ACCESS_KEY=access-key
export MINIO_SECRET_KEY=secret-key

mkdir -p ~/s3/notebooks
minio server ~/s3 > /tmp/minio.log 2>&1 &

ps aux
