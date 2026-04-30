Building on the API
===================

This page is for developers who are building a client library, a code
generator, or an application on top of the Fluent gRPC API — not for
developers who are making direct one-off calls. If you want to connect and
call a specific RPC, start with :doc:`build_a_client` instead.

What the API schema is
----------------------

The API schema is a machine-readable contract that describes what exists in the
API, independent of any running Fluent session. It answers:

- **What paths exist?** — the complete hierarchy of objects, parameters, and
  named-object families.
- **What types apply?** — the type of every parameter and the return type of
  every query.
- **What operations are available?** — every command and query at every path,
  with their argument names and types.
- **What constraints apply?** — whether a parameter has a restricted set of
  allowed values, whether it is read-only, and so on.

The contract is stable across sessions. It does not depend on whether a case is
loaded, a solver is running, or any runtime state is populated. That makes it
the right foundation for generated code, validation logic, and introspective
tooling.

Both the DataModel service and the Settings service expose their schema through
a single ``GetSchema`` RPC:

- ``DataModelStub.GetSchema(GetSchemaRequest(rules=...))`` → ``GetSchemaResponse``
- ``SettingsStub.GetSchema(GetSchemaRequest(root=...))`` → ``GetSchemaResponse``

What the schema contains
------------------------

The two services return different message types, reflecting their different
structural models.

**DataModel service — ``GetSchemaResponse.info`` (``Schema``)**

.. list-table::
   :header-rows: 1
   :widths: 30 70

   * - Field
     - Content
   * - ``singletons``
     - Child singleton objects. Each has its own ``Schema`` sub-tree.
   * - ``named_objects``
     - Child named-object families. Each has a prototype ``Schema`` that
       describes all instances of that family.
   * - ``parameters``
     - Leaf parameters. Each entry carries a type tag (``Bool``, ``Integer``,
       ``Real``, ``String``, ``List``, ``Dict``) and an ``allowed_values``
       field where applicable.
   * - ``commands``
     - Available commands. Each command entry lists its argument names and
       types as a nested parameter map.
   * - ``queries``
     - Available queries. Same structure as commands.
   * - ``type``
     - String type identifier for the current node.
   * - ``help_string``
     - Human-readable description of the node.

**Settings service — ``GetSchemaResponse.info`` (``Schema``)**

.. list-table::
   :header-rows: 1
   :widths: 30 70

   * - Field
     - Content
   * - ``type``
     - Object type string (``group``, ``named-object``, ``integer``,
       ``real``, ``string``, ``boolean``, ``list-object``, etc.)
   * - ``children``
     - List of child settings nodes, each with a ``name`` and a ``Schema``
       value.
   * - ``commands``
     - Available commands at this settings path.
   * - ``queries``
     - Available queries at this settings path.
   * - ``arguments``
     - Argument descriptors for the containing command or query.
   * - ``help``
     - Human-readable description.
   * - ``has_allowed_values``
     - ``True`` when the parameter only accepts a predefined set of values.

Using the schema to build a client
-----------------------------------

The general pattern for any schema-driven client is the same regardless of the
service or target language:

1. **Fetch at startup.** Call ``GetSchema`` once when the client initialises
   and hold the result in memory. The schema is stable for the lifetime of a
   Fluent installation version; there is no need to re-fetch it per session.

2. **Traverse and index.** Walk the returned tree and build your own index —
   a flat map of path → node, a set of valid command names per path, a type
   map for parameter validation. The exact shape of the index depends on what
   your client needs to do.

3. **Validate at the boundary.** Before issuing any ``GetState``, ``SetVar``,
   or ``ExecuteCommand`` call, check the path and arguments against your index.
   This catches typos and version mismatches at the client side, before the
   round trip.

4. **Execute only valid operations.** Once the index says the path and
   operation exist and the argument types match, build the request message and
   send it. Treat RPC errors as unexpected — your validation layer should
   surface most problems before the call.

In pseudocode:

