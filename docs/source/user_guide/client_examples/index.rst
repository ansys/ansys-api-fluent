.. _client_examples:

======================
Python client examples
======================

These pages walk through working Python examples for every major service in
``ansys.api.fluent.v1``. Each page focuses on runnable code; full message and
field listings are in the :ref:`api_reference`.

A typical workflow starts by configuring the simulation, then running it while
observing live output, and finally reading or post-processing the results.

**Configuring the simulation**

The :doc:`DataModel <datamodel_se>` and :doc:`Settings <settings>` services
are the two primary ways to read and write Fluent's internal state. They share
the same core RPC names — ``GetSchema``, ``GetState``, ``SetState``,
``CreateObject``, ``DeleteObject``, ``ExecuteCommand``, and ``ExecuteQuery`` —
but address different domains: DataModel owns the meshing and workflow object
tree (identified by a *rules* string such as ``"meshing"`` and a slash-separated
path), while Settings owns the solver configuration hierarchy (boundary
conditions, physics models, solver controls, and results settings, rooted at
``"fluent"``). Start with the schema discovery examples in either page to
understand what paths and commands are available before writing any state.

**Connecting and managing the session**

:doc:`Session setup <session_setup>` covers everything needed before issuing
simulation calls: authenticating the gRPC channel, verifying that the server is
ready, and using the ApplicationRuntime service to query the running process,
enable beta features, set a working directory, and record a journal.

**Observing a running simulation**

Once the solver is running, :doc:`Solver streams <solver_streams>` shows how to
tap into three complementary live feeds: the raw Fluent console transcript (line
by line in a background thread), typed lifecycle events (iteration ends, time
steps, pause/resume, and errors) decoded with ``WhichOneof``, and per-iteration
monitor data (residuals and solution monitors) streamed from the Monitor service.
The page ends with an end-to-end example that runs all three streams concurrently.

**Reading and post-processing results**

:doc:`Simulation data <simulation_data>` covers the three services for
extracting numbers from a converged or in-progress solution. Start by
discovering available surfaces and scalar/vector fields via FieldData, stream
field arrays off surfaces, then use the Reduction service to compute aggregated
quantities (area averages, force decompositions, conditional sums) without
streaming raw arrays. For direct access to solver internals, SolutionVariable
lets you read and write per-zone arrays by name (e.g. ``SV_P``, ``SV_U``).

**Shared building blocks**

:doc:`Helper types <helpers>` documents the ``Variant`` and ``Point`` message
types that appear across multiple services, with examples of how to construct
and unpack them.

.. list-table::
   :widths: 25 75
   :header-rows: 1

   * - Page
     - Contents
   * - :doc:`DataModel <datamodel_se>`
     - Read/write access to Fluent's meshing, preferences, and workflow object tree via a
       rules context and slash-separated path.
   * - :doc:`Settings <settings>`
     - Read/write access to solver configuration: boundary conditions, physics
       models, solver controls, and results settings.
   * - :doc:`Session setup <session_setup>`
     - Connect to a running Fluent server, verify health, and manage the
       session (version, mode, journal recording, exit).
   * - :doc:`Solver streams <solver_streams>`
     - Stream live console output, typed solver lifecycle events, and
       per-iteration monitor data from a running simulation.
   * - :doc:`Simulation data <simulation_data>`
     - Stream surface fields, compute aggregated reductions, and read or write
       raw per-zone solution variable arrays.
   * - :doc:`Helper types <helpers>`
     - Construct and unpack the ``Variant`` and ``Point`` types used across
       multiple services.

.. toctree::
   :hidden:
   :maxdepth: 2

   session_setup
   datamodel_se
   settings
   solver_streams
   simulation_data
   helpers
