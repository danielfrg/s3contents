# Contributing

## Development environment

Create Python env

```
make env
conda activate word2vec
```

Install package for developmentt

```
make develop
```

## Iteration

Start minio (using docker) in one terminal:

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
c.S3ContentsManager.bucket = "notebooks"

c.NotebookApp.open_browser = False
c.NotebookApp.tornado_settings = {"debug": True}
```

Start Jupyter Notebook in another terminal:

```
jupyter notebook
```

## Tests

```
make test
```

Check linting and format

```
make check
make fmt
```
