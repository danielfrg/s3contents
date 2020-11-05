import json
from urllib.parse import urlparse

from traitlets import Any

from s3contents.genericmanager import GenericContentsManager, from_dict
from s3contents.ipycompat import Unicode
from s3contents.s3_fs import S3FS


class S3ContentsManager(GenericContentsManager):

    access_key_id = Unicode(
        help="S3/AWS access key ID", allow_none=True, default_value=None
    ).tag(config=True, env="JPYNB_S3_ACCESS_KEY_ID")
    secret_access_key = Unicode(
        help="S3/AWS secret access key", allow_none=True, default_value=None
    ).tag(config=True, env="JPYNB_S3_SECRET_ACCESS_KEY")

    endpoint_url = Unicode("https://s3.amazonaws.com", help="S3 endpoint URL").tag(
        config=True, env="JPYNB_S3_ENDPOINT_URL"
    )
    region_name = Unicode("us-east-1", help="Region name").tag(
        config=True, env="JPYNB_S3_REGION_NAME"
    )
    bucket = Unicode("notebooks", help="Bucket name to store notebooks").tag(
        config=True, env="JPYNB_S3_BUCKET"
    )
    prefix = Unicode("", help="Prefix path inside the specified bucket").tag(
        config=True
    )
    signature_version = Unicode(help="").tag(config=True)
    delimiter = Unicode("/", help="Path delimiter").tag(config=True)
    sse = Unicode(help="Type of server-side encryption to use").tag(config=True)

    kms_key_id = Unicode(help="KMS ID to use to encrypt workbooks").tag(config=True)

    session_token = Unicode(
        help="S3/AWS session token", allow_none=True, default_value=None
    ).tag(config=True, env="JPYNB_S3_SESSION_TOKEN")

    boto3_session = Any(
        help="Place to store custom boto3 session (passed to S3_FS) - could be set by init_s3_hook"
    )
    init_s3_hook = Any(help="optional hook for init'ing s3").tag(config=True)

    s3fs_additional_kwargs = Any(help="optional dictionary to be appended to s3fs additional kwargs").tag(config=True)

    def __init__(self, *args, **kwargs):
        super(S3ContentsManager, self).__init__(*args, **kwargs)

        self.run_init_s3_hook()
        self.bucket = _validate_bucket(self.bucket, self.log)
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
            kms_key_id=self.kms_key_id,
            boto3_session=self.boto3_session,
            s3fs_additional_kwargs=self.s3fs_additional_kwargs
        )

    def run_init_s3_hook(self):
        if self.init_s3_hook is not None:
            self.init_s3_hook(self)

    def _save_notebook(self, model, path):
        nb_contents = from_dict(model["content"])
        self.check_and_sign(nb_contents, path)
        file_contents = json.dumps(model["content"])
        self._fs.writenotebook(path, file_contents)
        self.validate_notebook_model(model)
        return model.get("message")


def _validate_bucket(user_bucket, log):
    """Helper function to strip off schemas and keys from your bucket.

    Another approach may be to use regexes, but then you have to
    think about regexes...

    Parameters
    ----------
    user_bucket : str
        The bucket that the user provided in their jupyter_notebook_config.py
    log :
        The logger hanging off of GenericContentsManager

    Returns
    -------
    str
        The properly parsed bucket out of `user_bucket`

    Raises
    ------
    ValueError
        * When I'm not sure how to parse out a bucket from the provided input
        * When the user provides an empty bucket
    """
    if not user_bucket:
        raise ValueError(f"user_bucket function argument is empty: {user_bucket}")
    log.debug(f"s3manager._validate_bucket: User provided bucket: {user_bucket}")
    res = urlparse(user_bucket)
    scheme, netloc, path, params, query, fragment = res
    if netloc:
        bucket = netloc
        log.warning(
            "s3manager._validate_bucket: "
            f"Assuming you meant {bucket} for your bucket. "
            f"Using that. Please set bucket={bucket} "
            "in your jupyter_notebook_config.py file"
        )
        return bucket
    if scheme or netloc or params or query or fragment:
        log.error("s3manager._validate_bucket: " f"Invalid bucket specification: {res}")
        raise ValueError(f"Invalid bucket specification: {res}")

    bucket = path
    if "/" not in bucket:
        return bucket

    bucket, key = bucket.split("/", maxsplit=1)
    log.warning(
        "s3manager._validate_bucket: "
        f"Assuming you meant {bucket} for your bucket name. Don't "
        f"include '/' in your bucket name. Removing /{key} "
        f"from your bucket name. Please set bucket={bucket} "
        "in your jupyter_notebook_config.py file"
    )
    return bucket
