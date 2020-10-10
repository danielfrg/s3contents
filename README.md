# S3Contents

[![PyPI](https://badge.fury.io/py/s3contents.svg)](https://pypi.org/project/s3contents/)
[![Testing](https://github.com/danielfrg/s3contents/workflows/test/badge.svg)](http://github.com/danielfrg/s3contents/actions)
[![Coverage Status](https://codecov.io/gh/danielfrg/s3contents/branch/master/graph/badge.svg)](https://codecov.io/gh/danielfrg/s3contents?branch=master)
[![License](https://img.shields.io/:license-Apache%202-blue.svg)](http://github.com/danielfrg/s3contents/blob/master/LICENSE.txt)

An S3 and GCS backed ContentsManager implementation for Jupyter.

It aims to a be a transparent, drop-in replacement for Jupyter standard filesystem-backed storage system.
With this implementation of a Jupyter Contents Manager you can save all your notebooks, regular files, directories
structure directly to a S3/GCS bucket, this could be on AWS/GCP or a self hosted S3 API compatible like [minio](http://minio.io).

## Prerequisites

Write access (valid credentials) to an S3/GCS bucket, this could be on AWS/GCP or a self hosted S3 like [minio](http://minio.io).

## Installation

```
$ pip install s3contents
```

## Jupyter config

Edit `~/.jupyter/jupyter_notebook_config.py` based on the backend you want to
based on the examples below. Replace credentials as needed.

## AWS S3

```python
from s3contents import S3ContentsManager

c = get_config()

# Tell Jupyter to use S3ContentsManager for all storage.
c.NotebookApp.contents_manager_class = S3ContentsManager
c.S3ContentsManager.access_key_id = "{{ AWS Access Key ID / IAM Access Key ID }}"
c.S3ContentsManager.secret_access_key = "{{ AWS Secret Access Key / IAM Secret Access Key }}"
c.S3ContentsManager.session_token = "{{ AWS Session Token / IAM Session Token }}"
c.S3ContentsManager.bucket = "{{ S3 bucket name }}"

# Optional settings:
c.S3ContentsManager.prefix = "this/is/a/prefix/on/the/s3/bucket"
c.S3ContentsManager.sse = "AES256"
c.S3ContentsManager.signature_version = "s3v4"
c.S3ContentsManager.init_s3_hook = init_function  # See AWS key refresh
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

### AWS EC2 role auth setup

It also possible to use IAM Role-based access to the S3 bucket from an Amazon EC2 instance.

To do that just leave `access_key_id` and `secret_access_key` set to their default values (`None`),
and ensure that the EC2 instance has an IAM role which provides sufficient permissions for the bucket and the operations necessary.

### AWS key refresh

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

## GCP Cloud Storage

```python
from s3contents import GCSContentsManager

c = get_config(

c.NotebookApp.contents_manager_class = GCSContentsManager
c.GCSContentsManager.project = "{{ your-project }}"
c.GCSContentsManager.token = "~/.config/gcloud/application_default_credentials.json"
c.GCSContentsManager.bucket = "{{ GCP bucket name }}"
```

Note that the file `~/.config/gcloud/application_default_credentials.json` assumes a posix system
when you did `gcloud init`

## Access local files

To access local file as well as remote files in S3 you can use [hybridcontents](https://github.com/viaduct-ai/hybridcontents).

First install it:

```
pip install hybridcontents
```

Use a configuration similar to this:

```python
from s3contents import S3ContentsManager
from hybridcontents import HybridContentsManager
from notebook.services.contents.largefilemanager import LargeFileManager

c = get_config()

c.NotebookApp.contents_manager_class = HybridContentsManager

c.HybridContentsManager.manager_classes = {
    # Associate the root directory with an S3ContentsManager.
    # This manager will receive all requests that don"t fall under any of the
    # other managers.
    "": S3ContentsManager,
    # Associate /directory with a LargeFileManager.
    "local_directory": LargeFileManager,
}

c.HybridContentsManager.manager_kwargs = {
    # Args for root S3ContentsManager.
    "": {
        "access_key_id": "{{ AWS Access Key ID / IAM Access Key ID }}",
        "secret_access_key": "{{ AWS Secret Access Key / IAM Secret Access Key }}",
        "bucket": "{{ S3 bucket name }}",
    },
    # Args for the LargeFileManager mapped to /directory
    "local_directory": {
        "root_dir": "/Users/danielfrg/Downloads",
    },
}
```

## File Save Hooks

If you want to use pre/post file save hooks here are some examples.

A `pre_save_hook` is written in the exact same way as normal, operating on the file in local storage before commiting it to the object store.

```python
def scrub_output_pre_save(model, **kwargs):
    """scrub output before saving notebooks"""
    # only run on notebooks
    if model["type"] != "notebook":
        return
    # only run on nbformat v4
    if model["content"]["nbformat"] != 4:
        return

    for cell in model["content"]["cells"]:
        if cell["cell_type"] != "code":
            continue
        cell["outputs"] = []
        cell["execution_count"] = None

c.S3ContentsManager.pre_save_hook = scrub_output_pre_save
```

A `post_save_hook` instead operates on the file in object storage, because of this it is useful to use the file methods on the `contents_manager` for data manipulation. In addition, one must use the following function signature (unique to `s3contents`):

```python
def make_html_post_save(model, s3_path, contents_manager, **kwargs):
    """
    convert notebooks to HTML after saving via nbconvert
    """
    from nbconvert import HTMLExporter

    if model["type"] != "notebook":
        return

    content, _format = contents_manager.fs.read(s3_path, format="text")
    my_notebook = nbformat.reads(content, as_version=4)

    html_exporter = HTMLExporter()
    html_exporter.template_name = "classic"

    (body, resources) = html_exporter.from_notebook_node(my_notebook)

    base, ext = os.path.splitext(s3_path)
    contents_manager.fs.write(path=(base + ".html"), content=body, format=_format)

c.S3ContentsManager.post_save_hook = make_html_post_save
```

## Notes

While there are some implementations of this already:
([s3nb](https://github.com/monetate/s3nb) or [s3drive](https://github.com/stitchfix/s3drive)),
I wasn't able to make them work in newer versions of Jupyter Notebook.
This aims to be a more tested version and it's based on [PGContents](https://github.com/quantopian/pgcontents).
