import os

from notebook.auth import passwd
from s3contents import S3ContentsManager

c = get_config()

# Tell Jupyter to use S3ContentsManager for all storage.
c.NotebookApp.contents_manager_class = S3ContentsManager
c.S3ContentsManager.access_key_id = os.environ["AWS_ACCESS_KEY_ID"]
c.S3ContentsManager.secret_access_key = os.environ["AWS_SECRET_ACCESS_KEY"]
#c.S3ContentsManager.session_token = "<AWS Session Token / IAM Session Token>"
c.S3ContentsManager.bucket = os.environ["S3_BUCKET"]

# Optional settings:
c.S3ContentsManager.prefix = os.environ.get("S3_PREFIX", "notebooks/")
#c.S3ContentsManager.signature_version = "s3v4"

## Whether to open in a browser after starting. The specific browser used is
#  platform dependent and determined by the python standard library `webbrowser`
#  module, unless it is overridden using the --browser (NotebookApp.browser)
#  configuration option.
c.NotebookApp.open_browser = False

## Hashed password to use for web authentication.
#
#  To generate, type in a python/IPython shell:
#
#    from notebook.auth import passwd; passwd()
#
#  The string should be of the form type:salt:hashed-password.
c.NotebookApp.password = passwd(os.environ["JUPYTER_PASSWORD"])
