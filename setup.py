import os
import sys

import versioneer
from setuptools import find_packages, setup


def read_file(filename):
    this_dir = os.path.abspath(os.path.dirname(__file__))
    filepath = os.path.join(this_dir, filename)
    with open(filepath) as file:
        return file.read()

setup(
    name="s3conents",
    version=versioneer.get_version(),
    description="",
    long_description=read_file("README.md"),
    long_description_content_type="text/markdown",
    author="Daniel Rodriguez",
    author_email="daniel@danielfrg.com",
    url="https://github.com/danielfrg/s3contents",
    license="Apache 2.0",
    python_requires=">=3.0,!=3.0.*,!=3.1.*,!=3.2.*,!=3.3.*,!=3.4.*",
    install_requires=read_file("requirements.package.txt").splitlines(),
    keywords=["jupyter", "s3", "contents-manager"],
    packages=find_packages(),
    include_package_data=True,
    zip_safe=False,
    cmdclass=versioneer.get_cmdclass(),
    entry_points = {},
)
