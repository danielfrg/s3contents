# S3Contents

A S3 backed ContentsManager implementation for Jupyter.

It aims to a be a transparent, drop-in replacement for Jupyter standard filesystem-backed storage system.
With this implementation of a Jupyter Contents Manager you can save all your notebooks, regular file, directories
structure directly to an S3 bucket, this could be on AWS or a self hosted S3 like [minio](http://minio.io).

While there is some implementations of this functionality already available online [2] I wasn't able to make
them work in a newer Jupyter installation. This aims to be a better tested one
by being highly based on the nice [PGContents](https://github.com/quantopian/pgcontents).

## Getting Started

### Prerequisites

Write access (valid credentials) to an S3 bucket, this could be on AWS or a self hosted S3 like [minio](http://minio.io)

### Installation

```
$ pip install s3contents
```

### Jupyter config

Configure Jupyter to use s3contents as its storage backend.

Edit `~/.jupyter/jupyter_notebook_config.py` by filling the missing values:

```python
from s3contents import S3ContentsManager

c = get_config()

# Tell Jupyter to use S3ContentsManager for all storage.
c.NotebookApp.contents_manager_class = S3ContentsManager
c.S3ContentsManager.access_key_id = ""
c.S3ContentsManager.secret_access_key = ""
c.S3ContentsManager.bucket_name = ""
```

Example for `play.minio.io:9000`:

```python
from s3contents import S3ContentsManager

c = get_config()

# Tell Jupyter to use S3ContentsManager for all storage.
c.NotebookApp.contents_manager_class = S3ContentsManager
c.S3ContentsManager.access_key_id = "Q3AM3UQ867SPQQA43P2F"
c.S3ContentsManager.secret_access_key = "zuf+tfteSlswRu7BJ86wekitnifILbZam1KYY3TG"
c.S3ContentsManager.bucket_name = "danielfrg"
c.S3ContentsManager.endpoint_url = "http://localhost:9000"
```

## See also

1. [PGContents](https://github.com/quantopian/pgcontents)
2. [s3drive](https://github.com/stitchfix/s3drive)
