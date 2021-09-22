from .gcsmanager import GCSContentsManager  # noqa
from .s3manager import S3ContentsManager  # noqa

__version__ = "0.8.0-dev"


# We need this try/except here for tests to work
try:
    # This is needed for notebook 5.0, 5.1, 5.2(maybe)
    # https://github.com/jupyter/notebook/issues/2798
    import notebook.transutils  # noqa
except ImportError:
    # Will fail in notebook 4.X - its ok
    pass
