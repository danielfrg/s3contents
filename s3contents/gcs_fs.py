import base64
import os

import gcsfs
from tornado.web import HTTPError

from s3contents.genericfs import GenericFS, NoSuchFile
from s3contents.ipycompat import Unicode


class GCSFS(GenericFS):

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

    dir_keep_file = Unicode(
        ".gcskeep", help="Empty file to create when creating directories"
    ).tag(config=True)

    def __init__(self, log, **kwargs):
        super(GCSFS, self).__init__(**kwargs)
        self.log = log

        token = os.path.expanduser(self.token)
        self.fs = gcsfs.GCSFileSystem(project=self.project, token=token)

        self.init()

    def init(self):
        self.mkdir("")
        self.ls("")
        assert self.isdir(""), "The root directory should exists :)"

    #  GenericFS methods -----------------------------------------------------------------------------------------------

    def ls(self, path):
        path_ = self.path(path)
        self.log.debug("S3contents.GCSFS: Listing directory: `%s`", path_)
        files = self.fs.ls(path_)
        return self.unprefix(files)

    def isfile(self, path):
        path_ = self.path(path)
        is_file = False

        exists = self.fs.exists(path_)
        if not exists:
            is_file = False
        else:
            try:
                is_file = self.fs.info(path_)['type'] == 'file'
            except FileNotFoundError:
                pass

        self.log.debug("S3contents.GCSFS: `%s` is a file: %s", path_, is_file)
        return is_file

    def isdir(self, path):
        # GCSFS doesnt return exists=True for a directory with no files so
        # we need to check if the dir_keep_file exists
        is_dir = self.isfile(path + self.separator + self.dir_keep_file)
        path_ = self.path(path)
        self.log.debug("S3contents.GCSFS: `%s` is a directory: %s", path_, is_dir)
        return is_dir

    def mv(self, old_path, new_path):
        self.log.debug("S3contents.GCSFS: Move file `%s` to `%s`", old_path, new_path)
        self.cp(old_path, new_path)
        self.rm(old_path)

    def cp(self, old_path, new_path):
        old_path_, new_path_ = self.path(old_path), self.path(new_path)
        self.log.debug("S3contents.GCSFS: Coping `%s` to `%s`", old_path_, new_path_)

        if self.isdir(old_path):
            old_dir_path, new_dir_path = old_path, new_path
            for obj in self.ls(old_dir_path):
                old_item_path = obj
                new_item_path = old_item_path.replace(old_dir_path, new_dir_path, 1)
                self.cp(old_item_path, new_item_path)
        elif self.isfile(old_path):
            self.fs.copy(old_path_, new_path_)

    def rm(self, path):
        path_ = self.path(path)
        self.log.debug("S3contents.GCSFS: Removing: `%s`", path_)
        if self.isfile(path):
            self.log.debug("S3contents.GCSFS: Removing file: `%s`", path_)
            self.fs.rm(path_)
        elif self.isdir(path):
            self.log.debug("S3contents.GCSFS: Removing directory: `%s`", path_)
            dirs = self.fs.walk(path_)
            for dir in dirs:
                for file in dir[2]:
                    self.fs.rm(dir[0] + self.separator + file)

    def mkdir(self, path):
        path_ = self.path(path, self.dir_keep_file)
        self.log.debug("S3contents.GCSFS: Making dir (touch): `%s`", path_)
        self.fs.touch(path_)

    def read(self, path, format):
        path_ = self.path(path)
        if not self.isfile(path):
            raise NoSuchFile(path_)
        with self.fs.open(path_, mode="rb") as f:
            content = f.read()
        if format == "base64":
            return base64.b64encode(content).decode("ascii"), "base64"
        else:
            # Try to interpret as unicode if format is unknown or if unicode
            # was explicitly requested.
            try:
                return content.decode("utf-8"), "text"
            except UnicodeError:
                if format == "text":
                    err = "{} is not UTF-8 encoded".format(path_)
                    self.log.error(err)
                    raise HTTPError(400, err, reason="bad format")

    def lstat(self, path):
        path_ = self.path(path)
        info = self.fs.info(path_)
        ret = {}
        if "updated" in info:
            ret["ST_MTIME"] = info["updated"]
        return ret

    def write(self, path, content, format):
        path_ = self.path(self.unprefix(path))
        self.log.debug("S3contents.GCSFS: Writing file: `%s`", path_)
        with self.fs.open(path_, mode="wb") as f:
            if format == "base64":
                b64_bytes = content.encode("ascii")
                content_ = base64.b64decode(b64_bytes)
            else:
                content_ = content.encode("utf8")
            f.write(content_)

    #  Utilities -------------------------------------------------------------------------------------------------------

    def strip(self, path):
        if isinstance(path, str):
            return path.strip(self.separator)
        if isinstance(path, (list, tuple)):
            return list(map(self.strip, path))

    def join(self, *paths):
        paths = self.strip(paths)
        return self.separator.join(paths)

    def get_prefix(self):
        """Full prefix: bucket + optional prefix"""
        prefix = self.bucket
        if self.prefix:
            prefix += self.separator + self.prefix
        return prefix

    prefix_ = property(get_prefix)

    def unprefix(self, path):
        """Remove the self.prefix_ (if present) from a path or list of paths"""
        path = self.strip(path)
        if isinstance(path, str):
            path = path[len(self.prefix_) :] if path.startswith(self.prefix_) else path
            path = path[1:] if path.startswith(self.separator) else path
            return path
        if isinstance(path, (list, tuple)):
            path = [
                p[len(self.prefix_) :] if p.startswith(self.prefix_) else p
                for p in path
            ]
            path = [p[1:] if p.startswith(self.separator) else p for p in path]
            return path

    def path(self, *path):
        """Utility to join paths including the bucket and prefix"""
        path = list(filter(None, path))
        path = self.unprefix(path)
        items = [self.prefix_] + path
        return self.join(*items)
