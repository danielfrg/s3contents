import sys

try:
    import gcsfs
except ImportError:
    print(
        """ERROR: Trying to use GCS but dependencies are not installed.
Install them with: pip install s3contents[gcs]"""
    )
    sys.exit(1)


from .gcsmanager import GCSContentsManager  # noqa
