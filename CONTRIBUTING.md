# Contributing

## Development environment

The following requires poetry 1.2.0a2 or newer.

Create Python env

```
make env
conda create --name s3contents
conda activate s3contents
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

# only log s3contents but not boto
import logging
log = logging.getLogger()
log.setLevel(logging.ERROR)
c.log_level = "DEBUG"
c.Application.log_level = "DEBUG"
```

Start Jupyter Notebook in another terminal:

```
jupyter notebook
```

After you have made some changes, recompile with:

```
conda activate s3contents && make env && jupyter notebook
```

or use this faster command to copy changes to s3contents installation path:

```bash
rsync -r --exclude '.git' ./s3contents/ $(echo "$(pip show s3contents | grep Location: | cut -d' ' -f2)/s3contents/") && jupyter notebook

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
