"""
Utilities to make S3 look like a regular file system
"""
import six
import boto3
from botocore.client import Config

from s3contents.ipycompat import HasTraits, Unicode


class S3FS(HasTraits):

    access_key_id = Unicode(help="S3/AWS access key ID").tag(config=True, env="JPYNB_S3_ACCESS_KEY_ID")
    secret_access_key = Unicode(help="S3/AWS secret access key").tag(config=True, env="JPYNB_S3_SECRET_ACCESS_KEY")

    bucket_name = Unicode("notebooks", help="The").tag(config=True, env="JPYNB_S3_BUCKET_NAME")
    region_name = Unicode("us-east-1", help="Region Name").tag(config=True, env="JPYNB_S3_REGION_NAME")
    endpoint_url = Unicode("s3.amazonaws.com", help="The").tag(config=True, env="JPYNB_S3_ENDPOINT_URL")
    signature_version = Unicode(help="").tag(config=True)
    delimiter = Unicode("/", help="Path delimiter").tag(config=True)

    dir_keep_file = Unicode(".s3keep", help="Empty file to create when creating directories").tag(config=True)

    def __init__(self, **kwargs):
        super(S3FS, self).__init__(**kwargs)

        config = None
        if self.signature_version:
            config = Config(signature_version=self.signature_version)

        self.client = boto3.client(
            "s3",
            aws_access_key_id=self.access_key_id,
            aws_secret_access_key=self.secret_access_key,
            endpoint_url=self.endpoint_url,
            region_name=self.region_name,
            config=config
        )

        self.resource = boto3.resource(
            "s3",
            aws_access_key_id=self.access_key_id,
            aws_secret_access_key=self.secret_access_key,
            endpoint_url=self.endpoint_url,
            region_name=self.region_name,
            config=config
        )

        self.bucket = self.resource.Bucket(self.bucket_name)
        self.delimiter = "/"

    def as_key(self, data):
        if isinstance(data, six.string_types):
            # return data.replace("/", delimiter).strip(delimiter)
            # data = data.replace(" ", "_")
            return data.strip(self.delimiter)
        if isinstance(data, list):
            return [self.as_key(item) for item in data]

    def as_path(self, data):
        if isinstance(data, six.string_types):
            return data.strip(self.delimiter)
            # return data.replace(delimiter, "/").strip("/")
        if isinstance(data, list):
            return [self.as_path(item) for item in data]
        return

    def remove_prefix(self, text, prefix):
        if text.startswith(prefix):
            return text[len(prefix):]
        return text

    def join(self, *args):
        return self.delimiter.join(args)

    def get_keys(self, prefix=""):
        ret = []
        for obj in self.bucket.objects.filter(Prefix=prefix):
            ret.append(obj.key)
        return ret

    def listdir(self, prefix="", with_prefix=False):
        prefix = self.as_key(prefix)
        fnames = self.get_keys(prefix=prefix)
        fnames_no_prefix = [self.remove_prefix(n, prefix) for n in fnames]
        fnames_no_prefix = [n.lstrip(self.delimiter) for n in fnames_no_prefix]
        files = set(n.split(self.delimiter)[0] for n in fnames_no_prefix)
        if with_prefix:
            files = [self.join(prefix.strip(self.delimiter), f).strip(self.delimiter) for f in files]
        else:
            files = list(files)
        return self.as_path(files)

    def isfile(self, key):
        key = self.as_key(key)
        if key == "":
            return False
        try:
            self.client.head_object(Bucket=self.bucket_name, Key=key)
            return True
        except Exception as e:
            return False

    def isdir(self, path):
        path = self.as_key(path)
        if path == "":
            return True
        if not path.endswith(self.delimiter):
            path = path + self.delimiter
        if path == "":
            return True
        objs = list(self.bucket.objects.filter(Prefix=path))
        return len(objs) > 0

    def mv(self, old_path, new_path):
        self.cp(old_path, new_path)
        self.rm(old_path)

    def cp(self, old_path, new_path):
        old_key = self.as_key(old_path)
        new_key = self.as_key(new_path)
        source = "{bucket_name}/{old_key}".format(bucket_name=self.bucket_name, old_key=old_key)
        self.client.copy_object(Bucket=self.bucket_name, CopySource=source, Key=new_key)

    def rm(self, path):
        self.client.delete_object(Bucket=self.bucket_name, Key=path)

    def mkdir(self, path):
        obj_path = self.join(path, self.dir_keep_file)
        self.write(obj_path, "")

    def read(self, path):
        key = self.as_key(path)
        if not self.isfile(path):
            raise S3FSError("Key '%s' doesn't exist" % key)
        obj = self.resource.Object(self.bucket_name, key)
        text = obj.get()['Body'].read().decode('utf-8')
        return text

    def write(self, path, content):
        key = self.as_key(path)
        self.client.put_object(Bucket=self.bucket_name, Key=key, Body=content)


class S3FSError(Exception):
    pass
