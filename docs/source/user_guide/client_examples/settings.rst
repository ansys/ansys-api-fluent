Settings service — Python examples
====================================

This page shows how to build a Python client for the ``Settings`` gRPC
service — from connecting to the server and exploring the schema, through
reading and writing solver configuration, to a complete end-to-end example.

For the full message and field reference see
:doc:`../../api/services/settings`.

.. include:: ../../shared_example_assumptions.rst

.. code-block:: python
   :caption: Python

   import grpc
   from ansys.api.fluent.v1 import settings_pb2, settings_pb2_grpc

   channel = grpc.insecure_channel("127.0.0.1:50051")
   metadata = [("password", "your-server-password")]
   stub = settings_pb2_grpc.SettingsStub(channel)

Every RPC addresses a settings node with a ``PathInfo`` message carrying a
**root** string and a slash-separated **path**; for the Fluent solver, pass
``"fluent"`` as the root.

It is generally best to walk the schema first so you can confirm valid paths,
commands, and object names before making runtime calls. However, the Settings
service also allows direct runtime queries/commands when you already know the
exact path to target.

Discovering the schema
-----------------------

Call ``GetSchema`` once at startup and cache the result. It returns the
complete tree of paths, object types, commands, and queries available for a
given root. The schema is stable for a given Fluent version and does not
reflect runtime state.

.. code-block:: python
   :caption: Python

   schema_resp = stub.GetSchema(
       settings_pb2.GetSchemaRequest(root="fluent"),
       metadata=metadata,
   )

   def walk(node, indent=0):
       prefix = "  " * indent
       for child in node.children:
           print(f"{prefix}{child.name}/")
           walk(child.value, indent + 1)
       for cmd in node.commands:
           print(f"{prefix}{cmd.name}()")
       for qry in node.queries:
           print(f"{prefix}{qry.name}?")

   walk(schema_resp.info)

The tree structure directly mirrors the slash-separated paths used in every
other RPC call.

Runtime API overview
---------------------

Once you know the schema, the runtime RPCs follow a small, consistent set of
patterns.

**Read and write state** with ``GetState`` and ``SetState``. Values are
carried in ``Value`` messages, which use a ``oneof`` to hold one active type.
Call ``WhichOneof("value")`` on a returned ``Value`` to identify the active
field before accessing it.

.. code-block:: python
   :caption: Python

   resp = stub.GetState(
       settings_pb2.GetStateRequest(
           path_info=settings_pb2.PathInfo(root="fluent", path="setup/general/solver-type"),
       ),
       metadata=metadata,
   )
   kind = resp.value.WhichOneof("value")
   print(f"solver-type is {kind} = {getattr(resp.value, kind)}")

   stub.SetState(
       settings_pb2.SetStateRequest(
           path_info=settings_pb2.PathInfo(root="fluent", path="setup/general/solver-type"),
           value=settings_pb2.Value(string="pressure-based"),
       ),
       metadata=metadata,
   )

**Manage named objects** (boundary conditions, graphics objects, etc.) with
``CreateObject``, ``Rename``, ``DeleteObject``, and ``GetObjectNames``.
The Settings service also provides ``GetListSize`` and ``ResizeListObject``
for fixed-size list settings.

.. code-block:: python
   :caption: Python

   stub.CreateObject(
       settings_pb2.CreateObjectRequest(
           path_info=settings_pb2.PathInfo(root="fluent", path="setup/boundary-conditions/wall"),
           name="wall-1",
       ),
       metadata=metadata,
   )
   names = stub.GetObjectNames(
       settings_pb2.GetObjectNamesRequest(
           path_info=settings_pb2.PathInfo(root="fluent", path="setup/boundary-conditions/wall"),
       ),
       metadata=metadata,
   ).names
   print(list(names))

**Execute commands and queries** with ``ExecuteCommand`` and ``ExecuteQuery``.
Pass arguments as a ``Value`` message. ``ExecuteCommand`` performs a
state-mutating action; ``ExecuteQuery`` returns a computed result without side
effects.

.. code-block:: python
   :caption: Python

   stub.ExecuteCommand(
       settings_pb2.ExecuteCommandRequest(
           path_info=settings_pb2.PathInfo(root="fluent", path="solution/run-calculation"),
           command="iterate",
           args=settings_pb2.Value(integer=10),
       ),
       metadata=metadata,
   )

**Retrieve metadata** with ``GetAttrs`` to read type, active status, or
read-only flag at any path without a prior ``GetSchema`` call. Use
``IsWildcard`` to check whether a string will be treated as a wildcard by the
solver before passing it to other RPCs.

End-to-end example
-------------------

The example below walks through a complete solver configuration session:
connect, discover the schema, set a solver parameter, create a boundary
condition, run a calculation, and close.

.. code-block:: python
   :caption: Python

   import grpc
   from ansys.api.fluent.v1 import settings_pb2, settings_pb2_grpc

   channel = grpc.insecure_channel("127.0.0.1:50051")
   metadata = [("password", "your-server-password")]
   stub = settings_pb2_grpc.SettingsStub(channel)

   # Discover what is available at the top level.
   schema_resp = stub.GetSchema(
       settings_pb2.GetSchemaRequest(root="fluent"),
       metadata=metadata,
   )
   print("Top-level children:", [c.name for c in schema_resp.info.children])

   # Set the solver type.
   stub.SetState(
       settings_pb2.SetStateRequest(
           path_info=settings_pb2.PathInfo(root="fluent", path="setup/general/solver-type"),
           value=settings_pb2.Value(string="pressure-based"),
       ),
       metadata=metadata,
   )

   # Create a new wall boundary condition.
   stub.CreateObject(
       settings_pb2.CreateObjectRequest(
           path_info=settings_pb2.PathInfo(
               root="fluent", path="setup/boundary-conditions/wall"
           ),
           name="heated-wall",
       ),
       metadata=metadata,
   )

   # Configure an operating pressure for the case.
   stub.SetState(
       settings_pb2.SetStateRequest(
           path_info=settings_pb2.PathInfo(
               root="fluent",
               path="setup/general/operating-conditions/operating-pressure",
           ),
           value=settings_pb2.Value(real=101325.0),
       ),
       metadata=metadata,
   )

   # Confirm the value was written.
   resp = stub.GetState(
       settings_pb2.GetStateRequest(
           path_info=settings_pb2.PathInfo(
               root="fluent",
               path="setup/general/operating-conditions/operating-pressure",
           ),
       ),
       metadata=metadata,
   )
   print("Operating pressure:", resp.value.real)

   # Run 50 iterations.
   stub.ExecuteCommand(
       settings_pb2.ExecuteCommandRequest(
           path_info=settings_pb2.PathInfo(root="fluent", path="solution/run-calculation"),
           command="iterate",
           args=settings_pb2.Value(integer=50),
       ),
       metadata=metadata,
   )

   channel.close()

For the complete message and field reference — request/response types,
the ``Value`` and ``Schema`` message structures, and ``GetAttrs`` — see
:doc:`../../api/services/settings`.
