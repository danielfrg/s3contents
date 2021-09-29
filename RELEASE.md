# Releasing

## Upload to PyPI

- Update version on `__init__.py`
- Update version on `pyproject.toml`
- Update `CHANGELOG.md`
- Update `README.md`

```shell
export VERSION=1.0.0

# Optional reset
make clean

make all
make upload-pypi

git commit -am "Release ${VERSION}" --allow-empty
git tag ${VERSION}

git push origin ${VERSION}
git push
```
