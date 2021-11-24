import sys

try:
    import gcsfs
except ImportError:
    print(
        """ERROR: Trying to use GCS Content Manager but dependencies are not installed.
Install them with: pip install s3contents[gcs]"""
    )

from .gcsmanager import GCSContentsManager  # noqa
