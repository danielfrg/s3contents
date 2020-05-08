import pytest

from s3contents import GCSContentsManager
from s3contents.ipycompat import TestContentsManager


@pytest.mark.gcs
class GCSContentsManagerTestCase_prefix(TestContentsManager):
    def setUp(self):
        """
        This setup is a hardcoded to run on my laptop and GCP account :)
        """
        self.contents_manager = GCSContentsManager(
            project="continuum-compute",
            token="~/.config/gcloud/application_default_credentials.json",
            bucket="gcsfs-test",
            prefix="this/is/the/prefix",
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
