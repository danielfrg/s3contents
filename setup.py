import versioneer

from distutils.core import setup
from setuptools import find_packages

with open("requirements.txt") as f:
    requirements = f.read().splitlines()

setup(
    name="s3contents",
    version=versioneer.get_version(),
    cmdclass=versioneer.get_cmdclass(),
    description="A S3-backed ContentsManager implementation for Jupyter",
    url="https://github.com/danielfrg/s3contents",
    maintainer="Daniel Rodriguez",
    maintainer_email="df.rodriguez143@gmail.com",
    license="Apache 2.0",
    packages=find_packages(),
    install_requires=requirements,
    zip_safe=False,
)
