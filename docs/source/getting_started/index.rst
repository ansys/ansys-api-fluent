.. _getting_started:

===============
Getting started
===============

The two guides below cover what you need. Start with the API overview to understand how the services
are structured, then follow the installation guide to make your first calls against
a running Fluent server.

:doc:`fluent_grpc_api`
   How the API is organised: the DataModel and Settings services and their
   shared design, the other single-purpose services, path-addressing
   conventions, and the schema versus runtime distinction.

:doc:`installation_and_first_call`
   Package installation, prerequisites, and your first RPC call. Includes
   proto compilation commands and a health-check example in Python, C++, Go,
   Java, and C# to illustrate the language-agnostic nature of the API.

.. toctree::
   :hidden:
   :maxdepth: 2

   fluent_grpc_api
   installation_and_first_call
