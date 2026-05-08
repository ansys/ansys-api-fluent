Ansys Fluent gRPC API
======================

.. toctree::
   :hidden:
   :maxdepth: 2

   getting_started/index
   user_guide/index
   api/index
   glossary


The Fluent `gRPC <https://grpc.io/>`_ API is a service-based interface for
driving Fluent programmatically from external clients.
This package provides pre-generated Python stubs for building clients against
this API.
The `repository <https://github.com/ansys-internal/ansys-api-fluent>`_
contains the underlying `.proto files <https://protobuf.dev/overview/>`_,
which are language-independent and can be used to generate native clients in
C++, Go, Java, C#, or any other language with `gRPC <https://grpc.io/>`_ support.

Getting started
---------------

Start with :ref:`getting_started` to understand the API structure,
installation steps, and multi-language examples that highlight the
language-agnostic nature of the proto files.

Python client examples
----------------------

Browse :ref:`client_examples` for the current Python examples covering
client setup, live solver streams, and simulation data access.

API reference
-------------

Use :ref:`api_reference` to look up a specific service, RPC, or message.

Glossary
--------

See :doc:`glossary` for terminology used throughout the documentation.
