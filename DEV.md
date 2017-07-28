Create dev environment

```
make env

source activate s3-contents-dev
pip install -e .
```

Start minio

```
make minio
```

Edit `~/.jupyter/jupyter_notebook_config.py` by filling the missing values:

```python
from s3contents import S3ContentsManager

c = get_config()

# Tell Jupyter to use S3ContentsManager for storage
c.NotebookApp.contents_manager_class = S3ContentsManager
c.S3ContentsManager.endpoint_url = "http://localhost:9000"
c.S3ContentsManager.access_key_id = "key"
c.S3ContentsManager.secret_access_key = "secret"
c.S3ContentsManager.bucket_name = "notebooks"

c.NotebookApp.open_browser = False
c.NotebookApp.tornado_settings = {"debug": True}
```

Run `jupyter notebook`
