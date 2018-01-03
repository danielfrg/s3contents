import tempfile, shutil

from s3contents.ipycompat import TestContentsManager

from s3contents import StorefactContentsManager


class StorefactContentsManagerTestCase(TestContentsManager):

    def setUp(self):
        self.tempdir = tempfile.mkdtemp()
        self.contents_manager = StorefactContentsManager(
            store_url="fs://" + self.tempdir)

    def tearDown(self):
        try:
            for item in self.contents_manager.fs.ls(""):

                self.contents_manager.fs.rm(item)
            self.contents_manager.fs.init()
        finally:
            shutil.rmtree(self.tempdir)

    # Overwrites from TestContentsManager
    def make_dir(self, api_path):
        self.contents_manager.new(
            model={"type": "directory"},
            path=api_path,)


# This needs to be removed or else we'll run the main IPython tests as well.
del TestContentsManager
