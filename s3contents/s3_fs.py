"""
Utilities to make S3 look like a regular file system
"""
import os
import sys
import six
import s3fs
import base64

from tornado.web import HTTPError
from botocore.exceptions import ClientError

from s3contents.compat import FileNotFoundError
from s3contents.ipycompat import Unicode
from s3contents.genericfs import GenericFS, NoSuchFile


SAMPLE_ACCESS_POLICY = """
{{
    "Sid": "S3contentsKeepFile",
    "Action": [
        "s3:*"
    ],
    "Effect": "Allow",
    "Resource": [
        "arn:aws:s3:::{bucket}/.s3keep"
    ]
}}
"""


class S3FS(GenericFS):

    access_key_id = Unicode(
        help="S3/AWS access key ID", allow_none=True, default_value=None).tag(
            config=True, env="JPYNB_S3_ACCESS_KEY_ID")
    secret_access_key = Unicode(
        help="S3/AWS secret access key", allow_none=True, default_value=None).tag(
            config=True, env="JPYNB_S3_SECRET_ACCESS_KEY")

    endpoint_url = Unicode(
        "s3.amazonaws.com", help="S3 endpoint URL").tag(
            config=True, env="JPYNB_S3_ENDPOINT_URL")
    region_name = Unicode(
        "us-east-1", help="Region name").tag(
            config=True, env="JPYNB_S3_REGION_NAME")
    bucket = Unicode(
        "notebooks", help="Bucket name to store notebooks").tag(
            config=True, env="JPYNB_S3_BUCKET")
    signature_version = Unicode(help="").tag(config=True)
    sse = Unicode(help="Type of server-side encryption to use").tag(config=True)

    prefix = Unicode("", help="Prefix path inside the specified bucket").tag(config=True)
    delimiter = Unicode("/", help="Path delimiter").tag(config=True)

    dir_keep_file = Unicode(
        ".s3keep", help="Empty file to create when creating directories").tag(config=True)

    session_token = Unicode(
        help="S3/AWS session token",
        allow_none=True,
        default_value=None
    ).tag(config=True, env="JPYNB_S3_SESSION_TOKEN")

    def __init__(self, log, **kwargs):
        super(S3FS, self).__init__(**kwargs)
        self.log = log

        client_kwargs = {
            "endpoint_url": self.endpoint_url,
            "region_name": self.region_name,
        }
        config_kwargs = {}
        if self.signature_version:
            config_kwargs["signature_version"] = self.signature_version
        s3_additional_kwargs = {}
        if self.sse:
            s3_additional_kwargs["ServerSideEncryption"] = self.sse

        self.fs = s3fs.S3FileSystem(key=self.access_key_id,
                                    secret=self.secret_access_key,
                                    token=self.session_token,
                                    client_kwargs=client_kwargs,
                                    config_kwargs=config_kwargs,
                                    s3_additional_kwargs=s3_additional_kwargs)

        self.init()

    def init(self):
        try:
            self.mkdir("")
            self.ls("")
            self.isdir("")
        except ClientError as ex:
            if "AccessDenied" in str(ex):
                policy = SAMPLE_ACCESS_POLICY.format(bucket=os.path.join(self.bucket, self.prefix))
                self.log.error("AccessDenied error while creating initial S3 objects. Create an IAM policy like:\n{policy}".format(policy=policy))
                sys.exit(1)
            else:
                raise ex

    #  GenericFS methods -----------------------------------------------------------------------------------------------

    def ls(self, path=""):
        path_ = self.path(path)
        self.log.debug("S3contents.S3FS: Listing directory: `%s`", path_)
        files = self.fs.ls(path_, refresh=True)
        return self.unprefix(files)

    def isfile(self, path):
        path_ = self.path(path)
        is_file = False

        exists = self.fs.exists(path_)
        if not exists:
            is_file = False
        else:
            try:
                # Info will fail if path is a dir
                self.fs.info(path_, refresh=True)
                is_file = True
            except FileNotFoundError:
                pass

        self.log.debug("S3contents.S3FS: `%s` is a file: %s", path_, is_file)
        return is_file

    def isdir(self, path):
        path_ = self.path(path)
        is_dir = False

        exists = self.fs.exists(path_)
        if not exists:
            is_dir = False
        else:
            try:
                # Info will fail if path is a dir
                self.fs.info(path_, refresh=True)
                is_dir = False
            except FileNotFoundError:
                is_dir = True

        self.log.debug("S3contents.S3FS: `%s` is a directory: %s", path_, is_dir)
        return is_dir

    def mv(self, old_path, new_path):
        self.log.debug("S3contents.S3FS: Move file `%s` to `%s`", old_path, new_path)
        self.cp(old_path, new_path)
        self.rm(old_path)

    def cp(self, old_path, new_path):
        old_path_, new_path_ = self.path(old_path), self.path(new_path)
        self.log.debug("S3contents.S3FS: Coping `%s` to `%s`", old_path_, new_path_)

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
        self.log.debug("S3contents.S3FS: Removing: `%s`", path_)
        if self.isfile(path):
            self.log.debug("S3contents.S3FS: Removing file: `%s`", path_)
            self.fs.rm(path_)
        elif self.isdir(path):
            self.log.debug("S3contents.S3FS: Removing directory: `%s`", path_)
            self.fs.rm(path_ + self.delimiter, recursive=True)
            # self.fs.rmdir(path_ + self.delimiter, recursive=True)

    def mkdir(self, path):
        path_ = self.path(path, self.dir_keep_file)
        self.log.debug("S3contents.S3FS: Making dir: `%s`", path_)
        self.fs.touch(path_)

    def read(self, path):
        path_ = self.path(path)
        if not self.isfile(path):
            raise NoSuchFile(path_)
        with self.fs.open(path_, mode='rb') as f:
            content = f.read().decode("utf-8")
        return content

    def lstat(self, path):
        path_ = self.path(path)
        info = self.fs.info(path_, refresh=True)
        ret = {}
        ret["ST_MTIME"] = info["LastModified"]
        return ret

    def write(self, path, content, format):
        path_ = self.path(self.unprefix(path))
        self.log.debug("S3contents.S3FS: Writing file: `%s`", path_)
        if format not in {'text', 'base64'}:
            raise HTTPError(
                400,
                "Must specify format of file contents as 'text' or 'base64'",
            )
        try:
            if format == 'text':
                content_ = content.encode('utf8')
            else:
                b64_bytes = content.encode('ascii')
                content_ = base64.b64decode(b64_bytes)
        except Exception as e:
            raise HTTPError(
                400, u'Encoding error saving %s: %s' % (path_, e)
            )
        with self.fs.open(path_, mode='wb') as f:
            f.write(content_)

    def writenotebook(self, path, content):
        path_ = self.path(self.unprefix(path))
        self.log.debug("S3contents.S3FS: Writing notebook: `%s`", path_)
        with self.fs.open(path_, mode='wb') as f:
            f.write(content.encode("utf-8"))

    #  Utilities -------------------------------------------------------------------------------------------------------

    def get_prefix(self):
        """Full prefix: bucket + optional prefix"""
        prefix = self.bucket
        if self.prefix:
            prefix += self.delimiter + self.prefix
        return prefix
    prefix_ = property(get_prefix)

    def unprefix(self, path):
        """Remove the self.prefix_ (if present) from a path or list of paths"""
        if isinstance(path, six.string_types):
            path = path[len(self.prefix_):] if path.startswith(self.prefix_) else path
            path = path[1:] if path.startswith(self.delimiter) else path
            return path
        if isinstance(path, (list, tuple)):
            path = [p[len(self.prefix_):] if p.startswith(self.prefix_) else p for p in path]
            path = [p[1:] if p.startswith(self.delimiter) else p for p in path]
            return path

    def path(self, *path):
        """Utility to join paths including the bucket and prefix"""
        path = list(filter(None, path))
        path = self.unprefix(path)
        items = [self.prefix_] + path
        return self.delimiter.join(items)
