from s3contents.ipycompat import Unicode

from s3contents.s3_fs import S3FS
from s3contents.genericmanager import GenericContentsManager


class S3ContentsManager(GenericContentsManager):

    access_key_id = Unicode(
        help="S3/AWS access key ID", allow_none=True, default_value=None).tag(
            config=True, env="JPYNB_S3_ACCESS_KEY_ID")
    secret_access_key = Unicode(
        help="S3/AWS secret access key", allow_none=True, default_value=None).tag(
            config=True, env="JPYNB_S3_SECRET_ACCESS_KEY")

    endpoint_url = Unicode(
        "https://s3.amazonaws.com", help="S3 endpoint URL").tag(
            config=True, env="JPYNB_S3_ENDPOINT_URL")
    region_name = Unicode(
        "us-east-1", help="Region name").tag(
            config=True, env="JPYNB_S3_REGION_NAME")
    bucket = Unicode(
        "notebooks", help="Bucket name to store notebooks").tag(
            config=True, env="JPYNB_S3_BUCKET")
    prefix = Unicode("", help="Prefix path inside the specified bucket").tag(config=True)
    signature_version = Unicode(help="").tag(config=True)
    delimiter = Unicode("/", help="Path delimiter").tag(config=True)

    def __init__(self, *args, **kwargs):
        super(S3ContentsManager, self).__init__(*args, **kwargs)

        self._fs = S3FS(
            log=self.log,
            access_key_id=self.access_key_id,
            secret_access_key=self.secret_access_key,
            endpoint_url=self.endpoint_url,
            region_name=self.region_name,
            bucket=self.bucket,
            prefix=self.prefix,
            signature_version=self.signature_version,
            delimiter=self.delimiter)
