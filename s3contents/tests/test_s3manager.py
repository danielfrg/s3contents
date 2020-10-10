import os
import time

import pytest

from s3contents import S3ContentsManager
from s3contents.ipycompat import TestContentsManager
from s3contents.s3manager import _validate_bucket
from s3contents.tests.hooks import make_html_post_save, scrub_output_pre_save


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

    def test_save_hooks(self):
        """
        Extends TestContentsManager.save
        """

        self.contents_manager.pre_save_hook = scrub_output_pre_save
        self.contents_manager.post_save_hook = make_html_post_save

        cm = self.contents_manager
        model = cm.new_untitled(type="notebook")
        path = model["path"]

        full_model = cm.get(path)
        nb = full_model["content"]
        nb["metadata"]["counter"] = int(1e6 * time.time())
        self.add_code_cell(nb)

        cm.save(full_model, path)

        # test pre_save_hook
        loaded_model = cm.get(path)
        for cell in loaded_model["content"]["cells"]:
            assert cell["outputs"] == []

        # test post_save_hook
        html_file = os.path.splitext(path)[0] + ".html"
        html, _type = cm.fs.read(html_file, "text")

        assert cm.fs.isfile(html_file)
        assert "<!DOCTYPE html>" in html

        self.contents_manager.pre_save_hook = None
        self.contents_manager.post_save_hook = None


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


def test_bucket_validation_empty_bucket_name(caplog):
    import logging

    logger = logging.getLogger()
    with pytest.raises(ValueError):
        _validate_bucket("", logger)
