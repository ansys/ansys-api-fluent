Ansys Fluent gRPC API
=====================

.. toctree::
   :hidden:
   :maxdepth: 2

   getting_started/index
   user_guide/index
   api/index
   glossary

This package provides the gRPC interface for Ansys Fluent with pre-generated
Python stubs for building a client. The underlying ``.proto`` files are
language-independent and can be used to generate native clients in C++, Go,
Java, C#, or any other language with gRPC support.

**New here?** Start with :ref:`getting_started` — it explains how the API is
structured, walks you through installation, and includes examples in multiple
languages to illustrate the language-agnostic nature of the ``.proto`` files.

**Ready to build?** Read :doc:`user_guide/build_a_client` to understand the
DataModel and Settings services — the two you need for a minimal working client.
Then browse the :ref:`client_examples` for annotated Python examples covering
session setup, live solver streams, and simulation data access.

**Looking up a specific service, RPC, or message?** Go straight to the
:ref:`api_reference`.

**Unfamiliar with a term?** See the :doc:`glossary`.
