Building a minimal Fluent client
=================================

A minimal Fluent client needs just one service. :doc:`DataModel <../api/services/datamodel_se>`
and :doc:`Settings <../api/services/settings>` cover the full lifecycle of a
Fluent session between them — choose the one that matches your use case:

- Use **DataModel** if you are driving meshing, guided workflows, or
  application preferences.
- Use **Settings** if you are configuring the solver — boundary conditions,
  physics models, or solver controls.

Both services have the same design and the same core RPCs, so skills transfer
directly. Everything else in the API — health checks, streaming, field data —
is optional and can be added incrementally.

.. note::

   The ``.proto`` files are language-agnostic. RPC names and message structures
   are identical whether you generate a client in Python, Go, Java, or C++.

Shared design
-------------

DataModel and Settings are deliberately mirrors of each other, which is why
learning one immediately transfers to the other. They expose the same core RPCs:

.. list-table::
   :header-rows: 1
   :widths: 35 65

   * - RPC
     - Purpose
   * - ``GetSchema``
     - Return the full static structure — every path, type, command, and query.
   * - ``GetState`` / ``SetState``
     - Read or write the value at a path.
   * - ``CreateObject`` / ``DeleteObject``
     - Create or remove a named child object.
   * - ``Rename`` / ``GetObjectNames``
     - Rename a named object or list all names under a path.
   * - ``ExecuteCommand`` / ``ExecuteQuery``
     - Invoke a command or a read-only query at a path.

Once you know how to use one service, you already understand the other.

Differences
-----------

The services differ in **domain** and **addressing**:

- **DataModel** owns meshing, guided workflows, and preferences. Calls carry a
  *rules* string (e.g. ``"meshing"``) and a slash-separated path.
  It additionally provides ``UpdateDict``, ``GetAttributeValue``, ``FixState``,
  and ``CreateCommandArguments`` / ``DeleteCommandArguments``.

- **Settings** owns the solver — boundary conditions, physics models, and
  solver controls. Calls carry a ``PathInfo`` with a *root* string
  (typically ``"fluent"``) and a slash-separated path.
  It additionally provides ``GetAttrs``, ``IsWildcard``, ``GetListSize``,
  and ``ResizeListObject``.

Working with the schema
-----------------------

``GetSchema`` is the starting point for any client. Call it once at startup,
cache the result, and walk the returned ``Schema`` tree — via its ``children``,
``commands``, and ``queries`` fields — to discover valid paths before reading
or writing state. The schema is also the foundation for generating a fully
typed client API: each node becomes a class, each parameter a typed property,
and each command a method. This is exactly how PyFluent is built.

See the schema discovery sections of :doc:`client_examples/datamodel_se` and
:doc:`client_examples/settings` for runnable examples, and the service
references at :doc:`../api/services/datamodel_se` and
:doc:`../api/services/settings` for the full message definitions.

