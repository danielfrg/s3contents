#!/usr/bin/env python
# -*- coding: utf-8 -*-

import six
from s3contents.ipycompat import HasTraits, Unicode


class BaseFS(HasTraits):
    delimiter = Unicode("/", help="Path delimiter").tag(config=True)
    prefix = Unicode("", help="Prefix path inside the specified bucket").tag(config=True)
    dir_keep_file = Unicode(
        ".s3keep", help="Empty file to create when creating directories").tag(config=True)

    def __init__(self, log, **kwargs):
        super(BaseFS, self).__init__(**kwargs)
        self.log = log

    def get_keys(self, prefix=""):
        raise NotImplementedError

    def isfile(self, path):
        raise NotImplementedError

    def isdir(self, path):
        self.log.debug("S3contents[BaseFS] Checking if `%s` is a directory", path)
        key = self.as_key(path)
        if key == "":
            return True
        if not key.endswith(self.delimiter):
            key = key + self.delimiter
        if key == "":
            return True
        is_dir = len(self.get_keys(prefix=key)) > 0
        self.log.debug("S3contents[BaseFS] `%s` is a directory: %s", path, is_dir)
        return is_dir

    def mv(self, old_path, new_path):
        self.cp(old_path, new_path)
        self.rm(old_path)

    def cp(self, old_path, new_path):
        raise NotImplementedError

    def rm(self, path):
        raise NotImplementedError

    def mkdir(self, path):
        self.log.debug("S3contents[BaseFS] Making dir: `%s`", path)
        if self.isfile(path):
            self.log.debug("S3contents[BaseFS] File `%s` already exists, not creating anything", path)
        elif self.isdir(path):
            self.log.debug("S3contents[BaseFS] Directory `%s` already exists, not creating anything",
                           path)
        else:
            obj_path = self.join(path, self.dir_keep_file)
            self.write(obj_path, "")

    def read(self, path):
        raise NotImplementedError

    def write(self, path, content):
        raise NotImplementedError

    def listdir(self, path="", with_prefix=False):
        self.log.debug("S3contents[BaseFS] Listing directory: `%s`", path)
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

    def as_key(self, path):
        """Utility: Make a path a S3 key
        """
        path_ = self.abspath(path)
        self.log.debug("S3contents[BaseFS] Understanding `%s` as `%s`", path, path_)
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


class NoSuchFileException(Exception):
    def __init__(self, path, *args):
        super(NoSuchFileException, self).__init__(*args)
        self.path = path
