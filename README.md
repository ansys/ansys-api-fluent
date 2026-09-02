# ansys-api-fluent

This repository contains the [Protocol Buffer](https://protobuf.dev/overview/) (`.proto`) definition files for the [Ansys Fluent](https://www.ansys.com/products/fluids/ansys-fluent) gRPC API, along with pre-generated Python stubs published as the [`ansys-api-fluent`](https://pypi.org/project/ansys-api-fluent/) PyPI package.

> **Note:** This repository targets the **v1 API**, compatible with **Fluent 27R1 and later**.
> The `v0` directory is retained for backwards compatibility only and is not supported.

## Documentation

Full documentation — getting started, API reference, and client examples — is available at:

**<https://api.fluent.docs.pyansys.com>**

## Installation (Python)

```bash
pip install ansys-api-fluent
```

## Build documentation locally

```bash
pip install -r requirements/requirements_docs.txt
cd docs && make html
```
