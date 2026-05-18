Ansys Fluent gRPC API
======================

.. toctree::
   :hidden:
   :maxdepth: 2

   getting_started/index
   user_guide/index
   api/index

The Ansys Fluent gRPC API exposes services and RPC methods for driving Fluent
programmatically from external clients. The
`repository <https://github.com/ansys-internal/ansys-api-fluent>`_ contains the
language-agnostic `.proto files <https://protobuf.dev/overview/>`_ used to
generate clients in C++, Go, Java, C#, Python, and other languages with
`gRPC <https://grpc.io/>`_ support. The
`Python package <https://pypi.org/project/ansys-api-fluent/>`_ provides
pre-generated Python stubs for building Python clients.

- :ref:`getting_started` provides an overview of the API structure, installation
  steps, proto compilation, and a minimal multi-language example.
- :ref:`user_guide` provides task-oriented Python client examples for session
  setup, configuration workflows, live solver streams, and simulation data
  access.
- :ref:`api_reference` documents every service, RPC method, and request/response
  message in detail.
