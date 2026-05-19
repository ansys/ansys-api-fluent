.. _client_examples:

======================
Python client examples
======================

Runnable code examples for the major services in ``ansys.api.fluent.v1``.
Full message and field listings are in the :ref:`api_reference`.

For the two generic configuration services, the workflow is the same: use
``GetSchema`` to discover the service shape first, then call the relevant RPC
methods to read state, write state, run commands, or issue queries. Use
``DataModel`` for meshing-oriented object trees and ``Settings`` for
solver-oriented paths.

Connecting and managing the session
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

:doc:`Session setup <session_setup>` — health checks, version negotiation,
product and build info, process info, app mode, beta features, and Python
journalling via the ``Health``, ``Connection``, and ``AppUtilities`` services.

Configuring the simulation
~~~~~~~~~~~~~~~~~~~~~~~~~~~

:doc:`DataModel <datamodel_se>` — schema discovery, reading and writing
object state, parameter attributes, commands, command arguments, and event
and state-change streaming via the meshing-oriented ``DataModel`` service.

:doc:`Settings <settings>` — schema discovery, reading and writing solver
state, named-object management, list sizes, commands, queries, and wildcard
checks via the solver-oriented ``Settings`` service.

Observing a running simulation
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

:doc:`Solver streams <solver_streams>` — opening, reading, filtering, and
cancelling live streams for console output (``Transcript``), typed solver
lifecycle events (``Events``), and per-iteration monitor samples (``Monitor``);
also covers pause/resume registration.

Reading and post-processing results
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

:doc:`Simulation data <simulation_data>` — field data availability, surface
and field enumeration, scalar and vector field streaming, geometric and
statistical reductions, force decomposition, conditional sums, and
solution-variable read/write via ``FieldData``, ``Reduction``, and
``SolutionVariable``.

Shared building blocks
~~~~~~~~~~~~~~~~~~~~~~~~

:doc:`Helper types <helpers>` — constructing and unpacking the ``Variant`` and
``Point`` messages used across multiple services.

.. toctree::
   :hidden:
   :maxdepth: 2

   session_setup
   datamodel_se
   settings
   solver_streams
   simulation_data
   helpers
