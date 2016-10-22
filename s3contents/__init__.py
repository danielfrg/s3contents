from ._version import get_versions
__version__ = get_versions()["version"]
del get_versions

from .s3manager import S3ContentsManager
