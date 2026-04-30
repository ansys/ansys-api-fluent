Building an end-to-end Fluent client
=====================================

This guide walks you through building a complete Python client from scratch.
You will learn how to connect to Fluent, discover what is available through the
API schema, read and write configuration state, and react to live solver events.
No prior knowledge of gRPC or Fluent internals is assumed.

.. include:: ../shared_example_assumptions.rst

Overview
--------

Fluent primarily exposes two APIs for reading and writing simulation configuration:

:doc:`DataModel <../api/services/datamodel_se>`
   Hierarchical read/write access to Fluent's internal object model — meshing
   workflows and post-processing. Paths are addressed
   by a **rules** string (which selects the context) and a slash-separated
   **path** within it.

:doc:`Settings <../api/services/settings>`
   Hierarchical read/write access to Fluent's simulation configuration —
   boundary conditions, solver controls, model parameters, and results
   settings. Paths are addressed by a **root** string (typically ``fluent``)
   and a slash-separated **path** within it.

Both follow the same pattern: call ``GetSchema`` RPC method to discover the 
configuration structure and how to address each element, then read and write 
state using those addresses.

Building a typical Fluent client involves five steps:

1. **Connect** — open a channel to the Fluent server and verify it is healthy.
2. **Discover** — call ``GetSchema`` on the DataModel or Settings service to
   learn what paths, parameters, commands, and queries exist.
3. **Read state** — call ``GetState`` or ``GetVar`` to retrieve current values.
4. **Write state** — call ``SetState`` or ``SetVar`` to change configuration.
5. **React** — subscribe to the Events service to receive live solver
   notifications.

Step 1 — Connect and verify server health
-----------------------------------------

Every client starts by opening a gRPC channel and checking that the server is
ready to accept requests.

.. code-block:: python
   :caption: Python

   import grpc
   from ansys.api.fluent.v1 import health_pb2, health_pb2_grpc

   HOST = "127.0.0.1"
   PORT = 50051
   PASSWORD = "your-server-password"

   channel = grpc.insecure_channel(f"{HOST}:{PORT}")
   metadata = [("password", PASSWORD)]

   health_stub = health_pb2_grpc.HealthStub(channel)
   resp = health_stub.Check(health_pb2.HealthCheckRequest(), metadata=metadata)
   assert resp.status == health_pb2.HealthCheckResponse.SERVING_STATUS_SERVING
   print("Server is healthy")

Keep ``channel`` and ``metadata`` alive for the lifetime of your client; pass
them to every stub you create.

.. tip::

   If ``Check`` raises ``grpc.RpcError`` with code ``UNAVAILABLE``, the server
   is not reachable. Verify the host, port, and that Fluent is running.

Step 2 — Discover the DataModel service schema
----------------------------------------------

The DataModel service organises Fluent's object model as a tree. Before reading or
writing any value, call ``GetSchema`` to learn what paths, parameter types,
commands, and queries exist for a given *rules context* (such as ``meshing``
or ``flserver``).

.. code-block:: python
   :caption: Python

   from ansys.api.fluent.v1 import datamodel_se_pb2, datamodel_se_pb2_grpc

   dm_stub = datamodel_se_pb2_grpc.DataModelStub(channel)

   schema_resp = dm_stub.GetSchema(
       datamodel_se_pb2.GetSchemaRequest(rules="meshing"),
       metadata=metadata,
   )

   # The top-level schema describes all singletons, named-object families,
   # parameters, commands, and queries at the root of the meshing rules context.
   root_schema = schema_resp.info

   print("Top-level singletons:", list(root_schema.singletons.keys()))
   print("Top-level named objects:", list(root_schema.named_objects.keys()))
   print("Top-level commands:", list(root_schema.commands.keys()))

The returned ``Schema`` (accessible as ``schema_resp.info``) is a recursive
structure. Each node contains:

