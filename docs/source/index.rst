======================
Ansys Fluent gRPC API
======================

.. toctree::
   :hidden:
   :maxdepth: 2

   getting_started/index
   user_guide/index
   api/index

Drive Fluent programmatically from any language.
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

The Ansys Fluent gRPC API exposes services and RPC methods for driving Fluent
programmatically from external clients. The
`repository <https://github.com/ansys/ansys-api-fluent>`_ contains
`.proto <https://protobuf.dev/overview/>`_ files that are language‑agnostic
and can be used to generate clients in C++, Go, Java, C#, or any other language
with gRPC support. Pre-generated `Python stubs <https://pypi.org/project/ansys-api-fluent/>`_
are provided for building Python clients.

.. note::

   This documentation covers the **gRPC package v1** only:

   - v1 is compatible with **Fluent 27R1 and later**
   - v1 is the target for all new development -- use the ``ansys.api.fluent.v1`` package
   - v0 is retained solely for backwards compatibility with existing clients; it is neither documented nor supported



.. |getting-started-label| raw:: html

   <big><strong>Getting started</strong></big>

|getting-started-label| -- see the :ref:`getting_started` page for an overview of the API structure,
installation steps, and multi-language examples.

**Python client examples** — browse the :ref:`client_examples`, which include simulation setup,
live solver streams, and simulation data access.

**API reference** — use the :ref:`api_reference` to look up a service, its methods,
and the corresponding request and response messages.
