.. _user_guide:

.. _client_examples:

======================
Python client examples
======================

This page provides runnable code examples for the services in
``ansys.api.fluent.v1``.
Full message and field listings are in the :ref:`api_reference`.

.. include:: ../../shared_example_assumptions.rst

Connecting and managing the session
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

See :doc:`session_setup` for health checks, version negotiation, product and
build info, process info, app mode, beta features, and Python journalling via
the ``Health``, ``Connection``, and ``ApplicationRuntime`` services.

Configuring the simulation
~~~~~~~~~~~~~~~~~~~~~~~~~~~

Use :doc:`object_model` to discover the schema, then read and write object
state, run commands, and stream events via the meshing-oriented ``ObjectModel``
service.

Use :doc:`settings` to discover the schema, then read and write solver state,
manage named objects, and call commands and queries via the solver-oriented
``Settings`` service.

Observing a running simulation
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

See :doc:`solver_streams` to open, read, filter, and cancel live streams for
console output (``Transcript``), typed solver lifecycle events (``Events``),
and per-iteration monitor samples (``Monitor``).

Reading and post-processing results
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

See :doc:`simulation_data` for field data availability, surface and field
enumeration, scalar and vector field streaming, reductions, and
solution-variable read/write via ``FieldData``, ``Reduction``, and
``SolutionVariable``.

Shared building blocks
~~~~~~~~~~~~~~~~~~~~~~~~

See :doc:`helpers` for constructing and unpacking the ``Variant`` and
``Point`` messages used across multiple services.

.. toctree::
   :hidden:
   :maxdepth: 2

   session_setup
   object_model
   settings
   solver_streams
   simulation_data
   helpers
