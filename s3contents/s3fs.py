"""
Utilities to make S3 look like a regular file system
"""
import six
import boto3
from botocore.client import Config

from s3contents.ipycompat import HasTraits, Unicode


class S3FS(HasTraits):

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
        "us-east-1", help="Region Name").tag(
            config=True, env="JPYNB_S3_REGION_NAME")
    bucket_name = Unicode(
        "notebooks", help="Bucket name to store notebooks").tag(
            config=True, env="JPYNB_S3_BUCKET_NAME")
    prefix = Unicode("", help="Prefix path inside the specified bucket").tag(config=True)
    signature_version = Unicode(help="").tag(config=True)
    delimiter = Unicode("/", help="Path delimiter").tag(config=True)

    dir_keep_file = Unicode(
        ".s3keep", help="Empty file to create when creating directories").tag(config=True)

    def __init__(self, log, **kwargs):
        super(S3FS, self).__init__(**kwargs)
        self.log = log

        config = None
        if self.signature_version:
            config = Config(signature_version=self.signature_version)

        self.client = boto3.client(
            "s3",
            aws_access_key_id=self.access_key_id,
            aws_secret_access_key=self.secret_access_key,
            endpoint_url=self.endpoint_url,
            region_name=self.region_name,
            config=config)

        self.resource = boto3.resource(
            "s3",
            aws_access_key_id=self.access_key_id,
            aws_secret_access_key=self.secret_access_key,
            endpoint_url=self.endpoint_url,
            region_name=self.region_name,
            config=config)

        self.bucket = self.resource.Bucket(self.bucket_name)
        self.delimiter = "/"

        if self.prefix:
            self.mkdir("")

    def get_keys(self, prefix=""):
        ret = []
        for obj in self.bucket.objects.filter(Prefix=prefix):
            ret.append(obj.key)
        return ret

    def listdir(self, path="", with_prefix=False):
        self.log.debug("S3contents[S3FS] Listing directory: `%s`", path)
        prefix = self.as_key(path)
        fnames = self.get_keys(prefix=prefix)
        fnames_no_prefix = [self.remove_prefix(fname, prefix=prefix) for fname in fnames]
        fnames_no_prefix = [fname.lstrip(self.delimiter) for fname in fnames_no_prefix]
        files = set(fname.split(self.delimiter)[0] for fname in fnames_no_prefix)
        if with_prefix:
            files = [
                self.join(prefix.strip(self.delimiter), f).strip(self.delimiter) for f in files
            ]
        else:
            files = list(files)
        return map(self.as_path, files)

    def isfile(self, path):
        self.log.debug("S3contents[S3FS] Checking if `%s` is a file", path)
        key = self.as_key(path)
        is_file = None
        if key == "":
            is_file = False
        try:
            self.client.head_object(Bucket=self.bucket_name, Key=key)
            is_file = True
        except Exception as e:
            is_file = False
        self.log.debug("S3contents[S3FS] `%s` is a file: %s", path, is_file)
        return is_file

    def isdir(self, path):
        self.log.debug("S3contents[S3FS] Checking if `%s` is a directory", path)
        key = self.as_key(path)
        if key == "":
            return True
        if not key.endswith(self.delimiter):
            key = key + self.delimiter
        if key == "":
            return True
        objs = list(self.bucket.objects.filter(Prefix=key))
        is_dir = len(objs) > 0
        self.log.debug("S3contents[S3FS] `%s` is a directory: %s", path, is_dir)
        return is_dir

    def mv(self, old_path, new_path):
        self.cp(old_path, new_path)
        self.rm(old_path)

    def cp(self, old_path, new_path):
        self.log.debug("S3contents[S3FS] Copy `%s` to `%s`", old_path, new_path)
        if self.isdir(old_path):
            old_dir_path, new_dir_path = old_path, new_path
            old_dir_key = self.as_key(old_dir_path)
            for obj in self.bucket.objects.filter(Prefix=old_dir_key):
                old_item_path = self.as_path(obj.key)
                new_item_path = old_item_path.replace(old_dir_path, new_dir_path, 1)
                self.cp(old_item_path, new_item_path)
        elif self.isfile(old_path):
            old_key = self.as_key(old_path)
            new_key = self.as_key(new_path)
            source = "{bucket_name}/{old_key}".format(bucket_name=self.bucket_name, old_key=old_key)
            self.client.copy_object(Bucket=self.bucket_name, CopySource=source, Key=new_key)

    def rm(self, path):
        self.log.debug("S3contents[S3FS] Deleting: `%s`", path)
        if self.isfile(path):
            key = self.as_key(path)
            self.client.delete_object(Bucket=self.bucket_name, Key=key)
        elif self.isdir(path):
            key = self.as_key(path)
            key = key + "/"
            objects_to_delete = []
            for obj in self.bucket.objects.filter(Prefix=key):
                objects_to_delete.append({"Key": obj.key})
            self.bucket.delete_objects(Delete={"Objects": objects_to_delete})

    def mkdir(self, path):
        self.log.debug("S3contents[S3FS] Making dir: `%s`", path)
        if self.isfile(path):
            self.log.debug("S3contents[S3FS] File `%s` already exists, not creating anything", path)
        elif self.isdir(path):
            self.log.debug("S3contents[S3FS] Directory `%s` already exists, not creating anything",
                           path)
        else:
            obj_path = self.join(path, self.dir_keep_file)
            self.write(obj_path, "")

    def read(self, path):
        key = self.as_key(path)
        if not self.isfile(path):
            raise NoSuchFile(self.as_path(key))
        obj = self.resource.Object(self.bucket_name, key)
        text = obj.get()["Body"].read().decode("utf-8")
        return text

    def lstat(self, path):
        key = self.as_key(path)
        if not self.isfile(path):
            raise NoSuchFile(self.as_path(key))
        obj = self.resource.Object(self.bucket_name, key)

        info = {}
        info["ST_MTIME"] = obj.last_modified
        return info

    def write(self, path, content):
        key = self.as_key(path)
        self.client.put_object(Bucket=self.bucket_name, Key=key, Body=content)

    def as_key(self, path):
        """Utility: Make a path a S3 key
        """
        path_ = self.abspath(path)
        self.log.debug("S3contents[S3FS] Understanding `%s` as `%s`", path, path_)
        if isinstance(path_, six.string_types):
            return path_.strip(self.delimiter)
        if isinstance(path_, list):
            return [self.as_key(item) for item in path_]

    def as_path(self, key):
        """Utility: Make a S3 key a path
        """
        key_ = self.remove_prefix(key)
        if isinstance(key_, six.string_types):
            return key_.strip(self.delimiter)

    def remove_prefix(self, text, prefix=None):
        """Utility: remove a prefix from a string
        """
        if prefix is None:
            prefix = self.prefix
        if text.startswith(prefix):
            return text[len(prefix):].strip("/")
        return text.strip("/")

    def join(self, *args):
        """Utility: join using the delimiter
        """
        return self.delimiter.join(args)

    def abspath(self, path):
        """Utility: Return a normalized absolutized version of the pathname path
        Basically prepends the path with the prefix
        """
        path = path.strip("/")
        if self.prefix:
            path = self.join(self.prefix, path)
        return path.strip("/")


class S3FSError(Exception):
    pass


class NoSuchFile(S3FSError):

    def __init__(self, path, *args, **kwargs):
        super(NoSuchFile, self).__init__(*args, **kwargs)
        self.path = path
