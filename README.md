
[![Build Status](https://travis-ci.org/danielfrg/s3contents.svg?branch=master)](https://travis-ci.org/danielfrg/s3contents)
[![Coverage Status](https://coveralls.io/repos/github/danielfrg/s3contents/badge.svg?branch=master)](https://coveralls.io/github/danielfrg/s3contents?branch=master)

# S3Contents

A S3 backed ContentsManager implementation for Jupyter.

It aims to a be a transparent, drop-in replacement for Jupyter standard filesystem-backed storage system.
With this implementation of a Jupyter Contents Manager you can save all your notebooks, regular files, directories
structure directly to a S3 bucket, this could be on AWS or a self hosted S3 API compatible like [minio](http://minio.io).

While there is some implementations of this functionality already available online [2] I wasn't able to make
them work in newer Jupyter Notebook installations. This aims to be a better tested one
by being highly based on the nice [PGContents](https://github.com/quantopian/pgcontents)[1].

## Prerequisites

Write access (valid credentials) to an S3 bucket, this could be on AWS or a self hosted S3 like [minio](http://minio.io).

## Installation

```
$ pip install s3contents
```

## Jupyter config

Edit `~/.jupyter/jupyter_notebook_config.py` by filling the missing values:

```python
from s3contents import S3ContentsManager

c = get_config()

# Tell Jupyter to use S3ContentsManager for all storage.
c.NotebookApp.contents_manager_class = S3ContentsManager
c.S3ContentsManager.access_key_id = <AWS Access Key ID / IAM Access Key ID>
c.S3ContentsManager.secret_access_key = <AWS Secret Access Key / IAM Secret Access Key>
c.S3ContentsManager.bucket_name = "<>"
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
c.S3ContentsManager.bucket_name = "s3contents-demo"
c.S3ContentsManager.prefix = "notebooks/test"
```

## AWS IAM

It is also possible to use IAM Role-based access to the S3 bucket from an Amazon EC2 instance; to do that,
just leave ```access_key_id``` and ```secret_access_key``` set to their default values (```None```), and ensure that
the EC2 instance has an IAM role which provides sufficient permissions for the bucket and the operations necessary.


## See also

1. [PGContents](https://github.com/quantopian/pgcontents)
2. [s3nb](https://github.com/monetate/s3nb) or [s3drive](https://github.com/stitchfix/s3drive)
