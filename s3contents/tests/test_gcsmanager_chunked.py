import time

import pytest

from s3contents import GCSContentsManager
from s3contents.chunks import content_chunks
from s3contents.ipycompat import TestLargeFileManager


@pytest.mark.gcs
class GcsContentsManagerLargeFileTestCase(TestLargeFileManager):
    def setUp(self):
        """
        This setup is a hardcoded to run on my laptop and GCP account :)
        """
        self.contents_manager = GCSContentsManager(
            project="continuum-compute",
            token="~/.config/gcloud/application_default_credentials.json",
            bucket="gcsfs-test",
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

    def test_save(self):
        current_value = content_chunks.get()
        current_value["stale_file.txt"] = {
            "started_at": time.time() - 4000,
            "chunks": [],
        }

        super().test_save()

        self.assertNotIn("stale_file.txt", current_value)


# This needs to be removed or else we'll run the main IPython tests as well.
del TestLargeFileManager
