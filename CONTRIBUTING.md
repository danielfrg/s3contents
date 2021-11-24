# Contributing

## Development environment

Create Python env

```shell
make env
source ./.venv/bin/activate
```

## Iteration

Start minio (using docker) in one terminal:

```shell
make minio
```

Edit `~/.jupyter/jupyter_notebook_config.py`:

```python
c = get_config()

# Tell Jupyter to use S3ContentsManager for storage
from s3contents import S3ContentsManager
c.ServerApp.contents_manager_class = S3ContentsManager
c.S3ContentsManager.endpoint_url = "http://localhost:9000"
c.S3ContentsManager.access_key_id = "access-key"
c.S3ContentsManager.secret_access_key = "secret-key"
c.S3ContentsManager.bucket = "notebooks"

c.ServerApp.open_browser = False
c.ServerApp.tornado_settings = {"debug": True}
```

Start Jupyter Notebook in another terminal:

```shell
jupyter lab
```

## Tests

```shell
make test
```

Check linting and format

```shell
make check
make fmt
```
