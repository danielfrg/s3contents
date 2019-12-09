
[![Build Status](https://travis-ci.org/danielfrg/s3contents.svg?branch=master)](https://travis-ci.org/danielfrg/s3contents)
[![Coverage Status](https://coveralls.io/repos/github/danielfrg/s3contents/badge.svg?branch=master)](https://coveralls.io/github/danielfrg/s3contents?branch=master)

# S3Contents

A S3 and GCS backed ContentsManager implementation for Jupyter.

It aims to a be a transparent, drop-in replacement for Jupyter standard filesystem-backed storage system.
With this implementation of a Jupyter Contents Manager you can save all your notebooks, regular files, directories
structure directly to a S3/GCS bucket, this could be on AWS/GCP or a self hosted S3 API compatible like [minio](http://minio.io).

While there is some implementations of this functionality already available online ([s3nb](https://github.com/monetate/s3nb) or [s3drive](https://github.com/stitchfix/s3drive)) I wasn't able to make
them work in newer Jupyter Notebook installations. This aims to be a better tested one
by being highly based on the awesome [PGContents](https://github.com/quantopian/pgcontents).

## Prerequisites

Write access (valid credentials) to an S3/GCS bucket, this could be on AWS/GCP or a self hosted S3 like [minio](http://minio.io).

## Installation

```
$ pip install s3contents
```

## Jupyter config

Edit `~/.jupyter/jupyter_notebook_config.py` by filling the missing values:

### S3

```python
from s3contents import S3ContentsManager

c = get_config()

# Tell Jupyter to use S3ContentsManager for all storage.
c.NotebookApp.contents_manager_class = S3ContentsManager
c.S3ContentsManager.access_key_id = "<AWS Access Key ID / IAM Access Key ID>"
c.S3ContentsManager.secret_access_key = "<AWS Secret Access Key / IAM Secret Access Key>"
c.S3ContentsManager.session_token = "<AWS Session Token / IAM Session Token>"
c.S3ContentsManager.bucket = "<bucket-name>"

# Optional settings:
c.S3ContentsManager.prefix = "this/is/a/prefix"
c.S3ContentsManager.sse = "AES256"
c.S3ContentsManager.signature_version = "s3v4"
c.S3ContentsManager.init_s3_hook = init_function # See AWS key refresh
```

Example for `play.minio.io:9000`:

```python
from s3contents import S3ContentsManager

c = get_config()

# Tell Jupyter to use S3ContentsManager for all storage.
c.NotebookApp.contents_manager_class = S3ContentsManager
c.S3ContentsManager.access_key_id = "Q3AM3UQ867SPQQA43P2F"
c.S3ContentsManager.secret_access_key = "zuf+tfteSlswRu7BJ86wekitnifILbZam1KYY3TG"
c.S3ContentsManager.endpoint_url = "http://play.minio.io:9000"
c.S3ContentsManager.bucket = "s3contents-demo"
c.S3ContentsManager.prefix = "notebooks/test"
```

### GCP

Note that the file `~/.config/gcloud/application_default_credentials.json` assumes a posix system
when you did `gcloud init`

```python
from s3contents import GCSContentsManager

c = get_config(

c.NotebookApp.contents_manager_class = GCSContentsManager
c.GCSContentsManager.project = "<your-project>"
c.GCSContentsManager.token = "~/.config/gcloud/application_default_credentials.json"
c.GCSContentsManager.bucket = "<bucket-name>"
```

## AWS EC2 role auth setup

It is also possible to use IAM Role-based access to the S3 bucket from an Amazon EC2 instance; to do that,
just leave ```access_key_id``` and ```secret_access_key``` set to their default values (```None```), and ensure that
the EC2 instance has an IAM role which provides sufficient permissions for the bucket and the operations necessary.

## AWS key refresh

The optional `init_s3_hook` configuration can be used to enable AWS key rotation (described [here](https://dev.to/li_chastina/auto-refresh-aws-tokens-using-iam-role-and-boto3-2cjf) and [here](https://www.owenrumney.co.uk/2019/01/15/implementing-refreshingawscredentials-python/)) as follows:

```python
from s3contents import S3ContentsManager
from botocore.credentials import RefreshableCredentials
from botocore.session import get_session
import botocore
import boto3
from configparser import ConfigParser

def refresh_external_credentials():
    config = ConfigParser()
    config.read('/home/jovyan/.aws/credentials')
    return {
        "access_key": config['default']['aws_access_key_id'],
        "secret_key": config['default']['aws_secret_access_key'],
        "token": config['default']['aws_session_token'],
        "expiry_time": config['default']['aws_expiration']
    }

session_credentials = RefreshableCredentials.create_from_metadata(
        metadata = refresh_external_credentials(),
        refresh_using = refresh_external_credentials, 
        method = 'custom-refreshing-key-file-reader'
)

def make_key_refresh_boto3(this_s3contents_instance):
    refresh_session =  get_session() # from botocore.session
    refresh_session._credentials = session_credentials
    my_s3_session =  boto3.Session(botocore_session=refresh_session)
    this_s3contents_instance.boto3_session = my_s3_session

# Tell Jupyter to use S3ContentsManager for all storage.
c.NotebookApp.contents_manager_class = S3ContentsManager

c.S3ContentsManager.init_s3_hook = make_key_refresh_boto3
```

## Access local files

To access local file as well as remote files in S3 you can use [hybridcontents](https://github.com/viaduct-ai/hybridcontents).

First: 
```
pip install hybridcontents
```

And use a configuration like this:

```python
from s3contents import S3ContentsManager
from hybridcontents import HybridContentsManager
from IPython.html.services.contents.filemanager import FileContentsManager

c = get_config()

c.NotebookApp.contents_manager_class = HybridContentsManager

c.HybridContentsManager.manager_classes = {
    # Associate the root directory with an S3ContentsManager.
    # This manager will receive all requests that don"t fall under any of the
    # other managers.
    "": S3ContentsManager,
    # Associate /directory with a FileContentsManager.
    "local_directory": FileContentsManager,
}

c.HybridContentsManager.manager_kwargs = {
    # Args for root S3ContentsManager.
    "": {
        "access_key_id": "access-key",
        "secret_access_key": "secret-key",
        "endpoint_url": "http://localhost:9000",
        "bucket": "notebooks",
    },
    # Args for the FileContentsManager mapped to /directory
    "local_directory": {
        "root_dir": "/Users/drodriguez/Downloads",
    },
}
```

# Dockerfile

A Docker image is provided. The following environment variables are required:

- AWS_ACCESS_KEY_ID="<AWS Access Key ID / IAM Access Key ID>"
- AWS_SECRET_ACCESS_KEY="<AWS Secret Access Key / IAM Secret Access Key>"
- S3_BUCKET="<bucket-name>"
- JUPYTER_PASSWORD="<Jupyter password for accessing the notebooks>"

The following environment variables are optional:
- S3_PREFIX: "this/is/a/prefix". Default notebooks/

An [environment file](https://docs.docker.com/compose/env-file/) is a good way to store those variables. To start the script, run

```
docker run --rm --env-file .env -p 8888:8888 danielfrg/s3contents
```

