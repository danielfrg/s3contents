"""
Generic FileSystem class to be used by the Content Manager
"""

from s3contents.ipycompat import HasTraits


class GenericFS(HasTraits):
    def ls(self, path=""):
        raise NotImplementedError(
            "Should be implemented by the file system abstraction"
        )

    def isfile(self, path):
        raise NotImplementedError(
            "Should be implemented by the file system abstraction"
        )

    def isdir(self, path):
        raise NotImplementedError(
            "Should be implemented by the file system abstraction"
        )

    def mv(self, old_path, new_path):
        raise NotImplementedError(
            "Should be implemented by the file system abstraction"
        )

    def cp(self, old_path, new_path):
        raise NotImplementedError(
            "Should be implemented by the file system abstraction"
        )

    def rm(self, path):
        raise NotImplementedError(
            "Should be implemented by the file system abstraction"
        )

    def mkdir(self, path):
        raise NotImplementedError(
            "Should be implemented by the file system abstraction"
        )

    def read(self, path, format):
        raise NotImplementedError(
            "Should be implemented by the file system abstraction"
        )

    def lstat(self, path):
        raise NotImplementedError(
            "Should be implemented by the file system abstraction"
        )

    def write(self, path, content, format):
        raise NotImplementedError(
            "Should be implemented by the file system abstraction"
        )


class GenericFSError(Exception):
    pass


class NoSuchFile(GenericFSError):
    def __init__(self, path, *args, **kwargs):
        self.path = path
        self.message = "No such file or directory: {}".format(path)
        super(NoSuchFile, self).__init__(self.message, *args, **kwargs)
