import json

from s3contents.ipycompat import Unicode
from traitlets import Any
from s3contents.s3_fs import S3FS
from s3contents.genericmanager import from_dict, GenericContentsManager


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
    sse = Unicode(help="Type of server-side encryption to use").tag(config=True)

    kms_key_id = Unicode(help="KMS ID to use to encrypt workbooks").tag(config=True)

    session_token = Unicode(
        help="S3/AWS session token",
        allow_none=True,
        default_value=None
    ).tag(config=True, env="JPYNB_S3_SESSION_TOKEN")

    boto3_session = Any(help="Place to store custom boto3 session (passed to S3_FS) - could be set by init_s3_hook")
    init_s3_hook = Any(help="optional hook for init'ing s3").tag(config=True)

    def __init__(self, *args, **kwargs):
        super(S3ContentsManager, self).__init__(*args, **kwargs)

        self.run_init_s3_hook()

        self._fs = S3FS(
            log=self.log,
            access_key_id=self.access_key_id,
            secret_access_key=self.secret_access_key,
            endpoint_url=self.endpoint_url,
            region_name=self.region_name,
            bucket=self.bucket,
            prefix=self.prefix,
            session_token=self.session_token,
            signature_version=self.signature_version,
            delimiter=self.delimiter,
            sse=self.sse,
            kms_key_id= self.kms_key_id,
            boto3_session=self.boto3_session)

    def run_init_s3_hook(self):
        if self.init_s3_hook is not None:
            self.init_s3_hook(self)

    def _save_notebook(self, model, path):
        nb_contents = from_dict(model['content'])
        self.check_and_sign(nb_contents, path)
        file_contents = json.dumps(model["content"])
        self._fs.writenotebook(path, file_contents)
        self.validate_notebook_model(model)
        return model.get("message")
