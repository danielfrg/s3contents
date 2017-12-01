"""
Generic FileSystem class to be used by the Content Manager
"""

from s3contents.ipycompat import HasTraits


class GenericFS(HasTraits):

    def ls(self, path="", with_prefix=False):
        raise NotImplemented("Should be implemented")

    def isfile(self, path):
        raise NotImplemented("Should be implemented")

    def isdir(self, path):
        raise NotImplemented("Should be implemented")

    def mv(self, old_path, new_path):
        raise NotImplemented("Should be implemented")

    def cp(self, old_path, new_path):
        raise NotImplemented("Should be implemented")

    def rm(self, path):
        raise NotImplemented("Should be implemented")

    def mkdir(self, path):
        raise NotImplemented("Should be implemented")

    def read(self, path):
        raise NotImplemented("Should be implemented")

    def lstat(self, path):
        raise NotImplemented("Should be implemented")

    def write(self, path, content):
        raise NotImplemented("Should be implemented")


class GenericFSError(Exception):
    pass


class NoSuchFile(GenericFSError):

    def __init__(self, path, *args, **kwargs):
        self.path = path
        self.message = "No such file or directory: {}".format(path)
        super(NoSuchFile, self).__init__(self.message, *args, **kwargs)
