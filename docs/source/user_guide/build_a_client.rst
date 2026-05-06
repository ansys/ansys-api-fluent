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

Fluent exposes two primary services for reading and writing simulation
configuration: :doc:`DataModel <../api/services/datamodel_se>` and
:doc:`Settings <../api/services/settings>`. They serve different domains but
share a deliberately parallel design — the same RPC names appear in both,
making it straightforward to transfer knowledge from one to the other.

:doc:`DataModel <../api/services/datamodel_se>`
   Hierarchical access to Fluent's **meshing, guided workflows, and
   preferences**. Each call identifies the application context with a
   **rules** string and a slash-separated **path** within it.

:doc:`Settings <../api/services/settings>`
   Hierarchical access to the **Fluent solver** — boundary conditions, solver
   controls, model parameters, and results settings. Calls identify locations
   with a ``PathInfo`` message carrying a **root** string (typically
   ``"fluent"``) and a slash-separated **path**.

The parallel design means that once you know how to use one service you
already understand the other. Both expose ``GetSchema``, ``GetState``,
``SetState``, ``Rename``, ``CreateObject``, ``DeleteObject``,
``GetObjectNames``, ``ExecuteCommand``, and ``ExecuteQuery`` with the same
intent. The differences are in the domains they cover and a handful of
service-specific RPCs described below.

Step 1 — Connect and verify server health
-----------------------------------------

Before making any other call, open a gRPC channel and confirm the server is
ready using the :doc:`Health <../api/services/health>` service ``Check`` RPC.

See the :doc:`Health client example <client_examples/health>` for code.

Step 2 — Discover the schema
-----------------------------

Both the DataModel and Settings services expose a ``GetSchema`` RPC that
returns the full static structure of the service — every path, type, command,
and query available for a given Fluent version.

**When to call it.** Call ``GetSchema`` once when your client initialises and
cache the result. The schema is stable across sessions and does not reflect
runtime state, so there is no need to re-fetch it per session.

**What it returns.** The ``Schema`` message describes the object at the
requested root, together with its children, commands, queries, and argument
types, recursively. For the DataModel service the tree represents meshing and
workflow objects; for the Settings service it represents solver groups and
named-object collections such as boundary conditions.

See the schema sections of the
:doc:`DataModel client example <client_examples/datamodel_se>` and
:doc:`Settings client example <client_examples/settings>` for code.

Step 3 — Read and write state
------------------------------

The read/write RPCs have identical names in both services. The difference is in
how paths are addressed and how values are represented.

**DataModel** (meshing workflows and preferences)
   - Address objects with a **rules** string (identifies the application) and a
     slash-separated **path** within it.
   - State values are carried in :doc:`Variant <../api/helpers/variant>`
     messages, which can hold a scalar, a list, or a nested map.
   - Use ``GetState`` / ``SetState`` for reading and writing a single path, and
     ``UpdateDict`` to merge a partial dictionary into state without overwriting
     unchanged keys.
   - Use ``GetAttributeValue`` to read a single named attribute at a path
     without fetching the entire state subtree.
   - Use ``FixState`` when the datamodel indicates an inconsistency and the
     solver needs to reconcile the object tree.

**Settings** (solver — boundary conditions, models, controls)
   - Address objects with a ``PathInfo`` message that carries a **root** string
     and a slash-separated **path**.
   - State values are carried in ``Value`` messages, which can hold a boolean,
     integer, real, string, list, or map.
   - Use ``GetState`` / ``SetState`` for reading and writing a single path.
   - Use ``GetAttrs`` to retrieve metadata — type, allowed values, read-only
     flag — at any path without a prior ``GetSchema`` call. This is useful for
     runtime validation.
   - Use ``IsWildcard`` to check whether a string will be interpreted as a
     wildcard by the solver before passing it to other RPCs.

**Object lifecycle — shared pattern.** Both services manage named objects
(boundary conditions, workflow objects, etc.) through the same set of RPCs:
``CreateObject``, ``DeleteObject``, ``Rename``, and ``GetObjectNames``. The
request messages carry the same logical fields — a path to the parent container
and, where applicable, a name — with the addressing convention (rules/path vs
PathInfo) being the only structural difference. The Settings service
additionally provides ``GetListSize`` and ``ResizeListObject`` for fixed-size
list objects that have no DataModel equivalent.

**Commands and queries — shared pattern.** Both services expose
``ExecuteCommand`` and ``ExecuteQuery`` RPCs. Pass the path of the object, the
name of the command or query, and any arguments. The DataModel service also
supports ``CreateCommandArguments`` and ``DeleteCommandArguments`` for building
up command argument objects incrementally before executing the command, which is
useful when arguments are complex or populated in stages.

See the state read/write and object lifecycle sections of the
:doc:`DataModel client example <client_examples/datamodel_se>` and
:doc:`Settings client example <client_examples/settings>` for code.

Step 4 — React to state changes and solver events
--------------------------------------------------

The two services expose complementary event mechanisms.

**DataModel** provides a built-in event subscription model. Call
``SubscribeEvents`` to register interest in specific events for a rules
context, then call ``StreamEvents`` to open a server-side stream that delivers
those events as they occur. Call ``UnsubscribeEvents`` to cancel a
subscription. For coarser-grained monitoring, ``StreamStateChanges`` streams
the full state (or a diff) whenever anything changes in the datamodel.

The :doc:`Events <../api/services/events>` service covers **solver-level
lifecycle events** — iteration completion, time-step advancement, convergence,
and similar notifications that originate from the solver process rather than
the datamodel. Its ``BeginStreaming`` RPC returns a server-side stream of these
events. For deterministic per-iteration or per-time-step callbacks that pause
and resume the solver, use ``PauseSolveFor``, ``ResumeSolve``, and
``UnregisterPause`` on the same service.

See the :doc:`DataModel client example <client_examples/datamodel_se>` and the
:doc:`Events client example <client_examples/events>` for code.

Building on the schema
-----------------------

The schema returned by ``GetSchema`` is also the foundation for generating a
complete, typed client API at build time or startup time. The general approach
is:

1. Fetch ``GetSchema`` from a reference server, or embed the serialised
   response as a build artefact.
2. Walk the returned tree. For the DataModel service, each singleton or
   named-object node becomes a class, each parameter a typed property, and each
   command a method. For the Settings service, each group node becomes a class
   and each leaf a typed property.
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
- :doc:`../api/services/events` — solver lifecycle events and pause callbacks
- :doc:`../api/services/field_data` — streaming mesh geometry and field values
- :doc:`../api/services/health` — Health service reference
