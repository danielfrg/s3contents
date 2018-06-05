from datetime import datetime
import six
import storefact
from simplekv import CopyMixin
from simplekv.decorator import URLEncodeKeysDecorator

from s3contents.ipycompat import Unicode
from s3contents.genericfs import GenericFS, NoSuchFile

DUMMY_CREATED_DATE = datetime.fromtimestamp(0)


class StorefactFS(GenericFS):

    store_url = Unicode(
        "store_url", help="Storefact URL which configures the notebook store").tag(
            config=True, env="JPYNB_STOREFACT_URL")

    prefix = Unicode("", help="Prefix path inside the specified bucket").tag(config=True)
    separator = Unicode("/", help="Path separator").tag(config=True)

    dir_keep_file = Unicode(
        ".s3keep", help="Empty file to create when creating directories").tag(config=True)

    def __init__(self, log, **kwargs):
        super(StorefactFS, self).__init__(**kwargs)
        self.log = log
        self.original_store = storefact.get_store_from_url(kwargs['store_url'])
        self.store = URLEncodeKeysDecorator(self.original_store)
        self.init()

    def init(self):
        self.mkdir("")
        self.ls("")
        self.isdir("")

    #  GenericFS methods -----------------------------------------------------------------------------------------------

    def ls(self, path=""):
        prefix = self.as_key(path)
        fnames = self.store.keys(prefix=prefix)
        fnames_no_prefix = [self.remove_prefix(fname, prefix=prefix) for fname in fnames]
        fnames_no_prefix = [fname.lstrip(self.separator) for fname in fnames_no_prefix]
        files = set(fname.split(self.separator)[0] for fname in fnames_no_prefix)
        files = [
            self.join(prefix.strip(self.separator), f).strip(self.separator) for f in files
        ]
        return map(self.as_path, files)

    def isfile(self, path):
        key = self.as_key(path)
        if key != "" and key in self.store:
            self.log.debug("S3contents.StorefactFS: `%s` is a file: %s", path, True)
            return True
        self.log.debug("S3contents.StorefactFS: `%s` is a file: %s", path, False)
        return False

    def isdir(self, path):
        self.log.debug("S3contents.StorefactFS: Checking if `%s` is a directory", path)
        key = self.as_key(path)

        root_keep_file = self.as_key(self.dir_keep_file)
        if (key == "" or key == self.prefix) and root_keep_file in self.store:
            self.log.debug("S3contents.StorefactFS: `%s` is a directory: %s", path, True)
            return True
        if not key.endswith(self.separator):
            key = key + self.separator
        if (key == "" or key == self.prefix) and root_keep_file in self.store:
            self.log.debug("S3contents.StorefactFS: `%s` is a directory: %s", path, True)
            return True
        is_dir = len(self.store.keys(prefix=key)) > 0
        self.log.debug("S3contents.StorefactFS: `%s` is a directory: %s", path, is_dir)
        return is_dir

    def mv(self, old_path, new_path):
        self.log.debug("S3contents.StorefactFS: Move file `%s` to `%s`", old_path, new_path)
        self.cp(old_path, new_path)
        self.rm(old_path)

    def cp(self, old_path, new_path):
        self.log.debug("S3contents.StorefactFS: Copy `%s` to `%s`", old_path, new_path)
        if self.isdir(old_path):
            old_dir_path, new_dir_path = old_path, new_path
            old_dir_key = self.as_key(old_dir_path)
            for key in self.store.keys(prefix=old_dir_key):
                old_item_path = self.as_path(key)
                new_item_path = old_item_path.replace(old_dir_path, new_dir_path, 1)
                self.cp(old_item_path, new_item_path)
        elif self.isfile(old_path):
            old_key = self.as_key(old_path)
            new_key = self.as_key(new_path)
            # we can not use self.store here as it is decorated
            if isinstance(self.original_store, CopyMixin):
                    self.store.copy(old_key, new_key)
            else:
                self.store.put(new_key, self.store.get(old_key))

    def rm(self, path):
        self.log.debug("S3contents.StorefactFS: Removing: `%s`", path)
        if self.isdir(path):
            self.log.debug("S3contents.StorefactFS: Removing directory: `%s`", path)
            key = self.as_key(path)
            key += "/"
            for obj in self.store.keys(prefix=key):
                self.store.delete(obj)
        elif self.isfile(path):
            self.log.debug("S3contents.StorefactFS: Removing file: `%s`", path)
            key = self.as_key(path)
            self.store.delete(key)

    def mkdir(self, path):
        self.log.debug("S3contents.StorefactFS: Making dir: `%s`", path)
        if self.isfile(path):
            self.log.debug("S3contents.StorefactFS: File `%s` already exists, not creating anything", path)
        elif self.isdir(path):
            self.log.debug("S3contents.StorefactFS: Directory `%s` already exists, not creating anything",
                           path)
        else:
            obj_path = self.join(path, self.dir_keep_file)
            self.write(obj_path, "")

    def read(self, path):
        key = self.as_key(path)
        if not self.isfile(path):
            raise NoSuchFile(path)
        return self.store.get(key).decode('utf-8')

    def lstat(self, path):
        key = self.as_key(path)
        if not self.isfile(path):
            raise NoSuchFile(self.as_path(key))

        return {"ST_MTIME": DUMMY_CREATED_DATE}

    def write(self, path, content):
        self.log.debug("S3contents.StorefactFS: Writing file: `%s`", path)
        self.store.put(self.as_key(path), content.encode('utf-8'))

    #  Utilities -------------------------------------------------------------------------------------------------------

    def abspath(self, path):
        """Utility: Return a normalized absolutized version of the pathname path
        Basically prepends the path with the prefix
        """
        path = path.strip("/")
        if self.prefix:
            path = self.join(self.prefix, path)
        return path.strip("/")

    def as_key(self, path):
        """Utility: Make a path a storefact key
        """
        path_ = self.abspath(path)
        self.log.debug("S3contents.StorefactFS: Understanding `%s` as `%s`", path, path_)
        if isinstance(path_, six.string_types):
            return path_.strip(self.separator)
        if isinstance(path_, list):
            return [self.as_key(item) for item in path_]

    def as_path(self, key):
        """Utility: Make a storefact key a path
        """
        key_ = self.remove_prefix(key)
        if isinstance(key_, six.string_types):
            return key_.strip(self.separator)

    def remove_prefix(self, text, prefix=None):
        """Utility: remove a prefix from a string
        """
        if prefix is None:
            prefix = self.prefix
        if text.startswith(prefix):
            return text[len(prefix):].strip("/")
        return text.strip("/")

    def join(self, *args):
        """Utility: join using the separator
        """
        return self.separator.join(args)
