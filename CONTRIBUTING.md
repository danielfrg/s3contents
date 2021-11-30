# Contributing

## Development environment

The following requires poetry 1.2.0a2 or newer and these poetry `config.toml`
settings:

```toml
[virtualenvs]
in-project = true
```

Create Python env:

```shell
make env
source ./.venv/bin/activate
```

In case you want to use conda:

```shell
conda create --name s3contents
conda activate s3contents
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

# only log s3contents but not boto
import logging
log = logging.getLogger()
log.setLevel(logging.ERROR)
c.log_level = "DEBUG"
c.Application.log_level = "DEBUG"
```

Start Jupyter Notebook in another terminal:

```shell
jupyter lab --config ~/.jupyter/jupyter_notebook_config.py
```

## Applying changes

If you use conda:

```shell
conda activate s3contents && make env && jupyter lab --config ~/.jupyter/jupyter_notebook_config.py
```

or this faster one that will copy changes to the installation path:

```bash
rsync -r --exclude '.git' ./s3contents/ $(echo "$(pip show s3contents | grep Location: | cut -d' ' -f2)/s3contents/") && jupyter lab  --config ~/.jupyter/jupyter_notebook_config.py

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