.. list-table:: ``Schema`` fields
   :header-rows: 1
   :widths: 25 75

   * - Field
     - Meaning
   * - ``singletons``
     - Child singleton objects (fixed, single-instance sub-objects)
   * - ``named_objects``
     - Child named-object families (multiple instances, each with a name)
   * - ``parameters``
     - Leaf parameters (bool, int, real, string, list)
   * - ``commands``
     - Operations that change state; include argument descriptions
   * - ``queries``
     - Read-only computations with typed arguments
   * - ``type``
     - String type tag for the current node
   * - ``help_string``
     - Human-readable description

The following example prints the schema as an indented outline to help you
identify the path to the element you want:

.. code-block:: python
   :caption: Python

   def print_schema_tree(node, prefix="", depth=2):
       """Print the DataModel schema tree up to `depth` levels."""
       if depth == 0:
           return
       for name in list(node.singletons.keys()) + list(node.named_objects.keys()):
           print(f"{prefix}{name}/")
           child = node.singletons.get(name) or node.named_objects.get(name)
           print_schema_tree(child, prefix + "  ", depth - 1)
       for name in node.parameters.keys():
           print(f"{prefix}{name}  [{node.parameters[name].type}]")
       for name in node.commands.keys():
           print(f"{prefix}{name}()  [command]")

   print_schema_tree(root_schema)

Step 3 — Read and write DataModel state
----------------------------------------

Once you know the path to a parameter or object from the API schema, use
``GetState`` and ``SetState`` to read and write it. All values are exchanged
as ``Variant`` messages.

.. code-block:: python
   :caption: Python

   from ansys.api.fluent.v1 import variant_pb2

   # Read current value
   get_resp = dm_stub.GetState(
       datamodel_se_pb2.GetStateRequest(
           rules="meshing",
           path="GlobalSettings/EnableCleanCAD",
       ),
       metadata=metadata,
   )
   # Determine which field is set in the Variant
   kind = get_resp.state.WhichOneof("as")
   print(f"EnableCleanCAD ({kind}):", getattr(get_resp.state, kind))

   # Write a new value
   dm_stub.SetState(
       datamodel_se_pb2.SetStateRequest(
           rules="meshing",
           path="GlobalSettings/EnableCleanCAD",
           state=variant_pb2.Variant(bool_state=True),
           wait=True,
       ),
       metadata=metadata,
   )

``Variant`` supports these scalar fields: ``bool_state``, ``int64_state``,
``double_state``, ``string_state``. For lists and maps it provides
``variant_vector_state`` and ``variant_map_state``. Always use
``WhichOneof("as")`` to determine which field is populated in a response
``Variant``.

To execute a command discovered in the API schema:

.. code-block:: python
   :caption: Python

   cmd_args = variant_pb2.Variant(
       variant_map_state=variant_pb2.VariantMap(
           item={"FileName": variant_pb2.Variant(string_state="/path/to/geometry.scdoc")}
       )
   )

   dm_stub.ExecuteCommand(
       datamodel_se_pb2.ExecuteCommandRequest(
           rules="meshing",
           path="",
           command="ImportGeometry",
           wait=True,
           args=cmd_args,
       ),
       metadata=metadata,
   )

Step 4 — Discover the Settings service schema
---------------------------------------------

The Settings service uses a flat, slash-separated path hierarchy to expose solver
configuration. Call ``GetSchema`` to retrieve the full tree of available
settings paths, their types, allowed values, and help text.

.. code-block:: python
   :caption: Python

   from ansys.api.fluent.v1 import settings_pb2, settings_pb2_grpc

   settings_stub = settings_pb2_grpc.SettingsStub(channel)

   schema_resp = settings_stub.GetSchema(
       settings_pb2.GetSchemaRequest(root="fluent"),
       metadata=metadata,
   )

   root_schema = schema_resp.info

   print("Type:", root_schema.type)
   print("Top-level children:", [c.name for c in root_schema.children[:10]])

The returned ``Schema`` object describes the settings hierarchy:

.. list-table:: ``Schema`` fields
   :header-rows: 1
   :widths: 25 75

   * - Field
     - Meaning
   * - ``type``
     - Object type (``group``, ``named-object``, ``integer``, etc.)
   * - ``children``
     - Child settings nodes (list of ``SchemaMap`` with ``name`` and ``value``)
   * - ``commands``
     - Available commands at this path
   * - ``arguments``
     - Arguments for the current command or query
   * - ``help``
     - Human-readable description
   * - ``has_allowed_values``
     - Whether the parameter has a restricted set of valid values

