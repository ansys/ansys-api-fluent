Building a Fluent client
========================

This guide walks through the pattern for building a client against the Fluent
gRPC API: connecting to the server, discovering what the API exposes, reading
and writing state, and reacting to solver events. Each step points to the
relevant :doc:`client examples <client_examples/index>` for runnable code.

.. note::

   The ``.proto`` files in this package are language-agnostic. You can
   generate a client for any language gRPC supports — Go, Java, C++, and
   others. The client examples use Python for concreteness, but the RPC names
   and message structures are the same in every language.

.. include:: ../shared_example_assumptions.rst

Overview
--------

Fluent primarily exposes two services for reading and writing simulation
configuration:

:doc:`DataModel <../api/services/datamodel_se>`
   Hierarchical access to Fluent's object model — meshing workflows, guided
   workflows, and preferences. Each call identifies the application with a
   **rules** string and a slash-separated **path** within it.

:doc:`Settings <../api/services/settings>`
   Hierarchical access to the Fluent solver — boundary conditions, solver
   controls, model parameters, and results settings. Calls identify locations
   with a **root** string (typically ``fluent``) and a slash-separated **path**.

Both services follow the same two-step pattern: call ``GetSchema`` to discover
what paths and operations exist, then call the read/write RPCs using those
paths.

Step 1 — Connect and verify server health
-----------------------------------------

Before making any other call, open a gRPC channel and confirm the server is
ready using the :doc:`Health <../api/services/health>` service ``Check`` RPC.

See the :doc:`Health client example <client_examples/health>` for
code.

Step 2 — Discover the schema
-----------------------------

Both the DataModel and Settings services expose a ``GetSchema`` RPC. Call it
once to learn what paths, parameter types, commands, and queries are available
before reading or writing any live data.

**When to call it.** Call ``GetSchema`` once when your client initialises and
cache the result. The schema is stable across sessions — it describes the
structure of the API for a given Fluent version, not any runtime state. There
is no need to re-fetch it per session.

**What it returns.** The response describes the full structure of the service
— what exists at each path, what operations are available, and what types
apply. Full details are in the :doc:`DataModel <../api/services/datamodel_se>`
and :doc:`Settings <../api/services/settings>` API references.

See the schema sections of the
:doc:`DataModel client example <client_examples/datamodel_se>` and
:doc:`Settings client example <client_examples/settings>` for code.

Step 3 — Read and write state
------------------------------

For the **DataModel service**, use ``GetState`` and ``SetState`` with the rules
string and a path discovered from the schema. State values are carried in
:doc:`Variant <../api/helpers/variant>` messages. Use ``ExecuteCommand`` to run
a command at a path, passing arguments as a ``Variant`` map.

For the **Settings service**, use ``GetVar`` and ``SetVar`` with a ``PathInfo``
message. Values are carried in ``Value`` messages. Named objects such as
boundary conditions are managed with ``Create``, ``Rename``, ``Delete``, and
``GetObjectNames``. The Settings service also supports ``GetAttrs`` for
retrieving metadata (type, allowed values, read-only flag) at any path without
a prior ``GetSchema`` call.

See the state read/write and object lifecycle sections of the
:doc:`DataModel client example <client_examples/datamodel_se>` and
:doc:`Settings client example <client_examples/settings>` for code.

Step 4 — React to solver events
---------------------------------

The :doc:`Events <../api/services/events>` service ``BeginStreaming`` RPC
returns a server-side stream of solver lifecycle notifications. Iterate over it
while your solver runs to receive iteration, time-step, and completion events.
For deterministic per-iteration or per-time-step callbacks that pause and resume
the solver, use the ``PauseSolveFor``, ``ResumeSolve``, and ``UnregisterPause``
RPCs on the same service.

See the :doc:`Events client example <client_examples/events>` for
code.

Building on the schema
-----------------------

The schema is also useful as a build-time or startup-time foundation for
generating a complete, typed client API. The general approach is:

1. Fetch ``GetSchema`` from a reference server (or embed the serialised
   response as a build artefact).
2. Walk the returned tree. For the DataModel service: each singleton or
   named-object node becomes a class, each parameter a typed property, each
   command a method. For the Settings service: each group node becomes a class,
   each leaf a typed property.
3. Emit the generated source with path constants embedded so application code
   never constructs path strings manually.
4. Re-run the generator when the server version changes.

This is how PyFluent is built: the ``Schema`` responses were consumed by a
code generator that emitted the full Python class hierarchy. External developers
can use the same approach for any language.

Next steps
----------

- :doc:`../api/services/datamodel_se` — DataModel service reference
- :doc:`../api/services/settings` — Settings service reference
- :doc:`../api/services/events` — event types and solver pause callbacks
- :doc:`../api/services/field_data` — streaming mesh geometry and field values
- :doc:`../api/services/health` — Health service reference
