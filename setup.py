import os

from setuptools import find_packages, setup


setup_dir = os.path.abspath(os.path.dirname(__file__))


def read_file(filename):
    filepath = os.path.join(setup_dir, filename)
    with open(filepath) as file:
        return file.read()


setup(
    name="s3contents",
    use_scm_version=True,
    packages=find_packages(),
    # package_dir={"": "src"},
    zip_safe=False,
    include_package_data=True,
    # package_data={"s3contents": ["includes/*"]},
    # data_files=[],
    # cmdclass={},
    # entry_points = {},
    options={"bdist_wheel": {"universal": "1"}},
    python_requires=">=3.7",
    setup_requires=["setuptools_scm"],
    install_requires=read_file("requirements-package.txt").splitlines(),
    extras_require={
        "test": ["pytest", "pytest-cov", "toml"],
        "dev": read_file("requirements.txt").splitlines(),
    },
    description="S3 Contents Manager for Jupyter",
    long_description=read_file("README.md"),
    long_description_content_type="text/markdown",
    license="Apache License, Version 2.0",
    maintainer="Daniel Rodriguez",
    maintainer_email="daniel@danielfrg.com",
    url="https://github.com/danielfrg/s3contents",
    keywords=["jupyter", "s3", "contents-manager"],
    classifiers=[
        "License :: OSI Approved :: Apache Software License",
        "Programming Language :: Python :: 3.7",
        "Programming Language :: Python :: 3.8",
    ],
)
