from ._version import get_versions
__version__ = get_versions()["version"]
del get_versions

# We need this try/except here for tests to work
try:
    # This is needed for notebook 5.0, 5.1, 5.2(maybe)
    # https://github.com/jupyter/notebook/issues/2798
    import notebook.transutils
except:
    # Will fail in notebook 4.X - its ok
    pass

from .s3manager import S3ContentsManager
from .gcsmanager import GCSContentsManager
