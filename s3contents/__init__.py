try:
    from ._generated_version import version as __version__
except ImportError:
    # Package is not installed, parse git tag at runtime
    try:
        import setuptools_scm

        # Code duplicated from setup.py to avoid a dependency on each other
        def parse_git(root, **kwargs):
            """
            Parse function for setuptools_scm
            """
            from setuptools_scm.git import parse

            kwargs[
                "describe_command"
            ] = "git describe --dirty --tags --long --match '*[0-9]*'"
            return parse(root, **kwargs)

        __version__ = setuptools_scm.get_version("./", parse=parse_git)
    except ImportError:
        __version__ = None

from .gcsmanager import GCSContentsManager  # noqa
from .s3manager import S3ContentsManager  # noqa


# We need this try/except here for tests to work
try:
    # This is needed for notebook 5.0, 5.1, 5.2(maybe)
    # https://github.com/jupyter/notebook/issues/2798
    import notebook.transutils  # noqa
except ImportError:
    # Will fail in notebook 4.X - its ok
    pass
