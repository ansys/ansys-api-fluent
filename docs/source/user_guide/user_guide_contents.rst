.. _user_guide:

==========
User guide
==========

The user guide covers practical, task-oriented workflows. Each guide targets a
different audience — choose the one that fits your use case.

.. list-table::
   :widths: 30 70
   :header-rows: 1

   * - Guide
     - Audience and scope
   * - :doc:`build_a_client`
     - **Start here.** A six-step guide to connecting to a live Fluent server,
       calling ``GetSchema`` to discover available paths, reading and writing
       simulation state with ``GetState``/``SetState`` and ``GetVar``/``SetVar``,
       and subscribing to solver events via ``BeginStreaming``.
   * - :doc:`building_on_the_api`
     - **For tool and library authors.** Explains the API schema as a
       machine-readable contract independent of any running session — covering
       how to introspect path hierarchies, parameter types, commands, and
       constraints to generate stubs or build abstractions across services.

.. toctree::
   :hidden:
   :maxdepth: 2

   build_a_client
   building_on_the_api
