.. _client_examples:

======================
Python client examples
======================

This section is organised into working Python example pages for the major
services in ``ansys.api.fluent.v1``. Each page focuses on runnable snippets for
that service area, while full message and field listings are in the
:ref:`api_reference`.

The example pages are organised by task: simulation configuration,
session connection and management, live-stream observation, and
simulation data access.

Configuring the simulation
~~~~~~~~~~~~~~~~~~~~~~~~~~

:doc:`DataModel <datamodel_se>` focuses on meshing objects. It covers
discovering meshing paths, reading or writing object state, and running
meshing-side commands.

:doc:`Settings <settings>` focuses on solver configuration. It covers
configuration of boundary conditions, physics models, solver controls, and
result-output settings before or while solving.

Both pages begin with schema discovery so you can identify valid paths and
commands before modifying state.

Connecting and managing the session
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

:doc:`Session setup <session_setup>` contains start-up examples used before
service calls, including connection, readiness checks, and basic session
management.

Observing a running simulation
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

:doc:`Solver streams <solver_streams>` provides live streaming examples for
runtime observation while a simulation is running.

Reading and post-processing results
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

:doc:`Simulation data <simulation_data>` provides data-access examples for
extracting and post-processing solution results.

Shared building blocks
~~~~~~~~~~~~~~~~~~~~~~

:doc:`Helper types <helpers>` documents the ``Variant`` and ``Point`` message
types that appear across multiple services, with examples of how to construct
and unpack them.

.. toctree::
   :hidden:
   :maxdepth: 2

   session_setup
   datamodel_se
   settings
   solver_streams
   simulation_data
   helpers
