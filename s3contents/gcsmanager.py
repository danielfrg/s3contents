from s3contents.gcs_fs import GCSFS
from s3contents.genericmanager import GenericContentsManager
from s3contents.ipycompat import Unicode


class GCSContentsManager(GenericContentsManager):

    project = Unicode(help="GCP Project", allow_none=True, default_value=None).tag(
        config=True, env="JPYNB_GCS_PROJECT"
    )
    token = Unicode(
        help="Path to the GCP token", allow_none=True, default_value=None
    ).tag(config=True, env="JPYNB_GCS_TOKEN_PATH")

    region_name = Unicode("us-east-1", help="Region name").tag(
        config=True, env="JPYNB_GCS_REGION_NAME"
    )
    bucket = Unicode("notebooks", help="Bucket name to store notebooks").tag(
        config=True, env="JPYNB_GCS_BUCKET"
    )

    prefix = Unicode("", help="Prefix path inside the specified bucket").tag(
        config=True
    )
    separator = Unicode("/", help="Path separator").tag(config=True)

    def __init__(self, *args, **kwargs):
        super(GCSContentsManager, self).__init__(*args, **kwargs)

        self._fs = GCSFS(
            log=self.log,
            project=self.project,
            token=self.token,
            bucket=self.bucket,
            prefix=self.prefix,
            separator=self.separator,
        )