The following example prints every settings path with its type:

.. code-block:: python
   :caption: Python

   def find_settings_paths(node, prefix="", depth=3):
       """Print Settings service paths up to `depth` levels."""
       if depth == 0:
           return
       for child in node.children:
           path = f"{prefix}/{child.name}" if prefix else child.name
           print(path, f"[{child.value.type}]")
           find_settings_paths(child.value, path, depth - 1)

   find_settings_paths(root_schema)

Step 5 — Read and write Settings values
-----------------------------------------

Use ``GetVar`` and ``SetVar`` with a ``PathInfo`` to access any path discovered
in the Settings service schema. Values are exchanged as ``Value`` messages.

.. code-block:: python
   :caption: Python

   # Read current operating pressure
   get_resp = settings_stub.GetVar(
       settings_pb2.GetVarRequest(
           path_info=settings_pb2.PathInfo(
               root="fluent",
               path="setup/general/operating-conditions/operating-pressure",
           )
       ),
       metadata=metadata,
   )
   kind = get_resp.value.WhichOneof("value")
   print(f"Operating pressure ({kind}):", getattr(get_resp.value, kind))

   # Write a new value
   settings_stub.SetVar(
       settings_pb2.SetVarRequest(
           path_info=settings_pb2.PathInfo(
               root="fluent",
               path="setup/general/operating-conditions/operating-pressure",
           ),
           value=settings_pb2.Value(real=101325.0),
       ),
       metadata=metadata,
   )

``Value`` supports: ``boolean``, ``integer``, ``real``, ``string``,
``value_list``, and ``value_map``. Use ``WhichOneof("value")`` to identify
which field is set in a response.

Named objects (boundary conditions, contours, etc.) are managed with
``Create``, ``Rename``, ``Delete``, and ``GetObjectNames``:

.. code-block:: python
   :caption: Python

   # List existing wall boundary conditions
   names_resp = settings_stub.GetObjectNames(
       settings_pb2.GetObjectNamesRequest(
           path_info=settings_pb2.PathInfo(
               root="fluent",
               path="setup/boundary-conditions/wall",
           )
       ),
       metadata=metadata,
   )
   print("Wall BCs:", list(names_resp.names))

   # Create a new wall boundary condition
   settings_stub.Create(
       settings_pb2.CreateRequest(
           path_info=settings_pb2.PathInfo(
               root="fluent",
               path="setup/boundary-conditions/wall",
           ),
           name="wall-new",
       ),
       metadata=metadata,
   )

Step 6 — React to live solver events
--------------------------------------

The Events service delivers solver lifecycle notifications as a server-side
stream. Subscribe once and iterate over the stream while your solver runs.

.. code-block:: python
   :caption: Python

   from ansys.api.fluent.v1 import events_pb2, events_pb2_grpc

   events_stub = events_pb2_grpc.EventsStub(channel)

   stream = events_stub.BeginStreaming(
       events_pb2.BeginStreamingRequest(),
       metadata=metadata,
   )

   for response in stream:
       event_type = response.WhichOneof("as")

       if event_type == "iteration_ended_event":
           ev = response.iteration_ended_event
           print(f"Iteration {ev.index} complete")
       elif event_type == "calculations_ended_event":
           print("Calculations finished — stopping listener")
           break
       elif event_type == "error_event":
           ev = response.error_event
           print(f"Solver error {ev.error_code}: {ev.message}")
           break

For deterministic per-iteration or per-time-step callbacks (where you need to
pause and resume the solver), use the three solver-pause RPCs on the Events
service. See :doc:`../api/services/events` for the full reference.

Complete example
----------------

The following script ties all six steps together into one runnable program.

