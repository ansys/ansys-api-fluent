DataModel service — Python examples
====================================

This page shows how to build a Python client for the ``DataModel`` gRPC
service — from connecting to the server and exploring the schema, through
reading and writing state, to a complete end-to-end meshing session.

For the full message and field reference see
:doc:`../../api/services/datamodel_se`.

.. include:: ../../shared_example_assumptions.rst

.. code-block:: python
   :caption: Python

   import grpc
   from ansys.api.fluent.v1 import datamodel_se_pb2, datamodel_se_pb2_grpc
   from ansys.api.fluent.v1 import variant_pb2

   channel = grpc.insecure_channel("127.0.0.1:50051")
   metadata = [("password", "your-server-password")]
   stub = datamodel_se_pb2_grpc.DataModelStub(channel)

The **rules** string identifies the application context for every call.
The value to pass depends on the Fluent application you are targeting;
``"meshing"`` selects the meshing object model.

Discovering the schema
-----------------------

Call ``GetSchema`` once at startup and cache the result. It returns the
complete tree of paths, object types, commands, and queries available for a
given rules context. The schema is stable for a given Fluent version and does
not reflect runtime state.

.. code-block:: python
   :caption: Python

   schema_resp = stub.GetSchema(
       datamodel_se_pb2.GetSchemaRequest(rules="meshing"),
       metadata=metadata,
   )

   def walk(node, indent=0):
       prefix = "  " * indent
       for name, child in node.singletons.items():
           print(f"{prefix}{name}/")
           walk(child, indent + 1)
       for name, child in node.named_objects.items():
           print(f"{prefix}{name}:<name>/")
           walk(child, indent + 1)
       for name in node.parameters:
           print(f"{prefix}{name}")
       for name in node.commands:
           print(f"{prefix}{name}()")

   walk(schema_resp.info)

The tree structure directly mirrors the slash-separated paths used in every
other RPC call.

Runtime API overview
---------------------

Once you know the schema, the runtime RPCs follow a small, consistent set of
patterns.

**Read and write state** with ``GetState`` and ``SetState``. Values are
carried in :doc:`Variant <../../api/helpers/variant>` messages. Use
``UpdateDict`` to merge a partial map without overwriting untouched keys.

.. code-block:: python
   :caption: Python

   resp = stub.GetState(
       datamodel_se_pb2.GetStateRequest(rules="meshing", path="GlobalSettings/EnableCleanCAD"),
       metadata=metadata,
   )
   print(getattr(resp.state, resp.state.WhichOneof("as")))

   stub.SetState(
       datamodel_se_pb2.SetStateRequest(
           rules="meshing",
           path="GlobalSettings/EnableCleanCAD",
           state=variant_pb2.Variant(bool_state=True),
           wait=True,
       ),
       metadata=metadata,
   )

**Manage named objects** with ``CreateObject``, ``Rename``, ``DeleteObject``,
and ``GetObjectNames``. Instance paths use ``Type:<name>`` colon notation.

.. code-block:: python
   :caption: Python

   stub.CreateObject(
       datamodel_se_pb2.CreateObjectRequest(
           rules="meshing", path="SomeCollection", name="my-object", wait=True,
       ),
       metadata=metadata,
   )
   names = stub.GetObjectNames(
       datamodel_se_pb2.GetObjectNamesRequest(rules="meshing", path="SomeCollection"),
       metadata=metadata,
   ).names
   print(list(names))

**Execute commands and queries** with ``ExecuteCommand`` and
``ExecuteQuery``. Pass arguments as a ``Variant`` map. For complex
multi-field arguments, use ``CreateCommandArguments`` to build them
incrementally on the server before executing.

.. code-block:: python
   :caption: Python

   stub.ExecuteCommand(
       datamodel_se_pb2.ExecuteCommandRequest(
           rules="meshing", path="", command="ImportGeometry", wait=True,
           args=variant_pb2.Variant(
               variant_map_state=variant_pb2.VariantMap(
                   item={"FileName": variant_pb2.Variant(string_state="/data/my.scdoc")}
               )
           ),
       ),
       metadata=metadata,
   )

**React to changes** by subscribing to object-level events with
``SubscribeEvents`` and streaming them with ``StreamEvents``. For
coarser-grained monitoring, ``StreamStateChanges`` delivers a diff or
full snapshot whenever the datamodel changes.

End-to-end example
-------------------

The example below walks through a complete meshing session: connect,
initialise, discover the schema, configure a setting, import a geometry
file, verify the result, generate the mesh, and close.

.. code-block:: python
   :caption: Python

   import grpc
   from ansys.api.fluent.v1 import datamodel_se_pb2, datamodel_se_pb2_grpc, variant_pb2

   channel = grpc.insecure_channel("127.0.0.1:50051")
   metadata = [("password", "your-server-password")]
   stub = datamodel_se_pb2_grpc.DataModelStub(channel)

   # Initialise the datamodel for the meshing context.
   stub.InitDatamodel(
       datamodel_se_pb2.InitDatamodelRequest(rules="meshing", return_state_changes=False),
       metadata=metadata,
   )

   # Discover what is available at the top level.
   schema_resp = stub.GetSchema(
       datamodel_se_pb2.GetSchemaRequest(rules="meshing"), metadata=metadata,
   )
   print("Top-level singletons:", list(schema_resp.info.singletons.keys()))

   # Turn on clean CAD import before loading geometry.
   stub.SetState(
       datamodel_se_pb2.SetStateRequest(
           rules="meshing",
           path="GlobalSettings/EnableCleanCAD",
           state=variant_pb2.Variant(bool_state=True),
           wait=True,
       ),
       metadata=metadata,
   )

   # Import the geometry file.
   stub.ExecuteCommand(
       datamodel_se_pb2.ExecuteCommandRequest(
           rules="meshing",
           path="",
           command="ImportGeometry",
           wait=True,
           args=variant_pb2.Variant(
               variant_map_state=variant_pb2.VariantMap(
                   item={"FileName": variant_pb2.Variant(string_state="/data/my.scdoc")}
               )
           ),
       ),
       metadata=metadata,
   )

   # Confirm the setting was applied.
   resp = stub.GetState(
       datamodel_se_pb2.GetStateRequest(rules="meshing", path="GlobalSettings/EnableCleanCAD"),
       metadata=metadata,
   )
   print("EnableCleanCAD:", resp.state.bool_state)

   # Generate the mesh.
   stub.ExecuteCommand(
       datamodel_se_pb2.ExecuteCommandRequest(
           rules="meshing", path="", command="GenerateMesh", wait=True,
           args=variant_pb2.Variant(),
       ),
       metadata=metadata,
   )

   channel.close()

For the complete message and field reference — request/response types,
``Variant`` encoding, and the ``DiffState`` enum — see
:doc:`../../api/services/datamodel_se`.
