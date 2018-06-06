import os
from distutils.core import setup
from setuptools import find_packages

import versioneer


def read_file(filename):
    filepath = os.path.join(
        os.path.dirname(os.path.dirname(__file__)), filename)
    if os.path.exists(filepath):
        return open(filepath).read()
    else:
        return ''

REQUIREMENTS = read_file("requirements.txt").splitlines()


setup(
    name="s3contents",
    version=versioneer.get_version(),
    cmdclass=versioneer.get_cmdclass(),
    description="A S3-backed ContentsManager implementation for Jupyter",
    long_description=read_file('README.md'),
    long_description_content_type="text/markdown",
    url="https://github.com/danielfrg/s3contents",
    maintainer="Daniel Rodriguez",
    maintainer_email="df.rodriguez143@gmail.com",
    license="Apache 2.0",
    packages=find_packages(),
    install_requires=REQUIREMENTS,
    zip_safe=False,
)
