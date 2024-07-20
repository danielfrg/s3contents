# Contributing

Requirements:

- [Rye](https://rye.astral.sh/)

## Create Python env:

```shell
rye sync
```

## Iteration

Configure Jupyter:

- Edit `~/.jupyter/jupyter_notebook_config.py`:

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

# only log s3contents but not boto
import logging
log = logging.getLogger()
log.setLevel(logging.ERROR)
c.log_level = "DEBUG"
c.Application.log_level = "DEBUG"
```

Start Minio (using docker) in one terminal:

```shell
just minio
```

Start Jupyter Notebook in another terminal:

```shell
jupyter lab --config ~/.jupyter/jupyter_notebook_config.py
```

## Tests

```shell
just test
```

Check linting and format

```shell
just check
just fmt
```
