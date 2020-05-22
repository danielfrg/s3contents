import pytest

from s3contents import S3ContentsManager
from s3contents.ipycompat import TestContentsManager
from s3contents.s3manager import _validate_bucket


@pytest.mark.minio
class S3ContentsManagerTestCase(TestContentsManager):
    def setUp(self):
        """
        This setup is a hardcoded to the use a minio server running in localhost
        """
        self.contents_manager = S3ContentsManager(
            access_key_id="access-key",
            secret_access_key="secret-key",
            endpoint_url="http://127.0.0.1:9000",
            bucket="notebooks",
            # endpoint_url="https://play.minio.io:9000",
            # bucket="s3contents-test2",
            signature_version="s3v4",
        )

        self.tearDown()

    def tearDown(self):
        for item in self.contents_manager.fs.ls(""):
            self.contents_manager.fs.rm(item)
        self.contents_manager.fs.init()

    # Overwrites from TestContentsManager

    def make_dir(self, api_path):
        self.contents_manager.new(
            model={"type": "directory"}, path=api_path,
        )


# This needs to be removed or else we'll run the main IPython tests as well.
del TestContentsManager


@pytest.mark.parametrize(
    "user_bucket", ("s3://BUCKET/some/key/", "BUCKET/some/", "BUCKET", "//BUCKET")
)
def test_bucket_validation(user_bucket, caplog):
    import logging

    logger = logging.getLogger()
    validated_bucket = _validate_bucket(user_bucket, logger)
    assert (
        validated_bucket == "BUCKET"
    ), "ContentsManager's bucket should be parsed properly"
