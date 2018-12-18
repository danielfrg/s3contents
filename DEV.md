Create dev environment

```
make env
conda activate s3contents-dev
make deps
```

Start minio

```
make minio
```

Edit `~/.jupyter/jupyter_notebook_config.py`:

```python
c = get_config()

# Tell Jupyter to use S3ContentsManager for storage
from s3contents import S3ContentsManager
c.NotebookApp.contents_manager_class = S3ContentsManager
c.S3ContentsManager.endpoint_url = "http://localhost:9000"
c.S3ContentsManager.access_key_id = "access-key"
c.S3ContentsManager.secret_access_key = "secret-key"
c.S3ContentsManager.bucket_name = "notebooks"

# from s3contents import GCSContentsManager
# c.NotebookApp.contents_manager_class = GCSContentsManager
# c.GCSContentsManager.project = "continuum-compute"
# c.GCSContentsManager.token = "~/.config/gcloud/application_default_credentials.json"
# c.GCSContentsManager.bucket = "gcsfs-test"
# c.GCSContentsManager.prefix = "this/is/the/prefix"

c.NotebookApp.open_browser = False
c.NotebookApp.tornado_settings = {"debug": True}
```

Run `jupyter notebook` in the `s3-contents-dev`
