from s3contents.ipycompat import TestContentsManager

from s3contents import S3ContentsManager


class S3ContentsManagerTestCase(TestContentsManager):

    def setUp(self):
        """
        This setup is a hardcoded to the use a little minio server that run on travis CI or play.minio.io:9000
        """
        self.contents_manager = S3ContentsManager(
            access_key_id="Q3AM3UQ867SPQQA43P2F",
            secret_access_key="zuf+tfteSlswRu7BJ86wekitnifILbZam1KYY3TG",
            bucket_name="notebooks",
            endpoint_url="http://localhost:9000",
            # bucket_name="s3contents-test",
            # endpoint_url="https://play.minio.io:9000",
            signature_version='s3v4'
        )

    def tearDown(self):
        bucket = self.contents_manager.s3fs.bucket

        objects_to_delete = []
        for obj in bucket.objects.filter(Prefix=""):
            objects_to_delete.append({"Key": obj.key})

        bucket.delete_objects(
            Delete={
                "Objects": objects_to_delete
            }
        )

    # Overwrites from TestContentsManager

    def make_dir(self, api_path):
        self.contents_manager.new(
            model={"type": "directory"},
            path=api_path,
        )

# This needs to be removed or else we'll run the main IPython tests as well.
del TestContentsManager
