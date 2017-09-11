#!/usr/bin/env bash

# go get -u github.com/minio/minio
wget https://dl.minio.io/server/minio/release/linux-amd64/minio
chmod +x minio

export MINIO_ACCESS_KEY=access-key
export MINIO_SECRET_KEY=secret-key

mkdir -p ~/s3/notebooks
./minio server ~/s3 # > /tmp/minio.log 2>&1 &

ps auxww
