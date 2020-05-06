import os
import sys

from setuptools import find_packages, setup

setup_dir = os.path.abspath(os.path.dirname(__file__))


def read_file(filename):
    this_dir = os.path.abspath(os.path.dirname(__file__))
    filepath = os.path.join(this_dir, filename)
    with open(filepath) as file:
        return file.read()


def parse_git(root, **kwargs):
    """
    Parse function for setuptools_scm that ignores tags for non-C++
    subprojects, e.g. apache-arrow-js-XXX tags.
    """
    from setuptools_scm.git import parse

    kwargs["describe_command"] = "git describe --dirty --tags --long"
    return parse(root, **kwargs)


setup(
    name="s3contents",
    packages=find_packages() + ["s3contents.tests"],
    zip_safe=False,
    include_package_data=True,
    # package_data={"s3contents": ["includes/*"]},
    # data_files=[],
    # cmdclass={},
    # entry_points = {},
    use_scm_version={
        "root": setup_dir,
        "parse": parse_git,
        "write_to": os.path.join("s3contents/_generated_version.py"),
    },
    test_suite="s3contents/tests",
    setup_requires=["setuptools_scm"],
    install_requires=read_file("requirements.package.txt").splitlines(),
    tests_require=["pytest"],
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
