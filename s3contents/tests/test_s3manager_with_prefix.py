import pytest

from s3contents import S3ContentsManager
from s3contents.ipycompat import TestContentsManager


@pytest.mark.minio
class S3ContentsManagerTestCase_prefix(TestContentsManager):
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
            # bucket="s3contents-test",
            prefix="this/is/the/prefix",
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
