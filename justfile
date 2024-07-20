s3dir := "./tmp-data"

default:
  just --list

build:
  rye build

check:
  rye run isort . --check-only --diff
  rye run black . --check
  rye run ruff check s3contents
  rye run flake8

fmt:
  rye run isort .
  rye run ruff format

test FILTER="":
  rye run pytest -k "{{FILTER}}"

report:
  coverage xml
  coverage html

publish:
  rye publish

# ------------------------------------------------------------------------------
# Minio

minio:
  mkdir -p $PWD/notebooks
  docker run -p 9000:9000 -p 9001:9001 -v $PWD:/data -e MINIO_ROOT_USER=access-key -e MINIO_ROOT_PASSWORD=secret-key minio/minio:RELEASE.2021-11-09T03-21-45Z server /data --console-address ":9001"

# From https://docs.min.io/minio/baremetal/installation/deploy-minio-distributed.html?ref=con#deploy-distributed-minio
# Run minio server in distributed mode (necessary for versioning)
minio-distributed:
  echo "Once running, manually create a versioned 'notebooks' bucket in Minio-console"
  mkdir -p "$PWD/mnt/disk1/notebooks"
  mkdir -p "$PWD/mnt/disk2/notebooks"
  mkdir -p "$PWD/mnt/disk3/notebooks"
  mkdir -p "$PWD/mnt/disk4/notebooks"
  docker run -p 9000:9000 -p 9001:9001 \
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