.. code-block:: python
   :caption: Python

   from __future__ import annotations
   import grpc
   from ansys.api.fluent.v1 import (
       datamodel_se_pb2,
       datamodel_se_pb2_grpc,
       events_pb2,
       events_pb2_grpc,
       health_pb2,
       health_pb2_grpc,
       settings_pb2,
       settings_pb2_grpc,
       variant_pb2,
   )

   HOST = "127.0.0.1"
   PORT = 50051
   PASSWORD = "your-server-password"


   def main() -> None:
       channel = grpc.insecure_channel(f"{HOST}:{PORT}")
       metadata = [("password", PASSWORD)]

       # ------------------------------------------------------------------
       # Step 1: Health check
       # ------------------------------------------------------------------
       health_stub = health_pb2_grpc.HealthStub(channel)
       resp = health_stub.Check(health_pb2.HealthCheckRequest(), metadata=metadata)
       assert resp.status == health_pb2.HealthCheckResponse.SERVING_STATUS_SERVING
       print("Server is healthy")

       # ------------------------------------------------------------------
       # Step 2: Discover the DataModel service schema
       # ------------------------------------------------------------------
       dm_stub = datamodel_se_pb2_grpc.DataModelStub(channel)
       schema_resp = dm_stub.GetSchema(
           datamodel_se_pb2.GetSchemaRequest(rules="meshing"),
           metadata=metadata,
       )
       root = schema_resp.info
       print("DataModel singletons:", list(root.singletons.keys())[:5])
       print("DataModel commands:", list(root.commands.keys())[:5])

       # ------------------------------------------------------------------
       # Step 3: Read and write DataModel state
       # ------------------------------------------------------------------
       get_resp = dm_stub.GetState(
           datamodel_se_pb2.GetStateRequest(
               rules="meshing",
               path="GlobalSettings/EnableCleanCAD",
           ),
           metadata=metadata,
       )
       kind = get_resp.state.WhichOneof("as")
       print(f"EnableCleanCAD before: {getattr(get_resp.state, kind)}")

       dm_stub.SetState(
           datamodel_se_pb2.SetStateRequest(
               rules="meshing",
               path="GlobalSettings/EnableCleanCAD",
               state=variant_pb2.Variant(bool_state=True),
               wait=True,
           ),
           metadata=metadata,
       )

       # ------------------------------------------------------------------
       # Step 4: Discover the Settings service schema
       # ------------------------------------------------------------------
       settings_stub = settings_pb2_grpc.SettingsStub(channel)
       schema_resp = settings_stub.GetSchema(
           settings_pb2.GetSchemaRequest(root="fluent"),
           metadata=metadata,
       )
       print("Settings top-level children:",
             [c.name for c in schema_resp.info.children[:5]])

       # ------------------------------------------------------------------
       # Step 5: Read and write Settings values
       # ------------------------------------------------------------------
       get_resp = settings_stub.GetVar(
           settings_pb2.GetVarRequest(
               path_info=settings_pb2.PathInfo(
                   root="fluent",
                   path="setup/general/operating-conditions/operating-pressure",
               )
           ),
           metadata=metadata,
       )
       kind = get_resp.value.WhichOneof("value")
       print(f"Operating pressure: {getattr(get_resp.value, kind)}")

       settings_stub.SetVar(
           settings_pb2.SetVarRequest(
               path_info=settings_pb2.PathInfo(
                   root="fluent",
                   path="setup/general/operating-conditions/operating-pressure",
               ),
               value=settings_pb2.Value(real=101325.0),
           ),
           metadata=metadata,
       )

       # ------------------------------------------------------------------
       # Step 6: React to live solver events (limited to 10 for demo)
       # ------------------------------------------------------------------
       events_stub = events_pb2_grpc.EventsStub(channel)
       stream = events_stub.BeginStreaming(
           events_pb2.BeginStreamingRequest(),
           metadata=metadata,
       )
       for i, response in enumerate(stream):
           event_type = response.WhichOneof("as")
           print(f"Event: {event_type}")
           if i >= 9:
               break

       channel.close()


   if __name__ == "__main__":
       main()

Next steps
----------

- :doc:`../api/services/datamodel_se` — full DataModel service reference
- :doc:`../api/services/settings` — full Settings service reference
- :doc:`../api/services/events` — event types and solver pause callbacks
- :doc:`../api/services/field_data` — streaming mesh geometry and field values
- :doc:`../api/services/health` — health-check patterns
