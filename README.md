<p align="center">
    <img src="https://raw.githubusercontent.com/danielfrg/s3contents/main/docs/logo.png" width="450px">
</p>

<p align="center">
    <a href="https://pypi.org/project/s3contents/">
        <img src="https://img.shields.io/pypi/v/mkdocs-jupyter.svg">
    </a>
    <a href="https://github.com/danielfrg/s3contents/actions/workflows/test.yml">
        <img src="https://github.com/danielfrg/s3contents/workflows/test/badge.svg">
    </a>
    <a href="https://codecov.io/gh/danielfrg/s3contents?branch=main">
        <img src="https://codecov.io/gh/danielfrg/s3contents/branch/main/graph/badge.svg">
    </a>
    <a href="http://github.com/danielfrg/s3contents/blob/main/LICENSE.txt">
        <img src="https://img.shields.io/:license-Apache%202-blue.svg">
    </a>
</p>

# S3Contents - Jupyter Notebooks in S3

A transparent, drop-in replacement for Jupyter standard filesystem-backed storage system.
With this implementation of a
[Jupyter Contents Manager](https://jupyter-server.readthedocs.io/en/latest/developers/contents.html)
you can save all your notebooks, files and directory structure directly to a
S3/GCS bucket on AWS/GCP or a self hosted S3 API compatible like [MinIO](http://minio.io).

## Installation

```shell
pip install s3contents
```

Install with GCS dependencies:

```shell
pip install s3contents[gcs]
```

## s3contents vs X

While there are some implementations of an S3 Jupyter Content Manager such as
[s3nb](https://github.com/monetate/s3nb) or [s3drive](https://github.com/stitchfix/s3drive)
s3contents is the only one tested against new versions of Jupyter.
It also supports more authentication methods and Google Cloud Storage.

This aims to be a fully tested implementation and it's based on [PGContents](https://github.com/quantopian/pgcontents).

## Configuration

Create a `jupyter_notebook_config.py` file in one of the
[Jupyter config directories](https://jupyter.readthedocs.io/en/latest/use/jupyter-directories.html#id1)
for example: `~/.jupyter/jupyter_notebook_config.py`.

**Jupyter Notebook Classic**: If you plan to use the Classic Jupyter Notebook
interface you need to change `ServerApp` to `NotebookApp` for all the examples on this page.

## AWS S3

```python
from s3contents import S3ContentsManager

c = get_config()

# Tell Jupyter to use S3ContentsManager
c.ServerApp.contents_manager_class = S3ContentsManager
c.S3ContentsManager.bucket = "<S3 bucket name>"

# Fix JupyterLab dialog issues
c.ServerApp.root_dir = ""
```

### Authentication

Additionally you can configure multiple authentication methods:

Access and secret keys:

```python
c.S3ContentsManager.access_key_id = "<AWS Access Key ID / IAM Access Key ID>"
c.S3ContentsManager.secret_access_key = "<AWS Secret Access Key / IAM Secret Access Key>"
```

Session token:

```python
c.S3ContentsManager.session_token = "<AWS Session Token / IAM Session Token>"
```

### AWS EC2 role auth setup

It also possible to use IAM Role-based access to the S3 bucket from an Amazon EC2 instance or AWS resource.

To do that just leave any authentication options (`access_key_id`, `secret_access_key`) to their default of `None`
and ensure that the EC2 instance has an IAM role which provides sufficient permissions (read and write) for the bucket.

### Optional settings

```python
# A prefix in the S3 buckets to use as the root of the Jupyter file system
c.S3ContentsManager.prefix = "this/is/a/prefix/on/the/s3/bucket"

# Server-Side Encryption
c.S3ContentsManager.sse = "AES256"

# Authentication signature version
c.S3ContentsManager.signature_version = "s3v4"

# See AWS key refresh
c.S3ContentsManager.init_s3_hook = init_function
```

### AWS key refresh

The optional `init_s3_hook` configuration can be used to enable AWS key rotation (described [here](https://dev.to/li_chastina/auto-refresh-aws-tokens-using-iam-role-and-boto3-2cjf) and [here](https://www.owenrumney.co.uk/2019/01/15/implementing-refreshingawscredentials-python/)) as follows:

```python
import boto3
import botocore
from botocore.credentials import RefreshableCredentials
from botocore.session import get_session
from configparser import ConfigParser

from s3contents import S3ContentsManager

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

# Tell Jupyter to use S3ContentsManager
c.ServerApp.contents_manager_class = S3ContentsManager

c.S3ContentsManager.init_s3_hook = make_key_refresh_boto3
```

### MinIO playground example

You can test this using the [`play.minio.io:9000`](https://play.minio.io:9000) playground:

Just be sure to create the bucket first.

```python
from s3contents import S3ContentsManager

c = get_config()

# Tell Jupyter to use S3ContentsManager
c.ServerApp.contents_manager_class = S3ContentsManager
c.S3ContentsManager.access_key_id = "Q3AM3UQ867SPQQA43P2F"
c.S3ContentsManager.secret_access_key = "zuf+tfteSlswRu7BJ86wekitnifILbZam1KYY3TG"
c.S3ContentsManager.endpoint_url = "https://play.minio.io:9000"
c.S3ContentsManager.bucket = "s3contents-demo"
c.S3ContentsManager.prefix = "notebooks/test"
```

## Access local files

To access local file as well as remote files in S3 you can use [hybridcontents](https://github.com/viaduct-ai/hybridcontents).

Install it:

```shell
pip install hybridcontents
```

Use a configuration similar to this:

```python
from s3contents import S3ContentsManager
from hybridcontents import HybridContentsManager
from notebook.services.contents.largefilemanager import LargeFileManager

c = get_config()

c.ServerApp.contents_manager_class = HybridContentsManager

c.HybridContentsManager.manager_classes = {
    # Associate the root directory with an S3ContentsManager.
    # This manager will receive all requests that don"t fall under any of the
    # other managers.
    "": S3ContentsManager,
    # Associate /local_directory with a LargeFileManager.
    "local_directory": LargeFileManager,
}

c.HybridContentsManager.manager_kwargs = {
    # Args for root S3ContentsManager.
    "": {
        "access_key_id": "<AWS Access Key ID / IAM Access Key ID>",
        "secret_access_key": "<AWS Secret Access Key / IAM Secret Access Key>",
        "bucket": "<S3 bucket name>",
    },
    # Args for the LargeFileManager mapped to /local_directory
    "local_directory": {
        "root_dir": "/Users/danielfrg/Downloads",
    },
}
```

## GCP - Google Cloud Storage

Install the extra dependencies with:

```shell
pip install s3contents[gcs]
```

```python
from s3contents.gcs import GCSContentsManager

c = get_config(

c.ServerApp.contents_manager_class = GCSContentsManager
c.GCSContentsManager.project = "<your-project>"
c.GCSContentsManager.token = "~/.config/gcloud/application_default_credentials.json"
c.GCSContentsManager.bucket = "<GCP bucket name>"
```

Note that the file `~/.config/gcloud/application_default_credentials.json` assumes
a POSIX system when you did `gcloud init`.

## Other configuration

### File Save Hooks

If you want to use pre/post file save hooks here are some examples.

A `pre_save_hook` is written in the exact same way as normal, operating on the
file in local storage before committing it to the object store.

```python
def scrub_output_pre_save(model, **kwargs):
    """
    Scrub output before saving notebooks
    """

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

A `post_save_hook` instead operates on the file in object storage,
because of this it is useful to use the file methods on the `contents_manager`
for data manipulation.
In addition, one must use the following function signature (unique to `s3contents`):

```python
def make_html_post_save(model, s3_path, contents_manager, **kwargs):
    """
    Convert notebooks to HTML after saving via nbconvert
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
