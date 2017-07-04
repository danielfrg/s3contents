"""
Utilities to make S3 look like a regular file system
"""
import boto3
from botocore.client import Config

from s3contents.ipycompat import Unicode
from s3contents.basefs import BaseFS, NoSuchFileException


class S3FS(BaseFS):

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
    signature_version = Unicode(help="").tag(config=True)

    def __init__(self, log, **kwargs):
        super(S3FS, self).__init__(log, **kwargs)
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

    def isfile(self, path):
        self.log.debug("S3contents[S3FS] Checking if `%s` is a file", path)
        key = self.as_key(path)
        try:
            self.client.head_object(Bucket=self.bucket_name, Key=key)
            is_file = True
        except Exception:
            is_file = False
        self.log.debug("S3contents[S3FS] `%s` is a file: %s", path, is_file)
        return is_file

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

    def read(self, path):
        key = self.as_key(path)
        if not self.isfile(path):
            raise NoSuchFileException(self.as_path(key))
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
