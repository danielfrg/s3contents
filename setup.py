import os
from setuptools import setup
from setuptools import find_packages

import versioneer

BASE_DIR = os.path.abspath(os.path.dirname(__file__))

def read_file(filename):
    filepath = os.path.join(BASE_DIR, filename)
    with  open(filepath) as f:
        return f.read()


setup(
    name="s3contents",
    version=versioneer.get_version(),
    description="A S3-backed ContentsManager implementation for Jupyter",
    long_description=read_file("README.md"),
    long_description_content_type="text/markdown",
    url="https://github.com/danielfrg/s3contents",
    maintainer="Daniel Rodriguez",
    maintainer_email="df.rodriguez143@gmail.com",
    license="Apache 2.0",
    python_requires=">=3.0,!=3.0.*,!=3.1.*,!=3.2.*,!=3.3.*,!=3.4.*",
    install_requires=read_file("requirements.txt").splitlines(),
    keywords=["jupyter", "s3", "contents-manager"],
    packages=find_packages(),
    include_package_data=True,
    zip_safe=False,
    cmdclass=versioneer.get_cmdclass()
)
