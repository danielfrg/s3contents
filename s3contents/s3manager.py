import os
import json
import mimetypes
from datetime import datetime

from tornado.web import HTTPError

from s3contents.s3fs import S3FS, S3FSError
from s3contents.ipycompat import ContentsManager
from s3contents.ipycompat import HasTraits, Unicode
from s3contents.ipycompat import reads, from_dict, GenericFileCheckpoints

DUMMY_CREATED_DATE = datetime.fromtimestamp(0)
NBFORMAT_VERSION = 4


class S3ContentsManager(ContentsManager, HasTraits):

    access_key_id = Unicode(help="S3/AWS access key ID").tag(config=True, env="JPYNB_S3_ACCESS_KEY_ID")
    secret_access_key = Unicode(help="S3/AWS secret access key").tag(config=True, env="JPYNB_S3_SECRET_ACCESS_KEY")

    bucket_name = Unicode("notebooks", help="The").tag(config=True, env="JPYNB_S3_BUCKET_NAME")
    region_name = Unicode("us-east-1", help="Region Name").tag(config=True, env="JPYNB_S3_REGION_NAME")
    endpoint_url = Unicode("s3.amazonaws.com", help="The").tag(config=True, env="JPYNB_S3_ENDPOINT_URL")
    signature_version = Unicode(help="").tag(config=True)
    delimiter = Unicode("/", help="Path delimiter").tag(config=True)

    def __init__(self, *args, **kwargs):
        super(S3ContentsManager, self).__init__(*args, **kwargs)

        self.s3fs = S3FS(
            access_key_id=self.access_key_id,
            secret_access_key=self.secret_access_key,
            bucket_name=self.bucket_name,
            region_name=self.region_name,
            endpoint_url=self.endpoint_url,
            signature_version=self.signature_version,
            delimiter=self.delimiter
        )

    def _checkpoints_class_default(self):
        return GenericFileCheckpoints

    def do_error(self, msg, code=500):
        raise HTTPError(code, msg)

    def no_such_entity(self, path):
        self.do_error("No such entity: [{path}]".format(path=path), 404)

    def guess_type(self, path, allow_directory=True):
        """
        Guess the type of a file.
        If allow_directory is False, don't consider the possibility that the
        file is a directory.

        Parameters
        ----------
            obj: s3.Object or string
        """
        if path.endswith(".ipynb"):
            return "notebook"
        elif allow_directory and self.dir_exists(path):
            return "directory"
        else:
            return "file"

    def dir_exists(self, path):
        # Does a directory exist at the given path?
        self.log.debug("dir_exists '%s'", path)
        return self.s3fs.isdir(path)

    def file_exists(self, path):
        # Does a file exist at the given path?
        self.log.debug("file_exists '%s'", path)
        return self.s3fs.isfile(path)

    def get(self, path, content=True, type=None, format=None):
        # Get a file or directory model.
        self.log.debug("get '%s' %s %s", path, type, format)
        path = path.strip('/')

        if type is None:
            type = self.guess_type(path)
        try:
            fn = {
                "directory": self._get_directory,
                "notebook": self._get_notebook,
                "file": self._get_file,
            }[type]
        except KeyError:
            raise ValueError("Unknown type passed: '{}'".format(type))

        return fn(path=path, content=content, format=format)

    def _get_directory(self, path, content=True, format=None):
        self.log.debug("get_directory '%s' %s %s", path, type, format)
        # key = self._path_to_s3_key_dir(path)
        return self._directory_model_from_path(path, content=content)

    def _get_notebook(self, path, content=True, format=None):
        self.log.debug("get_notebook '%s' %s %s", path, content, format)
        return self._notebook_model_from_path(path, content=content, format=format)

    def _get_file(self, path, content=True, format=None):
        self.log.debug("get_file '%s' %s %s", path, content, format)
        return self._file_model_from_path(path, content=content, format=format)

    def _directory_model_from_path(self, path, content=False):
        model = base_directory_model(path)
        if content:
            model["format"] = "json"
            model["content"] = self._convert_file_records(self.s3fs.listdir(prefix=path, with_prefix=True))
        return model

    def _notebook_model_from_path(self, path, content=False, format=None):
        """
        Build a notebook model from database record.
        """
        # path = to_api_path(record['parent_name'] + record['name'])
        model = base_model(path)
        model['type'] = 'notebook'
        # model['last_modified'] = model['created'] = record['created_at']
        model['last_modified'] = model['created'] = DUMMY_CREATED_DATE
        if content:
            if not self.s3fs.isfile(path):
                self.no_such_entity(path)
            file_content = self.s3fs.read(path)
            nb_content = reads(file_content, as_version=NBFORMAT_VERSION)
            self.mark_trusted_cells(nb_content, path)
            model["format"] = "json"
            model["content"] = nb_content
            self.validate_notebook_model(model)
        return model

    def _file_model_from_path(self, path, content=False, format=None):
        """
        Build a file model from database record.
        """
        model = base_model(path)
        model['type'] = 'file'
        model['last_modified'] = model['created'] = DUMMY_CREATED_DATE
        if content:
            try:
                content = self.s3fs.read(path)
            except S3FSError as e:
                self.do_error(str(e), 500)
            model["format"] = format or "text"
            model["content"] = content
            model["mimetype"] = mimetypes.guess_type(path)[0] or "text/plain"
            if format == "base64":
                model["format"] = format or "base64"
                from base64 import b64decode
                model["content"] = content = b64decode(content)
        return model

    def _convert_file_records(self, paths):
        """
        Apply _notebook_model_from_s3_path or _file_model_from_s3_path to each entry
        in paths, depending on the result of `guess_type`.
        """
        ret = []
        for path in paths:
            if os.path.basename(path) == self.s3fs.dir_keep_file:
                continue
            type_ = self.guess_type(path, allow_directory=True)
            if type_ == "notebook":
                ret.append(self._notebook_model_from_path(path, False))
            elif type_ == "file":
                ret.append(self._file_model_from_path(path, False, None))
            elif type_ == "directory":
                ret.append(self._directory_model_from_path(path, False))
            else:
                self.do_error("Unknown file type %s for file '%s'" % (type_, path), 500)
        return ret

    def save(self, model, path):
        # Save a file or directory model to path.
        self.log.debug("save %s: '%s'", model, path)
        if "type" not in model:
            self.do_error("No model type provided", 400)
        if "content" not in model and model["type"] != "directory":
            self.do_error("No file content provided", 400)

        if model["type"] not in ("file", "directory", "notebook"):
            self.do_error("Unhandled contents type: %s" % model["type"], 400)

        try:
            if model["type"] == "notebook":
                validation_message = self._save_notebook(model, path)
            elif model["type"] == "file":
                validation_message = self._save_file(model, path)
            else:
                validation_message = self._save_directory(path)
        except Exception as e:
            self.log.error("Error while saving file: %s %s", path, e, exc_info=True)
            self.do_error("Unexpected error while saving file: %s %s" % (path, e), 500)

        model = self.get(path, type=model["type"], content=False)
        if validation_message is not None:
            model["message"] = validation_message
        return model

    def _save_notebook(self, model, path):
        nb_contents = from_dict(model['content'])
        self.check_and_sign(nb_contents, path)
        file_contents = json.dumps(model["content"])
        self.s3fs.write(path, file_contents)
        self.validate_notebook_model(model)
        return model.get("message")

    def _save_file(self, model, path):
        file_contents = model["content"]
        self.s3fs.write(path, file_contents)

    def _save_directory(self, path):
        self.s3fs.mkdir(path)

    def rename_file(self, old_path, new_path):
        # Rename a file or directory.
        self.log.debug("rename_file '%s' '%s'", old_path, new_path)
        if self.file_exists(old_path):
            self.s3fs.mv(old_path, new_path)
        elif self.dir_exists(old_path):
            self.do_error("Cannot rename a directory", 409)
        else:
            self.no_such_entity(old_path)

    def delete_file(self, path):
        # Delete the file or directory at path.
        self.log.debug("delete_file '%s'", path)
        if self.file_exists(path):
            self.s3fs.rm(path)
        elif self.dir_exists(path):
            self.do_error("Cannot delete directory")
        else:
            self.no_such_entity(path)

    def is_hidden(self, path):
        # Is path a hidden directory or file?
        self.log.debug("is_hidden '%s'", path)
        return False


def base_model(path):
    return {
        "name": path.rsplit('/', 1)[-1],
        "path": path,
        "writable": True,
        "last_modified": None,
        "created": None,
        "content": None,
        "format": None,
        "mimetype": None,
    }


def base_directory_model(path):
    m = base_model(path)
    m.update(
        type="directory",
        last_modified=DUMMY_CREATED_DATE,
        created=DUMMY_CREATED_DATE,
    )
    return m
