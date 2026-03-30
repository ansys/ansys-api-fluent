### ansys-api-fluent gRPC Interface Package

This Python package contains the auto-generated gRPC Python interface files for
Fluent.


#### User Documentation

For a complete step-by-step guide to use the packaged Fluent v1 Python gRPC
interface and build a client, see:

- [User Guide](ansys/api/fluent/v1/USER_GUIDE.md) - Quick start guide
- [Full Documentation](docs/source/index.rst) - Complete API documentation with examples for all services

The full documentation includes:

- Getting started tutorials
- Service-specific guides with code examples
- Complete API reference for all v1 services
- Best practices and common patterns


#### Installation

Provided that these wheels have been published to public PyPI, they can be
installed with:

```
pip install ansys-api-fluent
```

Otherwise, see the


#### Build

To build the gRPC packages, run:

```
pip install build
python -m build
```

This will create both the source distribution containing just the protofiles
along with the wheel containing the protofiles and build Python interface
files.

Note that the interface files are identical regardless of the version of Python
used to generate them, but the last pre-built wheel for ``grpcio~=1.30`` was
Python 3.7, so to improve your build time, use Python 3.7 when building the
wheel.


#### Build Documentation

To build the documentation locally, install the documentation dependencies and run make:

```bash
pip install -r docs/requirements.txt
cd docs
make html
```

The built HTML documentation will be in ``docs/_build/html/``. Open ``index.html`` in a web browser to view it.


#### Manual Deployment

After building the packages, manually deploy them with:

```
pip install twine
twine upload dist/*
```

Note that this is automatically done through CI/CD.


#### Automatic Deployment

This repository contains GitHub CI/CD that enables the automatic building of
source and wheel packages for these gRPC Python interface files. By default,
these are built on PRs, the main branch, and on tags when pushing. Artifacts
are uploaded for each PR.

To publicly release wheels to PyPI, ensure your branch is up-to-date and then
push tags. For example, for the version ``v0.5.0``.

```bash
git tag v0.5.0
git push --tags
```
