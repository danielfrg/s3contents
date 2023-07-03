from s3contents.gcs.gcs_fs import GCSFS
from s3contents.genericmanager import GenericContentsManager
from s3contents.ipycompat import Unicode
from fsspec.asyn import sync
import os


class GCSContentsManager(GenericContentsManager):
    project = Unicode(
        help="GCP Project", allow_none=True, default_value=None
    ).tag(config=True, env="JPYNB_GCS_PROJECT")
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

    def _convert_file_records(self, gcs_paths):
        """Convert gcs paths to models of the filetypes."""
        models = []
        gcs_paths = self.fs.remove_prefix(gcs_paths)
        self.log.debug("gcs paths", gcs_paths)
        for path in gcs_paths:
            if os.path.basename(path) == self.fs.dir_keep_file:
                continue
            _type = self.guess_type(path, allow_directory=True)
            if _type == "notebook":
                models.append(self._notebook_model_from_path(path, False))
            elif _type == "file":
                models.append(self._file_model_from_path(path, False, None))
            elif _type == "directory":
                models.append(self._directory_model_from_path(path, False))
            else:
                self.do_error(
                    "Unknown file type '%s' for file '%s'" % (_type, path), 500
                )
        return models

    def _list_contents(self, model, prefixed_path):
        # Specific to GCS filesystem
        files_gcs_detail = sync(self.fs.fs.loop, self.fs.fs._ls, prefixed_path)
        filtered_files_gcs_detail = list(
            filter(
                lambda detail: os.path.basename(detail) != "",
                files_gcs_detail,
            )
        )
        self.log.debug(f"listed files: {filtered_files_gcs_detail}\n")
        for files_gcs_detail in filtered_files_gcs_detail:
            self.log.debug(
                f"files_tcs_detail={files_gcs_detail}\n"
                f"lstat={self.fs.lstat(files_gcs_detail)}\n"
            )
        model["content"] = self._convert_file_records(
            filtered_files_gcs_detail
        )
        return model
