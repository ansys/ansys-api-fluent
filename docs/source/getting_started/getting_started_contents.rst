.. _getting_started:

===============
Getting started
===============

This section is your entry point to the Fluent gRPC API. Read the API overview
first to understand how the service hierarchy is structured, then follow the
installation guide to make your first calls against a running Fluent server.

.. list-table::
   :widths: 30 70
   :header-rows: 1

   * - Guide
     - What you will learn
   * - :doc:`fluent_grpc_api`
     - How the API is organised: the two high-level surfaces (DataModel and
       Settings), path-addressing conventions, and runtime versus schema
       concepts.
   * - :doc:`gettingstarted`
     - Package installation, channel setup, health-check verification, and
       your first RPC call. Also covers :ref:`using the API from other languages
       <other-languages>` such as C++, Go, Java, and C# by generating stubs
       directly from the ``.proto`` source files.

.. toctree::
   :hidden:
   :maxdepth: 2

   fluent_grpc_api
   gettingstarted
