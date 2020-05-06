import os
import sys

from setuptools import find_packages, setup


def read_file(filename):
    this_dir = os.path.abspath(os.path.dirname(__file__))
    filepath = os.path.join(this_dir, filename)
    with open(filepath) as file:
        return file.read()


setup(
    name="s3contents",
    packages=find_packages() + ["s3contents.tests"],
    zip_safe=False,
    include_package_data=True,
    # package_data={"word2vec": ["includes/**/*.c"]},
    # data_files=data_files,
    # cmdclass={},
    # entry_points = {},
    test_suite="word2vec/tests",
    setup_requires=["setuptools_scm"],
    install_requires=read_file("requirements.package.txt").splitlines(),
    tests_require=["pytest",],
    python_requires=">=3.5",
    description="S3 Contents Manager for Jupyter",
    long_description=read_file("README.md"),
    long_description_content_type="text/markdown",
    license="Apache License, Version 2.0",
    maintainer="Daniel Rodriguez",
    maintainer_email="daniel@danielfrg.com",
    url="https://github.com/danielfrg/s3contents",
    classifiers=[
        "License :: OSI Approved :: Apache Software License",
        "Programming Language :: Python :: 3.6",
        "Programming Language :: Python :: 3.7",
        "Programming Language :: Python :: 3.8",
    ],
    keywords=["jupyter", "s3", "contents-manager"],
)
