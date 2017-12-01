import s3fs

try:
    FileNotFoundError = s3fs.core.FileNotFoundError
except:
    class FileNotFoundError(IOError):
        pass