.. code-block:: text

   schema = stub.GetSchema(rules="meshing").info          # fetch once
   index  = build_index(schema)                           # flatten into a dict

   def set(path, value):
       node = index.get(path)
       if node is None:
           raise ValueError(f"Unknown path: {path}")
       if not type_matches(node.type, value):
           raise TypeError(f"Expected {node.type} at {path}")
       stub.SetState(rules="meshing", path=path, state=to_variant(value))

   def call(path, command, args):
       node = index.get(path)
       if command not in node.commands:
           raise ValueError(f"No command '{command}' at {path}")
       validate_args(node.commands[command], args)
       stub.ExecuteCommand(rules="meshing", path=path, command=command, args=to_variant(args))

Runtime discoverability
-----------------------

The schema layer is not the only way to discover the API at runtime.

**Settings service — strong runtime discoverability**

The Settings service is highly introspectable without ever calling
``GetSchema``:

- ``GetAttrs`` returns named attributes — ``type``, ``active?``,
  ``read-only?``, ``allowed-values``, ``default``, and others — for any path.
  The ``recursive`` flag makes it possible to walk a subtree in a single call.
- ``GetObjectNames`` enumerates the existing named-object instances at a path.
- ``GetListSize`` returns the current size of any list-typed setting.
- ``Value`` responses carry their type tag in the ``oneof`` field, so a
  generic client can dispatch on type without any prior schema knowledge.

A client that is limited to a known subtree of the Settings hierarchy can
sometimes avoid ``GetSchema`` entirely by using these RPCs to discover
structure on demand.

**DataModel service — limited runtime discoverability**

The DataModel service is less complete in this respect. ``GetAttributeValue``
and ``GetSpecs`` provide some path-level metadata, but there is no equivalent
of ``GetAttrs`` with recursive traversal. A DataModel client that needs to
enumerate the full structure reliably should use ``GetSchema``.

Code generation and static clients
------------------------------------

The most complete form of schema-driven development is using the schema to
generate a full client API at build time, so that application code works with
named Python (or other language) classes and methods rather than raw path
strings.

PyFluent (the official Ansys Python client for Fluent) uses this approach: the
``Schema`` schema for the DataModel service and the ``Schema`` for the
Settings service were consumed by a code generator that emitted the full Python
class hierarchy — one class per object type, one method per command or query,
typed properties for every parameter. End-user code calls
``session.meshing.GlobalSettings.EnableCleanCAD = True`` and never constructs a
``GetStateRequest`` manually.

External developers can do the same for any language. The process is:

1. Fetch the schema from a reference server (or embed the serialised
   ``GetSchemaResponse`` as a build artefact).
2. Traverse the tree. For the DataModel service: each singleton or
   named-object node becomes a class, each parameter becomes a typed property,
   each command becomes a method. For the Settings service: each group node
   becomes a class, each leaf node becomes a typed property.
3. Emit the generated source. Include path and rules/root constants so the
   generated classes can construct the correct ``PathInfo`` or ``rules``
   arguments automatically.
4. Re-run the generator whenever the server version changes and the schema
   shifts.

The advantage of this approach is a fully typed, IDE-navigable API with no
path strings in application code. The cost is the code-generation step and the
need to regenerate when the API evolves.

Dynamic clients
---------------

The alternative is a client that fetches the schema at runtime and adapts to
whatever the server returns — with no generated code at all. This is
appropriate when:

- You are building a generic tool (an inspector, a configuration editor, a
  scripting engine) that must work with any Fluent version without
  recompilation.
- You want to avoid a code-generation step in your build pipeline.
- The schema is expected to evolve frequently and you prefer to absorb changes
  at runtime rather than regenerating.

A dynamic client typically:

1. Calls ``GetSchema`` on startup (or on demand) and caches the result.
2. Presents the schema to the user or calling code as a navigable tree — for
   example, exposing ``client["GlobalSettings"]["EnableCleanCAD"]`` syntax
   backed by the live schema.
3. Builds request messages from path strings and Python dicts, validating
   against the cached schema before each call.
4. Re-fetches the schema if a server-side change is detected (for example, if
   an RPC returns ``NOT_FOUND`` for a previously valid path).

The trade-off compared to code generation is that dynamic clients sacrifice
static type checking and IDE completion. All errors that a static client would
catch at compile time become runtime errors. This is acceptable for tools and
scripts; it is a harder sell for production application code.
