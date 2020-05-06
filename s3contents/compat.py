import s3fs
import six

if six.PY3:
    FileNotFoundError = FileNotFoundError
else:
    try:
        FileNotFoundError = s3fs.core.FileNotFoundError
    except:

        class FileNotFoundError(IOError):
            pass
